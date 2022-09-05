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
        parser.add_argument('category')
        parser.add_argument('availability_zone')
        args = parser.parse_args()
        query = self._get_flavors()

        if args.get('all_projects') and self.authorize(
                'list:all', do_raise=False):
            query = self._get_all_flavors()
        else:
            query = self._get_flavors()

        if args.get('category'):
            query = query.filter(
                models.Flavor.category == args.get('category'))
        az = args.get('availability_zone')
        if az:
            query = query.filter(
                models.Flavor.availability_zone == az)

        query = query.order_by(models.Flavor.name, models.Flavor.memory_mb)
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

        free_slots = self.manager.flavor_free_slots(self.context, flavor,
                                                    start, end)
        return self.schema.dump(free_slots)
