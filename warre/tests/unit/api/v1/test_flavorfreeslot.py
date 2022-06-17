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


@mock.patch('warre.quota.get_enforcer', new=mock.Mock())
class TestFlavorFreeSlotAPI(base.ApiTestCase):

    def setUp(self):
        super().setUp()
        self.one_slot_flavor = self.create_flavor()
        self.two_slot_flavor = self.create_flavor(slots=2)

    def test_list_empty_free_slot(self):
        url = f'/v1/flavors/{self.one_slot_flavor.id}/freeslots/'
        response = self.client.get(url)
        self.assertStatus(response, 200)
        # only 1 big freeslot
        results = response.get_json()
        self.assertEqual(1, len(results))

        url = f'/v1/flavors/{self.two_slot_flavor.id}/freeslots/'
        response = self.client.get(url)
        self.assertStatus(response, 200)
        # only 1 big freeslot
        results = response.get_json()
        self.assertEqual(1, len(results))

    def test_querystring(self):
        url = f'/v1/flavors/{self.one_slot_flavor.id}/freeslots/'
        start_date = '2021-02-01'
        end_date = '2021-03-01'
        response = self.client.get(url,
            query_string = {'start': start_date, 'end': end_date})
        self.assertStatus(response, 200)
        results = response.get_json()
        self.assertIn(start_date, results[0]['start'])
        self.assertIn(end_date, results[0]['end'])
