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

from warre.extensions import db
from warre import models
from warre.tests.unit import base


@mock.patch("warre.quota.get_enforcer", new=mock.Mock())
class TestMaintenanceWindowAPI(base.ApiTestCase):
    ROLES = ["admin"]

    def setUp(self):
        super().setUp()
        self.flavor = self.create_flavor()

    def test_list_empty(self):
        response = self.client.get("/v1/maintenancewindows/")
        self.assert200(response)
        results = response.get_json().get("results")
        self.assertEqual(0, len(results))

    def test_list(self):
        self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 2),
            flavors=[self.flavor],
        )
        response = self.client.get("/v1/maintenancewindows/")
        self.assert200(response)
        results = response.get_json().get("results")
        self.assertEqual(1, len(results))
        self.assertEqual(1, len(results[0]["flavors"]))
        self.assertEqual(self.flavor.id, results[0]["flavors"][0]["id"])

    def test_create(self):
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-02T00:00:00+00:00",
            "note": "Planned maintenance",
            "flavor_ids": [self.flavor.id],
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 201)
        result = response.get_json()
        self.assertEqual("Planned maintenance", result["note"])
        self.assertEqual(1, len(result["flavors"]))
        self.assertEqual(self.flavor.id, result["flavors"][0]["id"])
        self.assertEqual(self.flavor.name, result["flavors"][0]["name"])

    def test_create_no_flavors(self):
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-02T00:00:00+00:00",
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 201)
        result = response.get_json()
        self.assertEqual([], result["flavors"])

    def test_create_end_before_start(self):
        data = {
            "start": "2026-05-10T00:00:00+00:00",
            "end": "2026-05-01T00:00:00+00:00",
            "flavor_ids": [self.flavor.id],
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 400)

    def test_create_end_equals_start(self):
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-01T00:00:00+00:00",
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 400)

    @freeze_time("2026-05-15")
    def test_create_start_in_past(self):
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-20T00:00:00+00:00",
            "flavor_ids": [self.flavor.id],
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 400)

    @freeze_time("2026-06-01")
    def test_create_entirely_in_past(self):
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-10T00:00:00+00:00",
            "flavor_ids": [self.flavor.id],
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 400)

    def test_create_bad_flavor(self):
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-02T00:00:00+00:00",
            "flavor_ids": ["nonexistent-id"],
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 404)

    def test_get(self):
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 2),
            note="Test window",
            flavors=[self.flavor],
        )
        response = self.client.get(f"/v1/maintenancewindows/{window.id}/")
        self.assert200(response)
        result = response.get_json()
        self.assertEqual(window.id, result["id"])
        self.assertEqual("Test window", result["note"])
        self.assertEqual(1, len(result["flavors"]))

    def test_get_not_found(self):
        response = self.client.get("/v1/maintenancewindows/does-not-exist/")
        self.assert404(response)

    def test_update_note(self):
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 2),
            note="Original",
            flavors=[self.flavor],
        )
        response = self.client.patch(
            f"/v1/maintenancewindows/{window.id}/",
            json={"note": "Updated"},
        )
        self.assert200(response)
        result = response.get_json()
        self.assertEqual("Updated", result["note"])
        self.assertIn("2026-05-01", result["start"])
        self.assertIn("2026-05-02", result["end"])
        self.assertEqual(1, len(result["flavors"]))

    def test_update_times(self):
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 2),
            flavors=[self.flavor],
        )
        response = self.client.patch(
            f"/v1/maintenancewindows/{window.id}/",
            json={
                "start": "2026-06-01T00:00:00+00:00",
                "end": "2026-06-03T00:00:00+00:00",
            },
        )
        self.assert200(response)
        result = response.get_json()
        self.assertIn("2026-06-01", result["start"])
        self.assertIn("2026-06-03", result["end"])

    def test_update_end_before_start(self):
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 10),
            flavors=[self.flavor],
        )
        response = self.client.patch(
            f"/v1/maintenancewindows/{window.id}/",
            json={"end": "2026-04-01T00:00:00+00:00"},
        )
        self.assertStatus(response, 400)

    @freeze_time("2026-05-15")
    def test_update_start_to_past(self):
        window = self.create_maintenance_window(
            start=datetime(2026, 6, 1),
            end=datetime(2026, 6, 10),
            flavors=[self.flavor],
        )
        response = self.client.patch(
            f"/v1/maintenancewindows/{window.id}/",
            json={
                "start": "2026-05-01T00:00:00+00:00",
                "end": "2026-05-10T00:00:00+00:00",
            },
        )
        self.assertStatus(response, 400)

    @freeze_time("2026-05-15")
    def test_update_note_on_started_window(self):
        # An already-started window (start in the past) can still be patched
        # for fields that don't change start/end.
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 20),
            flavors=[self.flavor],
        )
        response = self.client.patch(
            f"/v1/maintenancewindows/{window.id}/",
            json={"note": "still ongoing"},
        )
        self.assert200(response)
        self.assertEqual("still ongoing", response.get_json()["note"])

    def test_update_replace_flavors(self):
        other_flavor = self.create_flavor()
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 2),
            flavors=[self.flavor],
        )
        response = self.client.patch(
            f"/v1/maintenancewindows/{window.id}/",
            json={"flavor_ids": [other_flavor.id]},
        )
        self.assert200(response)
        result = response.get_json()
        self.assertEqual(1, len(result["flavors"]))
        self.assertEqual(other_flavor.id, result["flavors"][0]["id"])

    def test_update_clear_flavors(self):
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 2),
            flavors=[self.flavor],
        )
        response = self.client.patch(
            f"/v1/maintenancewindows/{window.id}/",
            json={"flavor_ids": []},
        )
        self.assert200(response)
        result = response.get_json()
        self.assertEqual([], result["flavors"])

    def test_update_bad_flavor(self):
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 2),
            flavors=[self.flavor],
        )
        response = self.client.patch(
            f"/v1/maintenancewindows/{window.id}/",
            json={"flavor_ids": ["nonexistent-id"]},
        )
        self.assertStatus(response, 404)

    def test_update_conflicts_with_reservation(self):
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 2),
            flavors=[self.flavor],
        )
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime(2026, 6, 1),
            end=datetime(2026, 6, 3),
            status=models.Reservation.ALLOCATED,
        )
        response = self.client.patch(
            f"/v1/maintenancewindows/{window.id}/",
            json={
                "start": "2026-06-01T00:00:00+00:00",
                "end": "2026-06-10T00:00:00+00:00",
            },
        )
        self.assertStatus(response, 409)

    def test_update_not_found(self):
        response = self.client.patch(
            "/v1/maintenancewindows/does-not-exist/",
            json={"note": "x"},
        )
        self.assert404(response)

    def test_delete(self):
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 2),
            flavors=[self.flavor],
        )
        response = self.client.delete(f"/v1/maintenancewindows/{window.id}/")
        self.assertStatus(response, 204)
        self.assertEqual(0, db.session.query(models.MaintenanceWindow).count())

    def test_delete_clears_flavor_association(self):
        window = self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 2),
            flavors=[self.flavor],
        )
        self.client.delete(f"/v1/maintenancewindows/{window.id}/")
        self.assertEqual(1, db.session.query(models.Flavor).count())

    def test_create_conflicts_with_reservation(self):
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 3),
            status=models.Reservation.ALLOCATED,
        )
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-10T00:00:00+00:00",
            "flavor_ids": [self.flavor.id],
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 409)

    def test_create_no_conflict_different_flavor(self):
        other_flavor = self.create_flavor()
        self.create_reservation(
            flavor_id=other_flavor.id,
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 3),
            status=models.Reservation.ALLOCATED,
        )
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-10T00:00:00+00:00",
            "flavor_ids": [self.flavor.id],
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 201)

    def test_create_no_conflict_non_overlapping_time(self):
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime(2026, 4, 1),
            end=datetime(2026, 4, 30),
            status=models.Reservation.ALLOCATED,
        )
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-10T00:00:00+00:00",
            "flavor_ids": [self.flavor.id],
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 201)

    def test_create_no_conflict_completed_reservation(self):
        self.create_reservation(
            flavor_id=self.flavor.id,
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 3),
            status=models.Reservation.COMPLETE,
        )
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-10T00:00:00+00:00",
            "flavor_ids": [self.flavor.id],
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 201)


