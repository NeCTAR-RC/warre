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

from warre import exceptions
from warre import manager
from warre import models
from warre.tests.unit import base


class TestManager(base.TestCase):

    def test_create_reservation(self):
        flavor = self.create_flavor()
        reservation = models.Reservation(flavor_id=flavor.id,
                                         start=datetime.datetime(2020, 1, 1),
                                         end=datetime.datetime(2020, 1, 2))
        mgr = manager.Manager()
        reservation = mgr.create_reservation(self.context, reservation)

        self.assertEqual(base.PROJECT_ID, reservation.project_id)
        self.assertEqual(base.USER_ID, reservation.user_id)
        self.assertEqual(flavor, reservation.flavor)

    def test_create_reservation_flavor_not_active(self):
        flavor = self.create_flavor(active=False)
        reservation = models.Reservation(flavor_id=flavor.id,
                                         start=datetime.datetime(2020, 1, 1),
                                         end=datetime.datetime(2020, 1, 2))
        mgr = manager.Manager()
        with self.assertRaises(exceptions.InvalidReservation) as cm:
            mgr.create_reservation(self.context, reservation)

        self.assertEqual("Flavor is not available". cm.exception.message)
