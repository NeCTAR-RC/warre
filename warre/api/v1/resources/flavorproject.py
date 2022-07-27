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
from warre.api.v1.schemas import flavorproject as schemas
from warre.common import exceptions
from warre.common import policies
from warre.extensions import db
from warre import models


LOG = logging.getLogger(__name__)


class FlavorProjectList(base.Resource):

    POLICY_PREFIX = policies.FLAVORPROJECT_PREFIX
    schema = schemas.flavorprojects

    def _get_flavorprojects(self):
        return db.session.query(models.FlavorProject)

    def get(self, **kwargs):
        try:
            self.authorize('list')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        parser = reqparse.RequestParser()
        parser.add_argument('limit', type=int)
        parser.add_argument('project_id')
        parser.add_argument('flavor_id')
        args = parser.parse_args()
        project_id = args.get('project_id')
        flavor_id = args.get('flavor_id')

        query = self._get_flavorprojects()
        if project_id:
            query = query.filter_by(project_id=project_id)
        if flavor_id:
            query = query.filter_by(flavor_id=flavor_id)

        return self.paginate(query, args)

    def post(self, **kwargs):
        try:
            self.authorize('create')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        json_data = request.get_json()
        if not json_data:
            return {"error_message": "No input data provided"}, 400

        try:
            flavorproject = schemas.flavorprojectcreate.load(json_data)
        except exceptions.FlavorDoesNotExist:
            return {'error_message': "Flavor does not exist"}, 404
        except marshmallow.ValidationError as err:
            return err.messages, 422

        existing = db.session.query(models.FlavorProject)\
                             .filter_by(project_id=flavorproject.project_id)\
                             .filter_by(flavor_id=flavorproject.flavor_id)\
                             .all()
        if existing:
            return {"error_message": "Already exists"}, 409

        db.session.add(flavorproject)
        db.session.commit()

        return schemas.flavorproject.dump(flavorproject)


class FlavorProject(base.Resource):

    POLICY_PREFIX = policies.FLAVORPROJECT_PREFIX

    def delete(self, id):
        flavorproject = db.session.query(models.FlavorProject) \
            .filter_by(id=id).first_or_404()
        try:
            self.authorize('delete')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(
                404, message="FlavorProject {} dosn't exist".format(id))
        db.session.delete(flavorproject)
        db.session.commit()
        return '', 204
