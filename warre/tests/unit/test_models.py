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

from datetime import datetime

from freezegun import freeze_time

from warre import models
from warre.tests.unit import base


class TestModels(base.TestCase):
    @freeze_time("2021-01-27")
    def test_create_reservation_defaults(self):
        flavor = self.create_flavor()
        reservation = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )
        self.assertEqual("PENDING_CREATE", reservation.status)
        self.assertEqual(1, reservation.instance_count)
        self.assertEqual(datetime(2021, 1, 27), reservation.created_at)

    def test_create_flavor_defaults(self):
        flavor = models.Flavor(name="test", vcpu=1, memory_mb=10, disk_gb=5)
        self.assertEqual(0, flavor.ephemeral_gb)
        self.assertEqual(1, flavor.slots)
        self.assertEqual(504, flavor.max_length_hours)
        self.assertTrue(flavor.active)
        self.assertTrue(flavor.is_public)
