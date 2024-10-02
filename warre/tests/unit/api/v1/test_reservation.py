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

from warre import models
from warre.tests.unit import base


@mock.patch("warre.quota.get_enforcer", new=mock.Mock())
class TestReservationAPI(base.ApiTestCase):
    def setUp(self):
        super().setUp()
        self.flavor = self.create_flavor()

    def test_list_reservations(self):
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
        )
        response = self.client.get("/v1/reservations/")

        self.assert200(response)
        results = response.get_json().get("results")
        self.assertEqual(1, len(results))

    def test_list_reservations_flavor(self):
        flavor_2 = self.create_flavor()
        self.create_flavor()
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
        )
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 2, 1),
            end=datetime.datetime(2021, 2, 2),
        )
        self.create_reservation(
            flavor_id=flavor_2.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
        )
        response = self.client.get(
            f"/v1/reservations/?flavor_id={self.flavor.id}"
        )

        self.assert200(response)
        results = response.get_json().get("results")
        self.assertEqual(2, len(results))

    def test_list_reservations_non_project(self):
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
            project_id="notmine",
        )
        response = self.client.get("/v1/reservations/")

        self.assert200(response)
        results = response.get_json().get("results")
        self.assertEqual(0, len(results))

    def test_create_reservation(self):
        data = {
            "flavor_id": self.flavor.id,
            "start": "2020-01-01T00:00:00+00:00",
            "end": "2020-01-01T01:00:00+00:00",
        }
        response = self.client.post("/v1/reservations/", json=data)
        self.assert200(response)
        self.assertEqual(1, response.get_json().get("instance_count"))
        self.assertEqual(
            "2020-01-01T00:00:00+00:00", response.get_json().get("start")
        )
        self.assertEqual(
            "2020-01-01T01:00:00+00:00", response.get_json().get("end")
        )

    def test_create_reservation_different_tz(self):
        data = {
            "flavor_id": self.flavor.id,
            "start": "2020-01-01T14:00:00+10:00",
            "end": "2020-01-01T18:00:00+10:00",
        }
        response = self.client.post("/v1/reservations/", json=data)
        self.assert200(response)
        self.assertEqual(1, response.get_json().get("instance_count"))
        self.assertEqual(
            "2020-01-01T04:00:00+00:00", response.get_json().get("start")
        )
        self.assertEqual(
            "2020-01-01T08:00:00+00:00", response.get_json().get("end")
        )

    def test_create_reservation_multiple_instances(self):
        data = {
            "flavor_id": self.flavor.id,
            "start": "2020-01-01T00:00:00+00:00",
            "end": "2020-01-01T01:00:00+00:00",
            "instance_count": 2,
        }
        response = self.client.post("/v1/reservations/", json=data)
        self.assert200(response)
        self.assertEqual(2, response.get_json().get("instance_count"))

    def test_create_reservation_noinput(self):
        data = {}
        response = self.client.post("/v1/reservations/", json=data)
        self.assert400(response)

    def test_create_reservation_bad_flavor(self):
        data = {
            "flavor_id": "bogus",
            "start": "2020-01-01T00:00:00+00:00",
            "end": "2020-02-02T00:00:00+00:00",
        }
        response = self.client.post("/v1/reservations/", json=data)
        self.assert404(response)

    def test_create_reservation_missing_args(self):
        data = {
            "flavor_id": self.flavor.id,
            "start": "2020-01-01T00:00:00+00:00",
        }
        response = self.client.post("/v1/reservations/", json=data)
        self.assertStatus(response, 422)

    def test_get_reservation(self):
        reservation = self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
        )
        response = self.client.get(f"/v1/reservations/{reservation.id}/")
        self.assert200(response)
        reservation_json = response.get_json()
        self.assertEqual(reservation.id, reservation_json.get("id"))
        self.assertEqual(
            reservation.flavor.id, reservation_json["flavor"]["id"]
        )

    def test_update_reservation_invalid_new_end(self):
        reservation = self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1, 0, 0),
            end=datetime.datetime(2021, 1, 2, 23, 59),
        )
        reservation.lease_id = "foo"

        data = {"end": "2021-01-01T23:59:00+00:00"}
        response = self.client.patch(
            f"/v1/reservations/{reservation.id}/", json=data
        )
        self.assert400(response)

    @mock.patch("warre.common.blazar.BlazarClient")
    def test_update_reservation(self, mock_blazar):
        reservation = self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1, 0, 0),
            end=datetime.datetime(2021, 1, 2, 23, 59),
        )
        reservation.lease_id = "foo"

        data = {"end": "2021-01-03T23:59:00+00:00"}
        response = self.client.patch(
            f"/v1/reservations/{reservation.id}/", json=data
        )
        self.assert200(response)
        reservation_json = response.get_json()
        self.assertEqual(
            "2021-01-01T00:00:00+00:00", reservation_json.get("start")
        )
        self.assertEqual(
            "2021-01-03T23:59:00+00:00", reservation_json.get("end")
        )

    @mock.patch("warre.common.blazar.BlazarClient")
    def test_update_reservation_with_tz(self, mock_blazar):
        reservation = self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1, 0, 0),
            end=datetime.datetime(2021, 1, 2, 23, 59),
        )
        reservation.lease_id = "foo"

        data = {"end": "2021-01-03T23:59:00+05:00"}
        response = self.client.patch(
            f"/v1/reservations/{reservation.id}/", json=data
        )
        self.assert200(response)
        reservation_json = response.get_json()
        self.assertEqual(
            "2021-01-01T00:00:00+00:00", reservation_json.get("start")
        )
        self.assertEqual(
            "2021-01-03T18:59:00+00:00", reservation_json.get("end")
        )

    @mock.patch("warre.common.blazar.BlazarClient")
    def test_update_reservation_no_capacity(self, mock_blazar):
        reservation = self.create_reservation(
            status=models.Reservation.ACTIVE,
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1, 0, 0),
            end=datetime.datetime(2021, 1, 2, 23, 59),
        )
        reservation.lease_id = "foo"

        # Create a reservation directly after
        self.create_reservation(
            status=models.Reservation.ALLOCATED,
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 3, 0, 0),
            end=datetime.datetime(2021, 1, 4, 23, 59),
        )

        data = {"end": "2021-01-03T23:59:00+00:00"}
        response = self.client.patch(
            f"/v1/reservations/{reservation.id}/", json=data
        )
        self.assert401(response)
        reservation_json = response.get_json()
        self.assertEqual(
            "Failed to extend reservation: No capacity",
            reservation_json.get("error_message"),
        )


class TestAdminReservationAPI(TestReservationAPI):
    ROLES = ["admin"]

    def test_list_reservations_all_projects(self):
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
            project_id="123",
        )
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
            project_id="987",
        )
        response = self.client.get("/v1/reservations/?all_projects=1")

        self.assert200(response)
        results = response.get_json().get("results")
        self.assertEqual(2, len(results))

    def test_list_reservations_other_project(self):
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
            project_id="123",
        )
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
            project_id="987",
        )
        response = self.client.get("/v1/reservations/?all_projects=1")

        self.assert200(response)
        results = response.get_json().get("results")
        self.assertEqual(2, len(results))
