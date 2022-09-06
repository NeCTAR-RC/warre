#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import datetime
from itertools import chain
from operator import itemgetter

from oslo_log import log as logging
from sqlalchemy.sql import functions

from warre.common import blazar
from warre.common import exceptions
from warre.extensions import db
from warre import models
from warre.worker import api as worker_api

LOG = logging.getLogger(__name__)


class Manager(object):

    def __init__(self):
        self.worker_api = worker_api.WorkerAPI()
        self.blazar = blazar.BlazarClient()

    def create_reservation(self, context, reservation):

        flavor = db.session.query(models.Flavor).get(reservation.flavor_id)
        if not flavor.active:
            raise exceptions.InvalidReservation("Flavor is not available")

        if not flavor.is_public and flavor.projects.filter_by(
                project_id=context.project_id).count() < 1:
            raise exceptions.InvalidReservation("Flavor is not accessible")

        if reservation.total_hours > flavor.max_length_hours:
            raise exceptions.InvalidReservation(
                "Reservation is too long, max allowed is %s hours" %
                flavor.max_length_hours)

        if flavor.start and flavor.start > reservation.start:
            raise exceptions.InvalidReservation(
                "Reservation start time before flavor start time of %s" %
                flavor.start)
        if flavor.end and flavor.end < reservation.end:
            raise exceptions.InvalidReservation(
                "Reservation end time after flavor end time of %s" %
                flavor.end)
        if reservation.end < reservation.start:
            raise exceptions.InvalidReservation(
                "Reservation start time of %s after reservation end time of %s"
                % (reservation.start, reservation.end))

        used_slots = db.session.query(
            functions.sum(models.Reservation.instance_count)) \
            .filter_by(flavor_id=flavor.id) \
            .filter(models.Reservation.end >= reservation.start) \
            .filter(models.Reservation.start <= reservation.end) \
            .filter(models.Reservation.status.in_(
                (models.Reservation.ALLOCATED,
                 models.Reservation.ACTIVE,
                 models.Reservation.PENDING_CREATE))
        ).scalar()
        if (used_slots or 0) >= flavor.slots:
            raise exceptions.InvalidReservation("No capacity")

        reservation.project_id = context.project_id
        reservation.user_id = context.user_id
        db.session.add(reservation)
        db.session.commit()
        self.worker_api.create_lease(context, reservation.id)
        return reservation

    def delete_reservation(self, context, reservation):
        if reservation.lease_id:
            self.blazar.delete_lease(reservation.lease_id)

        db.session.delete(reservation)
        db.session.commit()

    def extend_reservation(self, context, reservation, new_end):
        if not reservation.lease_id:
            raise exceptions.InvalidReservation("No lease")

        if reservation.status != models.Reservation.ACTIVE:
            raise exceptions.InvalidReservation(
                "Reservation must be in ACTIVE state")

        now = datetime.datetime.now()
        if ((new_end - now).total_seconds()
            > (reservation.flavor.max_length_hours * 60)):
            raise exceptions.InvalidReservation(
                "Reservation is too long, max allowed is %s hours" %
                reservation.flavor.max_length_hours)

        free_slots = self.flavor_free_slots(
            context, reservation.flavor, reservation.end,
            new_end, reservation)

        if free_slots:
            f_start = free_slots[0].get('start')
            f_end = free_slots[0].get('end')
            if f_start != reservation.end or f_end < new_end:
                raise exceptions.InvalidReservation("No capacity")
        else:
            raise exceptions.InvalidReservation("No capacity")

        reservation.end = new_end

        try:
            self.blazar.update_lease(reservation.lease_id,
                                     end_date=reservation.end)
        except Exception as e:
            LOG.exception(e)
            raise exceptions.InvalidReservation("Failed to extend lease")
        else:
            db.session.add(reservation)
            db.session.commit()
            LOG.info(f"Updated {reservation}")
            return reservation

    def delete_flavor(self, context, flavor):
        reservations = db.session.query(models.Reservation) \
            .filter_by(flavor_id=flavor.id).all()
        if reservations:
            raise exceptions.FlavorInUse(f'Flavor {flavor.id} is in use')
        db.session.delete(flavor)
        db.session.commit()

    def flavor_free_slots(self, context, flavor, start, end, reservation=None):
        """Get the free slots of a flavor
        Algorithm:
        1. Get slots from flavor table as the total resource
        2. Get all reservations of current flavor
        3. Calculate the free slots

        reservation - used to exclude an existing reservation when extending
        """
        if not flavor.active:
            return []

        if flavor.start and flavor.start > start:
            start = flavor.start

        if flavor.end and flavor.end < end:
            end = flavor.end

        query = db.session.query(models.Reservation) \
                          .filter(models.Reservation.end >= start) \
                          .filter(models.Reservation.start <= end) \
                          .filter(models.Reservation.status.in_(
                              (models.Reservation.ALLOCATED,
                               models.Reservation.ACTIVE))) \
                          .filter_by(flavor_id=flavor.id)
        if reservation:
            query = query.filter(models.Reservation.id != reservation.id)
        reservations = query.all()
        # the real thing begins here
        # Pass 1: segmentation and marking
        # out every start, end date into a list
        used_slots = []
        for r in reservations:
            # Treat multi instance as just multiple slots
            for i in range(0, r.instance_count):
                used_slots.append([(r.start, 'start'), (r.end, 'end')])

        time_list = list(chain.from_iterable(used_slots))
        # sort on time
        time_list.sort(key=itemgetter(0))
        segments = []
        current_slot = 0
        last_point = None
        for point, kind in time_list:
            if last_point is not None:
                segments.append({
                    "start": last_point,
                    "end": point,
                    "slot": current_slot
                    })
            # update last_point
            last_point = point
            # adjust current slot
            current_slot = current_slot + 1 if kind == 'start' \
                else current_slot - 1
        # Pass2: only keep slot >= maximum capacity, a.k.a. busy slots
        busy_slots = \
            [s for s in segments if s["slot"] >= flavor.slots]

        if len(busy_slots) == 0:
            return [{
                "start": start,
                "end": end
                }]
        free_slots = []
        start_free = start
        # Pass3: remove busy slots
        for s in busy_slots:
            if s["start"] <= start <= s["end"]:
                start_free = s["end"]
            else:
                diff = (s["start"] - start_free).total_seconds()
                if start_free < s["start"] and diff > 60:
                    if start_free != start:
                        start_free += datetime.timedelta(seconds=60)
                    free_slots.append({
                        "start": start_free,
                        "end": (s["start"] - datetime.timedelta(
                            seconds=1)).replace(second=0)
                    })
                start_free = s["end"]
        # add the last one
        if start_free < end:
            if start_free != start:
                start_free += datetime.timedelta(seconds=60)
            free_slots.append({
                "start": start_free,
                "end": end
            })

        return free_slots
