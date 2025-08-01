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

from freezegun import freeze_time

from warre.common import exceptions
from warre.extensions import db
from warre import manager
from warre import models
from warre.tests.unit import base


class TestManager(base.TestCase):
    def setUp(self):
        super().setUp()
        # Create some data to muddy the waters
        self.flavor = self.create_flavor()
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime(2020, 1, 1),
            end=datetime(2020, 1, 2),
        )

    @mock.patch("warre.worker.api.WorkerAPI")
    def test_create_reservation(self, mock_worker):
        worker = mock_worker.return_value
        flavor = self.create_flavor()
        reservation = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )
        mgr = manager.Manager()
        reservation = mgr.create_reservation(self.context, reservation)

        self.assertEqual(base.PROJECT_ID, reservation.project_id)
        self.assertEqual(base.USER_ID, reservation.user_id)
        self.assertEqual(flavor, reservation.flavor)
        worker.create_lease.assert_called_once_with(
            self.context, reservation.id
        )

    @mock.patch("warre.worker.api.WorkerAPI")
    def test_create_reservation_with_future_allocated_slot(self, mock_worker):
        worker = mock_worker.return_value
        flavor = self.create_flavor(slots=2)
        reservation1 = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2020, 1, 1),
            end=datetime(2020, 1, 2),
            status=models.Reservation.ALLOCATED,
        )
        reservation2 = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2020, 1, 2),
            end=datetime(2020, 1, 3),
            status=models.Reservation.ALLOCATED,
        )
        mgr = manager.Manager()
        mgr.create_reservation(self.context, reservation1)
        mgr.create_reservation(self.context, reservation2)
        # Create another reservation overlapping existing
        reservation3 = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2020, 1, 1),
            end=datetime(2020, 1, 3),
        )
        mgr.create_reservation(self.context, reservation3)
        self.assertEqual(base.PROJECT_ID, reservation3.project_id)
        self.assertEqual(base.USER_ID, reservation3.user_id)
        self.assertEqual(flavor, reservation3.flavor)
        worker.create_lease.assert_has_calls(
            [
                mock.call(
                    self.context,
                    reservation1.id,
                ),
                mock.call(
                    self.context,
                    reservation2.id,
                ),
                mock.call(
                    self.context,
                    reservation3.id,
                ),
            ]
        )

    def test_create_reservation_flavor_not_active(self):
        flavor = self.create_flavor(active=False)
        reservation = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )
        mgr = manager.Manager()

        with self.assertRaisesRegex(
            exceptions.InvalidReservation, "Flavor is not available"
        ):
            mgr.create_reservation(self.context, reservation)

    def test_create_reservation_flavor_private(self):
        flavor = self.create_flavor(is_public=False)
        reservation = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )
        mgr = manager.Manager()

        with self.assertRaisesRegex(
            exceptions.InvalidReservation, "Flavor is not accessible"
        ):
            mgr.create_reservation(self.context, reservation)

    def test_create_reservation_flavor_end_time_bad(self):
        flavor = self.create_flavor(end=datetime(2021, 1, 2))
        reservation = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 3),
        )
        mgr = manager.Manager()

        with self.assertRaisesRegex(
            exceptions.InvalidReservation,
            f"Reservation end time after flavor end time of {flavor.end}",
        ):
            mgr.create_reservation(self.context, reservation)

    def test_create_reservation_flavor_start_time_bad(self):
        flavor = self.create_flavor(start=datetime(2021, 1, 2))
        reservation = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 3),
        )
        mgr = manager.Manager()

        with self.assertRaisesRegex(
            exceptions.InvalidReservation,
            "Reservation start time before flavor "
            f"start time of {flavor.start}",
        ):
            mgr.create_reservation(self.context, reservation)

    def test_create_reservation_start_time_bad(self):
        flavor = self.create_flavor()
        reservation = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2021, 1, 3),
            end=datetime(2021, 1, 1),
        )
        mgr = manager.Manager()

        with self.assertRaisesRegex(
            exceptions.InvalidReservation,
            f"Reservation start time of {reservation.start} after "
            f"reservation end time of {reservation.end}",
        ):
            mgr.create_reservation(self.context, reservation)

    def test_create_reservation_no_slots(self):
        flavor = self.create_flavor(slots=1)
        reservation1 = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2020, 1, 1),
            end=datetime(2020, 1, 2),
            status=models.Reservation.ALLOCATED,
        )
        mgr = manager.Manager()
        mgr.create_reservation(self.context, reservation1)
        # Create another reservation with same time slot
        reservation2 = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2020, 1, 1),
            end=datetime(2020, 1, 2),
        )

        with self.assertRaisesRegex(
            exceptions.InvalidReservation, "No capacity"
        ):
            mgr.create_reservation(self.context, reservation2)

    def test_create_reservation_no_slots_multi_instance(self):
        flavor = self.create_flavor(slots=5)
        reservation1 = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2020, 1, 1),
            end=datetime(2020, 1, 2),
            status=models.Reservation.ALLOCATED,
            instance_count=5,
        )
        mgr = manager.Manager()
        mgr.create_reservation(self.context, reservation1)
        # Create another reservation with same time slot
        reservation2 = models.Reservation(
            flavor_id=flavor.id,
            start=datetime(2020, 1, 1),
            end=datetime(2020, 1, 2),
        )

        with self.assertRaisesRegex(
            exceptions.InvalidReservation, "No capacity"
        ):
            mgr.create_reservation(self.context, reservation2)

    @mock.patch("warre.common.blazar.BlazarClient")
    def test_delete_reservation(self, mock_blazar):
        blazar_client = mock_blazar.return_value
        flavor = self.create_flavor()
        reservations_pre = db.session.query(models.Reservation).all()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )

        mgr = manager.Manager()
        mgr.delete_reservation(self.context, reservation)
        blazar_client.delete_lease.assert_not_called()
        reservations = db.session.query(models.Reservation).all()
        self.assertEqual(reservations_pre, reservations)

    @mock.patch("warre.common.blazar.BlazarClient")
    def test_delete_reservation_with_lease(self, mock_blazar):
        blazar_client = mock_blazar.return_value
        flavor = self.create_flavor()
        reservations_pre = db.session.query(models.Reservation).all()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )
        reservation.lease_id = "foobar"
        db.session.add(reservation)
        db.session.commit()

        mgr = manager.Manager()
        mgr.delete_reservation(self.context, reservation)
        blazar_client.delete_lease.assert_called_once_with(
            reservation.lease_id
        )
        reservations = db.session.query(models.Reservation).all()
        self.assertEqual(reservations_pre, reservations)

    @mock.patch("warre.common.blazar.BlazarClient")
    def test_extend_reservation(self, mock_blazar):
        blazar_client = mock_blazar.return_value
        flavor = self.create_flavor()
        reservation = self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )
        reservation.lease_id = "foobar"
        self.create_reservation(
            status=models.Reservation.ALLOCATED,
            flavor_id=flavor.id,
            start=datetime(2021, 1, 5),
            end=datetime(2021, 1, 7),
        )

        new_end = datetime(2021, 1, 3)
        mgr = manager.Manager()
        reservation = mgr.extend_reservation(
            self.context, reservation, new_end
        )
        reservation_db = db.session.query(models.Reservation).get(
            reservation.id
        )

        self.assertEqual(new_end, reservation.end)
        self.assertEqual(reservation_db, reservation)
        blazar_client.update_lease.assert_called_once_with(
            "foobar", end_date=new_end
        )

    @mock.patch("warre.common.blazar.BlazarClient")
    def test_extend_reservation_blazar_error(self, mock_blazar):
        blazar_client = mock_blazar.return_value
        flavor = self.create_flavor()
        reservation = self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )
        reservation.lease_id = "foobar"

        new_end = datetime(2021, 1, 3)
        mgr = manager.Manager()
        blazar_client.update_lease.side_effect = Exception
        with self.assertRaisesRegex(
            exceptions.InvalidReservation, "Failed to extend lease"
        ):
            reservation = mgr.extend_reservation(
                self.context, reservation, new_end
            )

    def test_extend_reservation_no_lease(self):
        flavor = self.create_flavor()
        reservation = self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )

        new_end = datetime(2021, 1, 6)
        mgr = manager.Manager()
        with self.assertRaisesRegex(exceptions.InvalidReservation, "No lease"):
            reservation = mgr.extend_reservation(
                self.context, reservation, new_end
            )

    def test_extend_reservation_flavor_end(self):
        flavor = self.create_flavor(end=datetime(2021, 1, 5))
        reservation = self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )
        reservation.lease_id = "foobar"

        new_end = datetime(2021, 1, 6)
        mgr = manager.Manager()
        with self.assertRaisesRegex(
            exceptions.InvalidReservation, "No capacity"
        ):
            reservation = mgr.extend_reservation(
                self.context, reservation, new_end
            )

    @freeze_time("2021-01-26")
    @mock.patch("warre.common.blazar.BlazarClient")
    def test_extend_reservation_too_long(self, mock_blazar):
        flavor = self.create_flavor(max_length_hours=72)
        reservation = self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=flavor.id,
            start=datetime(2021, 1, 25, 0, 0),
            end=datetime(2021, 1, 26, 23, 59),
        )
        reservation.lease_id = "foobar"

        mgr = manager.Manager()
        with self.assertRaisesRegex(
            exceptions.InvalidReservation,
            "Reservation is too long, max allowed is 72 hours",
        ):
            new_end = datetime(2021, 1, 29, 23, 59)
            reservation = mgr.extend_reservation(
                self.context, reservation, new_end
            )

        # ensure its allowed when within limits
        new_end = datetime(2021, 1, 28, 23, 59)
        reservation = mgr.extend_reservation(
            self.context, reservation, new_end
        )

    def test_extend_reservation_no_capacity(self):
        flavor = self.create_flavor()
        reservation = self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=flavor.id,
            start=datetime(2021, 1, 1),
            end=datetime(2021, 1, 2),
        )
        reservation.lease_id = "foobar"
        self.create_reservation(
            status=models.Reservation.ALLOCATED,
            flavor_id=flavor.id,
            start=datetime(2021, 1, 4),
            end=datetime(2021, 1, 5),
        )

        mgr = manager.Manager()
        with self.assertRaisesRegex(
            exceptions.InvalidReservation, "No capacity"
        ):
            new_end = datetime(2021, 1, 5)
            mgr.extend_reservation(self.context, reservation, new_end)
        with self.assertRaisesRegex(
            exceptions.InvalidReservation, "No capacity"
        ):
            new_end = datetime(2021, 1, 6)
            mgr.extend_reservation(self.context, reservation, new_end)
        with self.assertRaisesRegex(
            exceptions.InvalidReservation, "No capacity"
        ):
            new_end = datetime(2021, 1, 7)
            mgr.extend_reservation(self.context, reservation, new_end)

    def test_delete_flavor(self):
        flavors_pre = db.session.query(models.Flavor).all()
        flavor = self.create_flavor()
        mgr = manager.Manager()
        mgr.delete_flavor(self.context, flavor)
        flavors = db.session.query(models.Flavor).all()
        self.assertEqual(flavors_pre, flavors)

    def test_delete_flavor_in_use(self):
        mgr = manager.Manager()
        with self.assertRaisesRegex(
            exceptions.FlavorInUse, f"Flavor {self.flavor.id} is in use"
        ):
            mgr.delete_flavor(self.context, self.flavor)


