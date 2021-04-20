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


from warre.common import blazar
from warre.common import exceptions
from warre.extensions import db
from warre import models
from warre.worker import api as worker_api


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

        reservations = db.session.query(models.Reservation) \
            .filter(models.Reservation.end >= reservation.start) \
            .filter(models.Reservation.start <= reservation.end) \
            .filter_by(flavor_id=flavor.id)
        if reservations.count() >= flavor.slots:
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

    def delete_flavor(self, context, flavor):
        reservations = db.session.query(models.Reservation) \
            .filter_by(flavor_id=flavor.id).all()
        if reservations:
            raise exceptions.FlavorInUse(f'Flavor {flavor.id} is in use')
        db.session.delete(flavor)
        db.session.commit()
