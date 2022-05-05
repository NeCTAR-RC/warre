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

from unittest import mock

from warre.tests.unit import base


class TestLimitsAPI(base.ApiTestCase):

    @mock.patch('warre.quota.get_enforcer')
    def test_limits_list(self, mock_get_enforcer):
        mock_enforcer = mock_get_enforcer.return_value
        mock_enforcer.get_project_limits.return_value = \
            [('hours', 1), ('reservation', 2)]
        response = self.client.get('/v1/limits/')

        self.assert200(response)
        results = response.get_json()
        expected = {
            'absolute': {
                'maxHours': 1,
                'maxReservations': 2,
                'totalHoursUsed': 0,
                'totalReservationsUsed': 0
            }
        }
        self.assertEqual(expected, results)

    def test_limits_list_project(self):
        response = self.client.get('/v1/limits/?project-id=123')
        self.assert403(response)


class TestAdminLimitsAPI(TestLimitsAPI):

    ROLES = ['admin']

    @mock.patch('warre.quota.get_enforcer')
    def test_limits_list_project(self, mock_get_enforer):
        response = self.client.get('/v1/limits/?project-id=123')
        self.assert200(response)