@mock.patch("warre.quota.get_enforcer", new=mock.Mock())
class TestMaintenanceWindowAPIMember(base.ApiTestCase):
    ROLES = ["member"]

    def test_list(self):
        response = self.client.get("/v1/maintenancewindows/")
        self.assertStatus(response, 200)

    def test_create_forbidden(self):
        data = {
            "start": "2026-05-01T00:00:00+00:00",
            "end": "2026-05-02T00:00:00+00:00",
        }
        response = self.client.post("/v1/maintenancewindows/", json=data)
        self.assertStatus(response, 403)

    def test_update_forbidden(self):
        response = self.client.patch(
            "/v1/maintenancewindows/some-id/",
            json={"note": "x"},
        )
        self.assertStatus(response, 404)


@mock.patch("warre.quota.get_enforcer", new=mock.Mock())
class TestMaintenanceWindowFreeSlots(base.ApiTestCase):
    ROLES = ["admin"]

    def setUp(self):
        super().setUp()
        self.flavor = self.create_flavor()

    def test_freeslot_unaffected_without_window(self):
        url = f"/v1/flavors/{self.flavor.id}/freeslots/"
        response = self.client.get(
            url,
            query_string={
                "start": "2026-05-01",
                "end": "2026-05-10",
            },
        )
        self.assert200(response)
        results = response.get_json()
        self.assertEqual(1, len(results))

    def test_freeslot_blocked_by_maintenance_window(self):
        self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 10),
            flavors=[self.flavor],
        )
        url = f"/v1/flavors/{self.flavor.id}/freeslots/"
        response = self.client.get(
            url,
            query_string={
                "start": "2026-05-01",
                "end": "2026-05-10",
            },
        )
        self.assert200(response)
        results = response.get_json()
        self.assertEqual(0, len(results))

    def test_freeslot_partial_maintenance_window(self):
        self.create_maintenance_window(
            start=datetime(2026, 5, 4),
            end=datetime(2026, 5, 6),
            flavors=[self.flavor],
        )
        url = f"/v1/flavors/{self.flavor.id}/freeslots/"
        response = self.client.get(
            url,
            query_string={
                "start": "2026-05-01",
                "end": "2026-05-10",
            },
        )
        self.assert200(response)
        results = response.get_json()
        # Free before and after the window
        self.assertEqual(2, len(results))
        self.assertIn("2026-05-01", results[0]["start"])
        self.assertIn("2026-05-10", results[1]["end"])

    def test_freeslot_window_on_other_flavor_unaffected(self):
        other_flavor = self.create_flavor()
        self.create_maintenance_window(
            start=datetime(2026, 5, 1),
            end=datetime(2026, 5, 10),
            flavors=[other_flavor],
        )
        url = f"/v1/flavors/{self.flavor.id}/freeslots/"
        response = self.client.get(
            url,
            query_string={
                "start": "2026-05-01",
                "end": "2026-05-10",
            },
        )
        self.assert200(response)
        results = response.get_json()
        self.assertEqual(1, len(results))
