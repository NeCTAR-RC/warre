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
from itertools import chain
from operator import itemgetter

from flask import request
import flask_restful
from flask_restful import inputs
from flask_restful import reqparse
import marshmallow
from oslo_log import log as logging
from oslo_policy import policy

from warre.api.v1.resources import base
from warre.api.v1.schemas import flavor as schemas
from warre.common import exceptions
from warre.common import policies
from warre.extensions import db
from warre import models


LOG = logging.getLogger(__name__)


class FlavorList(base.Resource):

    POLICY_PREFIX = policies.FLAVOR_PREFIX
    schema = schemas.flavors

    def _get_all_flavors(self):
        return db.session.query(models.Flavor)

    def _get_flavors(self):
        return db.session.query(models.Flavor).\
            join(models.FlavorProject, isouter=True). \
            filter(models.Flavor.active == True). \
            filter(db.or_(  # noqa
                models.FlavorProject.project_id == self.context.project_id,
                models.Flavor.is_public == True))  # noqa

    def get(self, **kwargs):
        try:
            self.authorize('list')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        parser = reqparse.RequestParser()
        parser.add_argument('limit', type=int)
        parser.add_argument('all_projects', type=bool)
        args = parser.parse_args()
        query = self._get_flavors()

        if args.get('all_projects') and self.authorize(
                'list:all', do_raise=False):
            query = self._get_all_flavors()
        else:
            query = self._get_flavors()

        return self.paginate(query, args)

    def post(self, **kwargs):
        try:
            self.authorize('create')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        json_data = request.get_json()
        if not json_data:
            return {"message": "No input data provided"}, 400

        try:
            flavor = schemas.flavorcreate.load(json_data)
        except marshmallow.ValidationError as err:
            return err.messages, 422

        db.session.add(flavor)
        db.session.commit()

        return schemas.flavor.dump(flavor), 202


class Flavor(base.Resource):

    POLICY_PREFIX = policies.FLAVOR_PREFIX
    schema = schemas.flavor

    def _get_flavor(self, id):
        return db.session.query(models.Flavor) \
                         .filter_by(id=id).first_or_404()

    def get(self, id):
        flavor = self._get_flavor(id)

        try:
            self.authorize('get')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        return self.schema.dump(flavor)

    def patch(self, id):
        data = request.get_json()

        errors = schemas.flavorupdate.validate(data)
        if errors:
            flask_restful.abort(400, message=errors)

        flavor = self._get_flavor(id)
        try:
            self.authorize('update')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(404,
                                message="Flavor {} dosn't exist".format(id))

        errors = schemas.flavorupdate.validate(data)
        if errors:
            flask_restful.abort(401, message="Not authorized to edit")

        flavor = schemas.flavorupdate.load(data, instance=flavor)
        db.session.commit()

        return self.schema.dump(flavor)

    def delete(self, id):
        flavor = self._get_flavor(id)
        try:
            self.authorize('delete')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(
                404, message="Flavor {} dosn't exist".format(id))
        try:
            self.manager.delete_flavor(self.context, flavor)
        except exceptions.FlavorInUse as err:
            return {'error_message': str(err)}, 409
        return '', 204


class FlavorFreeSlot(Flavor):

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
            self.authorize('get')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        # Get all reservations for this flavor
        flavor = self._get_flavor(id)

        start = args.start
        end = args.end

        if flavor.start and flavor.start > start:
            start = flavor.start

        if flavor.end and flavor.end < end:
            end = flavor.end

        reservations = db.session.query(models.Reservation) \
            .filter(models.Reservation.end >= start) \
            .filter(models.Reservation.start <= end) \
            .filter(models.Reservation.status.in_(
                (models.Reservation.ALLOCATED,
                 models.Reservation.ACTIVE))) \
            .filter_by(flavor_id=flavor.id).all()

        # the real thing begins here
        # Pass 1: segmentation and marking
        # put every start, end date into a list
        time_list = list(chain.from_iterable(
            [(r.start, 'start'), (r.end, 'end')] for r in reservations))
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
            return self.schema.dump([{
                "start": start,
                "end": end
                }])
        query = []
        start_free = start
        # Pass3: remove busy slots
        for s in busy_slots:
            if s["start"] <= start <= s["end"]:
                start_free = s["end"]
            else:
                if start_free < s["start"]:
                    query.append({
                        "start": start_free,
                        "end": s["start"]
                    })
                start_free = s["end"]
        # add the last one
        if start_free < end:
            query.append({
                "start": start_free,
                "end": end
            })

        return self.schema.dump(query)
