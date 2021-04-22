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
from unittest import mock

from warre.extensions import db
from warre import models
from warre.notification import endpoints
from warre.tests.unit import base


@mock.patch('warre.app.create_app')
class TestEndpoints(base.TestCase):

    def test_sample(self, mock_app):
        pass

    def test_update_lease(self, mock_app):
        lease_id = 'test-lease-id'

        flavor = self.create_flavor()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1))
        reservation.lease_id = lease_id
        db.session.add(reservation)
        db.session.commit()

        ep = endpoints.NotificationEndpoints()
        self.assertEqual(models.Reservation.ALLOCATED, reservation.status)
        ep._update_lease(lease_id, models.Reservation.ACTIVE)
        self.assertEqual(models.Reservation.ACTIVE, reservation.status)

    def test_update_lease_unknown(self, mock_app):
        lease_id = 'test-lease-id'

        flavor = self.create_flavor()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1))
        reservation.lease_id = lease_id
        db.session.add(reservation)
        db.session.commit()

        ep = endpoints.NotificationEndpoints()
        self.assertEqual(models.Reservation.ALLOCATED, reservation.status)
        ep._update_lease('bogus-id', models.Reservation.ACTIVE)
        self.assertEqual(models.Reservation.ALLOCATED, reservation.status)
