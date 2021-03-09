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

from warre.extensions import db
from warre import models
from warre.tests.unit import base


class TestFlavorAPI(base.ApiTestCase):

    def test_flavor_list(self):
        self.create_flavor()
        response = self.client.get('/v1/flavors/')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(1, len(results))

    def test_flavor_list_private(self):
        self.create_flavor(is_public=False)
        response = self.client.get('/v1/flavors/')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(0, len(results))

    def test_flavor_list_no_access(self):
        flavor = self.create_flavor(is_public=False)
        self.create_flavorproject(flavor_id=flavor.id, project_id='bogus_id')
        response = self.client.get('/v1/flavors/')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(0, len(results))

    def test_flavor_list_with_access(self):
        flavor = self.create_flavor(is_public=False)
        self.create_flavorproject(flavor_id=flavor.id,
                                  project_id=base.PROJECT_ID)
        response = self.client.get('/v1/flavors/')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(1, len(results))

    def test_flavor_list_all_projects(self):
        self.create_flavor(is_public=True)
        self.create_flavor(is_public=False)
        response = self.client.get('/v1/flavors/?all_projects=1')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(1, len(results))

    def test_flavor_create(self):
        data = {'name': 'test.create',
                'vcpu': 1,
                'memory_mb': 10,
                'disk_gb': 20,
                'max_length_hours': 1,
                'slots': 1}
        response = self.client.post('/v1/flavors/', json=data)
        self.assertStatus(response, 202)
        flavor = db.session.query(models.Flavor).all()[0]
        api_flavor = response.get_json()
        self.assertEqual(flavor.name, api_flavor.get('name'))


class TestAdminFlavorAPI(TestFlavorAPI):

    ROLES = ['admin']

    def test_flavor_list_all_projects(self):
        self.create_flavor(is_public=True)
        self.create_flavor(is_public=False)
        response = self.client.get('/v1/flavors/?all_projects=1')

        self.assert200(response)
        results = response.get_json().get('results')
        self.assertEqual(2, len(results))
