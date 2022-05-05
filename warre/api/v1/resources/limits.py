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


import flask_restful
from flask_restful import reqparse
from oslo_policy import policy

from warre.api.v1.resources import base
from warre import quota


class Limits(base.Resource):

    POLICY_PREFIX = 'warre:limits:%s'

    def get(self, **kwargs):
        parser = reqparse.RequestParser()
        parser.add_argument('project-id')
        args = parser.parse_args()

        if args.get('project-id'):
            try:
                self.authorize('list:all')
            except policy.PolicyNotAuthorized:
                flask_restful.abort(403, message="Not authorised")
            project_id = args.get('project_id')
        else:
            project_id = self.context.project_id

        total_reservations = quota.get_usage_by_project(
            project_id, 'reservation')
        total_hours = quota.get_usage_by_project(project_id, 'hours')

        enforcer = quota.get_enforcer()
        limits = dict(enforcer.get_project_limits(
            project_id, ['hours', 'reservation']))

        absolute = {
            'maxHours': limits.get('hours'),
            'maxReservations': limits.get('reservation'),
            'totalHoursUsed': total_hours,
            'totalReservationsUsed': total_reservations}

        return {'absolute': absolute}
