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
from unittest import mock

from warre.common import exceptions
from warre.extensions import db
from warre import manager
from warre import models
from warre.tests.unit import base


class TestManager(base.TestCase):

    def setUp(self):
        super().setUp()
        # Create some data to muddy the waters
        flavor = self.create_flavor()
        self.create_reservation(flavor_id=flavor.id,
                                start=datetime.datetime(2020, 1, 1),
                                end=datetime.datetime(2020, 1, 2))

    @mock.patch('warre.worker.api.WorkerAPI')
    def test_create_reservation(self, mock_worker):
        worker = mock_worker.return_value
        flavor = self.create_flavor()
        reservation = models.Reservation(flavor_id=flavor.id,
                                         start=datetime.datetime(2021, 1, 1),
                                         end=datetime.datetime(2021, 1, 2))
        mgr = manager.Manager()
        reservation = mgr.create_reservation(self.context, reservation)

        self.assertEqual(base.PROJECT_ID, reservation.project_id)
        self.assertEqual(base.USER_ID, reservation.user_id)
        self.assertEqual(flavor, reservation.flavor)
        worker.create_lease.assert_called_once_with(self.context,
                                                    reservation.id)

    def test_create_reservation_flavor_not_active(self):
        flavor = self.create_flavor(active=False)
        reservation = models.Reservation(flavor_id=flavor.id,
                                         start=datetime.datetime(2021, 1, 1),
                                         end=datetime.datetime(2021, 1, 2))
        mgr = manager.Manager()

        with self.assertRaisesRegex(exceptions.InvalidReservation,
                                    "Flavor is not available"):
            mgr.create_reservation(self.context, reservation)

    def test_create_reservation_flavor_private(self):
        flavor = self.create_flavor(is_public=False)
        reservation = models.Reservation(flavor_id=flavor.id,
                                         start=datetime.datetime(2021, 1, 1),
                                         end=datetime.datetime(2021, 1, 2))
        mgr = manager.Manager()

        with self.assertRaisesRegex(exceptions.InvalidReservation,
                                    "Flavor is not accessible"):
            mgr.create_reservation(self.context, reservation)

    def test_create_reservation_no_slots(self):
        flavor = self.create_flavor(slots=1)
        reservation1 = models.Reservation(flavor_id=flavor.id,
                                         start=datetime.datetime(2020, 1, 1),
                                         end=datetime.datetime(2020, 1, 2))
        mgr = manager.Manager()
        mgr.create_reservation(self.context, reservation1)
        # Create another reservation with same time slot
        reservation2 = models.Reservation(flavor_id=flavor.id,
                                          start=datetime.datetime(2020, 1, 1),
                                          end=datetime.datetime(2020, 1, 2))

        with self.assertRaisesRegex(exceptions.InvalidReservation,
                                    "No capacity"):
            mgr.create_reservation(self.context, reservation2)

    @mock.patch('warre.common.blazar.BlazarClient')
    def test_delete_reservation(self, mock_blazar):
        blazar_client = mock_blazar.return_value
        flavor = self.create_flavor()
        reservations_pre = db.session.query(models.Reservation).all()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2))

        mgr = manager.Manager()
        mgr.delete_reservation(self.context, reservation)
        blazar_client.delete_lease.assert_not_called()
        reservations = db.session.query(models.Reservation).all()
        self.assertEqual(reservations_pre, reservations)

    @mock.patch('warre.common.blazar.BlazarClient')
    def test_delete_reservation_with_lease(self, mock_blazar):
        blazar_client = mock_blazar.return_value
        flavor = self.create_flavor()
        reservations_pre = db.session.query(models.Reservation).all()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2))
        reservation.lease_id = 'foobar'
        db.session.add(reservation)
        db.session.commit()

        mgr = manager.Manager()
        mgr.delete_reservation(self.context, reservation)
        blazar_client.delete_lease.assert_called_once_with(
            reservation.lease_id)
        reservations = db.session.query(models.Reservation).all()
        self.assertEqual(reservations_pre, reservations)
