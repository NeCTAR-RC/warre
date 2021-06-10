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

from oslo_limit import limit

from warre.extensions import db
from warre import models


_ENFORCER = None
EFFECTIVE_STATES = (
    models.Reservation.ACTIVE,
    models.Reservation.ALLOCATED,
    models.Reservation.PENDING_CREATE
)


def get_enforcer():
    global _ENFORCER
    if not _ENFORCER:
        _ENFORCER = limit.Enforcer(get_usage)
    return _ENFORCER


def get_usage(project_id, resource_names):
    return {x: get_usage_by_project(project_id, x) for x in resource_names}


def get_usage_by_project(project_id, resource):
    if resource == 'reservation':
        return db.session.query(models.Reservation) \
            .filter_by(project_id=project_id) \
            .filter(models.Reservation.status.in_(EFFECTIVE_STATES)).count()
    if resource == 'hours':
        total = 0
        reservations = db.session.query(models.Reservation) \
            .filter_by(project_id=project_id) \
            .filter(models.Reservation.status.in_(EFFECTIVE_STATES)).all()
        for r in reservations:
            total += r.total_hours
        return total
