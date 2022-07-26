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

from warre.common import notifications
from warre.tests.unit import base


class TestNotifications(base.TestCase):

    def test_format_reservation(self):
        flavor = self.create_flavor()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2))

        reservation_dict = notifications.format_reservation(reservation)
        expected = {'end': datetime.datetime(2021, 1, 2, 0, 0),
                    'flavor': {'active': True,
                               'availability_zone': None,
                               'category': None,
                               'disk_gb': 30,
                               'ephemeral_gb': 0,
                               'end': None,
                               'id': flavor.id,
                               'memory_mb': 1024,
                               'name': 'test.small',
                               'start': None,
                               'vcpu': 4},
                    'id': reservation.id,
                    'instance_count': 1,
                    'lease_id': None,
                    'project_id': 'ksprojectid1',
                    'start': datetime.datetime(2021, 1, 1, 0, 0),
                    'user_id': 'ksuserid1'}
        self.assertEqual(expected, reservation_dict)

    def test_format_flavor(self):
        flavor = self.create_flavor(extra_specs={'bar': 'foo'})
        flavor_dict = notifications.format_flavor(flavor)
        expected = {'id': flavor.id,
                    'name': 'test.small',
                    'vcpu': 4,
                    'memory_mb': 1024,
                    'disk_gb': 30,
                    'ephemeral_gb': 0,
                    'active': True,
                    'category': None,
                    'availability_zone': None,
                    'start': None,
                    'end': None}
        self.assertEqual(expected, flavor_dict)
