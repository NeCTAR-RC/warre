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

from flask import request
import flask_restful
from flask_restful import reqparse
import marshmallow
from oslo_log import log as logging
from oslo_policy import policy

from warre.api.v1.resources import base
from warre.api.v1.schemas import maintenancewindow as schemas
from warre.common import policies
from warre.common import utils
from warre.extensions import db
from warre import models


LOG = logging.getLogger(__name__)


def _has_conflicting_reservation(start, end, flavor_ids):
    return (
        db.session.query(models.Reservation)
        .filter(models.Reservation.end >= start)
        .filter(models.Reservation.start <= end)
        .filter(models.Reservation.flavor_id.in_(flavor_ids))
        .filter(
            models.Reservation.status.in_(
                (
                    models.Reservation.ALLOCATED,
                    models.Reservation.ACTIVE,
                    models.Reservation.PENDING_CREATE,
                )
            )
        )
        .count()
    ) > 0


class MaintenanceWindowList(base.Resource):
    POLICY_PREFIX = policies.MAINTENANCEWINDOW_PREFIX
    schema = schemas.maintenancewindows

    def get(self, **kwargs):
        try:
            self.authorize("list")
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        parser = reqparse.RequestParser()
        parser.add_argument("limit", type=int, location="args")
        args = parser.parse_args()

        query = db.session.query(models.MaintenanceWindow).order_by(
            models.MaintenanceWindow.start
        )
        return self.paginate(query, args)

    def post(self, **kwargs):
        try:
            self.authorize("create")
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        json_data = request.get_json()
        if not json_data:
            return {"message": "No input data provided"}, 400

        flavor_ids = json_data.pop("flavor_ids", [])

        try:
            window = schemas.maintenancewindowcreate.load(json_data)
        except marshmallow.ValidationError as err:
            return err.messages, 422

        window.start = utils.normalise_time(window.start)
        window.end = utils.normalise_time(window.end)

        if window.end <= window.start:
            return {
                "error_message": "Maintenance window end time must be after start time"
            }, 400

        now = datetime.datetime.utcnow().replace(second=0, microsecond=0)
        if window.start < now:
            return {
                "error_message": "Maintenance window cannot start in the past"
            }, 400

        if flavor_ids:
            flavors = (
                db.session.query(models.Flavor)
                .filter(models.Flavor.id.in_(flavor_ids))
                .all()
            )
            if len(flavors) != len(flavor_ids):
                return {"error_message": "One or more flavors not found"}, 404

            if _has_conflicting_reservation(
                window.start, window.end, [f.id for f in flavors]
            ):
                return {
                    "error_message": "Maintenance window conflicts with existing reservations"
                }, 409

            window.flavors = flavors

        db.session.add(window)
        db.session.commit()

        return schemas.maintenancewindow.dump(window), 201


class MaintenanceWindowResource(base.Resource):
    POLICY_PREFIX = policies.MAINTENANCEWINDOW_PREFIX
    schema = schemas.maintenancewindow

    def _get_window(self, id):
        return (
            db.session.query(models.MaintenanceWindow)
            .filter_by(id=id)
            .first_or_404()
        )

    def get(self, id):
        try:
            self.authorize("get")
        except policy.PolicyNotAuthorized:
            flask_restful.abort(403, message="Not authorised")

        window = self._get_window(id)
        return self.schema.dump(window)

    def patch(self, id):
        try:
            self.authorize("update")
        except policy.PolicyNotAuthorized:
            flask_restful.abort(
                404, message=f"MaintenanceWindow {id} doesn't exist"
            )

        json_data = request.get_json()
        if not json_data:
            return {"message": "No input data provided"}, 400

        window = self._get_window(id)

        flavor_ids = json_data.pop("flavor_ids", None)

        try:
            window = schemas.maintenancewindowupdate.load(
                json_data, instance=window
            )
        except marshmallow.ValidationError as err:
            return err.messages, 422

        window.start = utils.normalise_time(window.start)
        window.end = utils.normalise_time(window.end)

        if window.end <= window.start:
            return {
                "error_message": "Maintenance window end time must be after start time"
            }, 400

        if "start" in json_data:
            now = datetime.datetime.utcnow().replace(second=0, microsecond=0)
            if window.start < now:
                return {
                    "error_message": "Maintenance window cannot start in the past"
                }, 400

        if flavor_ids is not None:
            if flavor_ids:
                flavors = (
                    db.session.query(models.Flavor)
                    .filter(models.Flavor.id.in_(flavor_ids))
                    .all()
                )
                if len(flavors) != len(flavor_ids):
                    return {
                        "error_message": "One or more flavors not found"
                    }, 404
            else:
                flavors = []
            window.flavors = flavors

        if window.flavors and _has_conflicting_reservation(
            window.start, window.end, [f.id for f in window.flavors]
        ):
            db.session.rollback()
            return {
                "error_message": "Maintenance window conflicts with existing reservations"
            }, 409

        db.session.commit()

        return schemas.maintenancewindow.dump(window)

    def delete(self, id):
        try:
            self.authorize("delete")
        except policy.PolicyNotAuthorized:
            flask_restful.abort(
                404, message=f"MaintenanceWindow {id} doesn't exist"
            )
        window = self._get_window(id)
        db.session.delete(window)
        db.session.commit()
        return "", 204
