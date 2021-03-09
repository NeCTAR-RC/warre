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

from flask import request
import flask_restful
from flask_restful import reqparse
import marshmallow
from oslo_log import log as logging
from oslo_policy import policy

from warre.api.v1.resources import base
from warre.api.v1.schemas import flavor as schemas
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