@freeze_time("2020-01-26")
class TestFlavorFreeSlots(base.TestCase):
    def setUp(self):
        super().setUp()
        self.one_slot_flavor = self.create_flavor()
        self.two_slot_flavor = self.create_flavor(slots=2)
        self.mgr = manager.Manager()

    def test_inactive_flavor(self):
        flavor = self.create_flavor(active=False)
        start = datetime(2021, 1, 1)
        end = datetime(2022, 1, 1)

        self.assertEqual(
            [], self.mgr.flavor_free_slots(self.context, flavor, start, end)
        )

    def test_one_slot_two_reservations(self):
        self.create_reservation(
            flavor_id=self.one_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1),
        )
        self.create_reservation(
            flavor_id=self.one_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 5, 1),
            end=datetime(2021, 6, 1),
        )

        start = datetime(2021, 1, 1)
        end = datetime(2022, 1, 1)

        slots = self.mgr.flavor_free_slots(
            self.context, self.one_slot_flavor, start, end
        )
        self.assertEqual(3, len(slots))

    def test_one_slot_one_reservation(self):
        self.create_reservation(
            flavor_id=self.one_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1),
        )
        start = datetime(2021, 1, 1)
        end = datetime(2022, 1, 1)

        slots = self.mgr.flavor_free_slots(
            self.context, self.one_slot_flavor, start, end
        )
        self.assertEqual(2, len(slots))

    def test_continuous_reservations(self):
        self.create_reservation(
            flavor_id=self.one_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1),
        )
        self.create_reservation(
            flavor_id=self.one_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 3, 1),
            end=datetime(2021, 4, 1),
        )
        start = datetime(2021, 1, 1)
        end = datetime(2022, 1, 1)

        slots = self.mgr.flavor_free_slots(
            self.context, self.one_slot_flavor, start, end
        )
        self.assertEqual(2, len(slots))

    def test_two_slots_one_reservation(self):
        self.create_reservation(
            flavor_id=self.two_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1),
        )
        start = datetime(2021, 1, 1)
        end = datetime(2022, 1, 1)

        slots = self.mgr.flavor_free_slots(
            self.context, self.two_slot_flavor, start, end
        )

        self.assertEqual(1, len(slots))
        self.assertEqual(start, slots[0]["start"])
        self.assertEqual(end, slots[0]["end"])

    def test_two_slots_two_reservations(self):
        self.create_reservation(
            flavor_id=self.two_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1),
        )
        self.create_reservation(
            flavor_id=self.two_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 5, 1),
            end=datetime(2021, 6, 1),
        )
        start = datetime(2021, 1, 1)
        end = datetime(2022, 1, 1)

        slots = self.mgr.flavor_free_slots(
            self.context, self.two_slot_flavor, start, end
        )
        self.assertEqual(1, len(slots))
        self.assertEqual(start, slots[0]["start"])
        self.assertEqual(end, slots[0]["end"])

    def test_two_slots_overlapping_reservations(self):
        self.create_reservation(
            flavor_id=self.two_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1),
        )
        self.create_reservation(
            flavor_id=self.two_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 10),
            end=datetime(2021, 3, 10),
        )
        start = datetime(2021, 1, 1)
        end = datetime(2022, 1, 1)

        slots = self.mgr.flavor_free_slots(
            self.context, self.two_slot_flavor, start, end
        )
        self.assertEqual(2, len(slots))
        self.assertEqual(datetime(2021, 2, 9, 23, 59), slots[0]["end"])
        self.assertEqual(datetime(2021, 3, 1, 0, 1), slots[1]["start"])

    def test_shorter(self):
        self.create_reservation(
            flavor_id=self.one_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 10, 1),
        )
        start = datetime(2021, 5, 1)
        end = datetime(2021, 9, 1)

        slots = self.mgr.flavor_free_slots(
            self.context, self.one_slot_flavor, start, end
        )
        self.assertEqual(0, len(slots))

    def test_overlapping(self):
        self.create_reservation(
            flavor_id=self.one_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 10, 1),
        )
        start = datetime(2021, 5, 1)
        end = datetime(2022, 1, 1)

        slots = self.mgr.flavor_free_slots(
            self.context, self.one_slot_flavor, start, end
        )
        self.assertEqual(1, len(slots))
        self.assertEqual(datetime(2021, 10, 1, 0, 1), slots[0]["start"])
        self.assertEqual(datetime(2022, 1, 1, 0), slots[0]["end"])

    def test_minutes_reservations(self):
        self.create_reservation(
            flavor_id=self.two_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1, 11),
            end=datetime(2021, 2, 1, 20),
        )
        self.create_reservation(
            flavor_id=self.two_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1, 16),
            end=datetime(2021, 2, 1, 22),
        )
        start = datetime(2021, 2, 1)
        end = datetime(2022, 2, 2)

        slots = self.mgr.flavor_free_slots(
            self.context, self.two_slot_flavor, start, end
        )
        self.assertEqual(2, len(slots))
        self.assertEqual(datetime(2021, 2, 1, 15, 59), slots[0]["end"])
        self.assertEqual(datetime(2021, 2, 1, 20, 1), slots[1]["start"])

    def test_flavor_start_end(self):
        start = datetime(2021, 1, 10)
        end = datetime(2021, 1, 20)
        flavor = self.create_flavor(start=start, end=end)
        start = datetime(2021, 1, 1)
        end = datetime(2022, 3, 1)

        slots = self.mgr.flavor_free_slots(self.context, flavor, start, end)

        self.assertEqual(datetime(2021, 1, 10, 0, 0), slots[0]["start"])
        self.assertEqual(datetime(2021, 1, 20, 0, 0), slots[0]["end"])

    def test_two_slots_instance_count(self):
        flavor = self.create_flavor(slots=5)
        self.create_reservation(
            flavor_id=flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 12),
            end=datetime(2021, 2, 20),
            instance_count=3,
        )
        self.create_reservation(
            flavor_id=flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 17),
            end=datetime(2021, 2, 27),
            instance_count=2,
        )
        # muddy waters more
        self.create_reservation(
            flavor_id=flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 22),
            end=datetime(2021, 2, 28),
            instance_count=1,
        )

        start = datetime(2021, 1, 1)
        end = datetime(2022, 1, 1)

        slots = self.mgr.flavor_free_slots(self.context, flavor, start, end)
        self.assertEqual(2, len(slots))
        self.assertEqual(datetime(2021, 2, 16, 23, 59), slots[0]["end"])
        self.assertEqual(datetime(2021, 2, 20, 0, 1), slots[1]["start"])

    def test_one_slot_ignore_self(self):
        reservation = self.create_reservation(
            flavor_id=self.one_slot_flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1),
        )

        start = datetime(2021, 1, 1)
        end = datetime(2022, 1, 1)

        slots = self.mgr.flavor_free_slots(
            self.context,
            self.one_slot_flavor,
            start,
            end,
            reservation=reservation,
        )

        self.assertEqual(1, len(slots))
        self.assertEqual(start, slots[0]["start"])
        self.assertEqual(end, slots[0]["end"])
