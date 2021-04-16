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

from datetime import datetime
from datetime import timedelta
import flask_restful
from flask_restful import inputs
from flask_restful import reqparse
from itertools import chain
from operator import itemgetter
from oslo_log import log as logging
from oslo_policy import policy

from warre.api.v1.resources import base
from warre.api.v1.schemas import freeslot as schemas
from warre.common import policies
from warre.extensions import db
from warre import models

LOG = logging.getLogger(__name__)


class FlavorFreeSlot(base.Resource):

    POLICY_PREFIX = policies.FLAVOR_PREFIX
    schema = schemas.freeslots

    def get(self, id, **kwargs):
        """Get the free slots of a flavor
        Algorithm:
        1. Get slots from flavor table as the total resource
        2. Get all reservations of current flavor
        3. Calculate the free slots
        """
        parser = reqparse.RequestParser()
        parser.add_argument(
            'start', type=inputs.date,
            default=datetime.now())
        parser.add_argument(
            'end', type=inputs.date,
            default=datetime.now() + timedelta(days=365))
        args = parser.parse_args()

        try:
            self.authorize('list')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        # Get all reservations for this flavor
        reservations = db.session.query(models.Reservation) \
            .filter_by(flavor_id=id).all()
        flavor = db.session.query(models.Flavor) \
            .filter_by(id=id).one()

        # the real thing begins here
        # Pass 1: segmentation and marking
        # put every start, end date into a list
        time_list = list(chain.from_iterable(
            [(r.start, 'start'), (r.end, 'end')] for r in reservations))
        # sort on time
        time_list.sort(key=itemgetter(0))
        # LOG.info(time_list)
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
            [s for s in segments if s["slot"] >= flavor.slots
                and s["end"] > args.start]

        if len(busy_slots) == 0:
            return self.schema.dump([{
                "start": args.start,
                "end": args.end
                }])
        query = []
        start_free = args.start
        # Pass3: remove busy slots
        for s in busy_slots:
            if s["start"] <= args.start <= s["end"]:
                start_free = s["end"]
            else:
                if start_free < s["start"]:
                    query.append({
                        "start": start_free,
                        "end": s["start"]
                    })
                start_free = s["end"]
        # add the last one
        if start_free < args.end:
            query.append({
                "start": start_free,
                "end": args.end
            })

        return self.schema.dump(query)
