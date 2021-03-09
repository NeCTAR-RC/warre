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
from warre.api.v1.schemas import reservation as schemas
from warre.common import exceptions
from warre.common import policies
from warre.extensions import db
from warre import models


LOG = logging.getLogger(__name__)


class ReservationList(base.Resource):

    POLICY_PREFIX = policies.RESERVATION_PREFIX
    schema = schemas.reservations

    def _get_reservations(self, project_id):
        return db.session.query(models.Reservation) \
            .filter_by(project_id=project_id)

    def get(self, **kwargs):
        try:
            self.authorize('list')
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        parser = reqparse.RequestParser()
        parser.add_argument('limit', type=int)
        args = parser.parse_args()
        query = self._get_reservations(self.oslo_context.project_id)
        return self.paginate(query, args)

    def post(self, **kwargs):
        data = request.get_json()
        if not data:
            return {"message": "No input data provided"}, 400

        # Check some kind of quota

        try:
            reservation = schemas.reservationcreate.load(data)
        except exceptions.FlavorDoesNotExist:
            return "Flavor does not exist", 404
        except marshmallow.ValidationError as err:
            return err.messages, 422

        reservation = self.manager.create_reservation(self.oslo_context,
                                                      reservation)
        return schemas.reservation.dump(reservation)


class Reservation(base.Resource):

    POLICY_PREFIX = policies.RESERVATION_PREFIX
    schema = schemas.reservation

    def _get_reservation(self, id):
        return db.session.query(models.Reservation) \
                         .filter_by(id=id).first_or_404()

    def get(self, id):
        reservation = self._get_reservation(id)

        target = {'project_id': reservation.project_id}
        try:
            self.authorize('get', target)
        except policy.PolicyNotAuthorized:
            flask_restful.abort(
                404, message="Reservation {} doesn't exist".format(id))

        return self.schema.dump(reservation)

    def delete(self, id):
        reservation = self._get_reservation(id)

        target = {'project_id': reservation.project_id}
        try:
            self.authorize('delete', target)
        except policy.PolicyNotAuthorized:
            flask_restful.abort(
                404, message="Reservation {} doesn't exist".format(id))

        self.manager.delete_reservation(self.oslo_context, reservation)
        return '', 204
