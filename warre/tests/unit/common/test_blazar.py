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

from blazarclient import exception as blazar_exc
from warre.common import blazar
from warre.tests.unit import base


class TestBlazar(base.TestCase):
    def test_create_lease(self):
        session = mock.Mock()
        flavor = self.create_flavor(
            extra_specs={"bar": "foo"}, ephemeral_gb=50
        )

        client = blazar.BlazarClient(session)
        with mock.patch.object(client, "client") as mock_client:
            reservation = self.create_reservation(
                flavor_id=flavor.id,
                start=datetime.datetime(2021, 1, 1),
                end=datetime.datetime(2021, 1, 2),
            )

            lease = client.create_lease(reservation)
            mock_client.lease.create.assert_called_once_with(
                name=f"Reservation {reservation.id}",
                start="2021-01-01 00:00",
                end="2021-01-02 00:00",
                reservations=[
                    {
                        "resource_type": "virtual:instance",
                        "amount": 1,
                        "vcpus": 4,
                        "memory_mb": 1024,
                        "disk_gb": 30,
                        "ephemeral_gb": 50,
                        "affinity": None,
                        "resource_properties": None,
                        "extra_specs": {"bar": "foo"},
                    }
                ],
                events=[],
            )

            self.assertEqual(mock_client.lease.create.return_value, lease)

    def test_delete_lease(self):
        session = mock.Mock()
        client = blazar.BlazarClient(session)
        lease_id = "fake-id"
        with mock.patch.object(client, "client") as mock_client:
            client.delete_lease(lease_id)

            mock_client.lease.delete.assert_called_once_with(lease_id)

    def test_delete_lease_not_found(self):
        session = mock.Mock()
        client = blazar.BlazarClient(session)
        lease_id = "fake-id"
        with mock.patch.object(client, "client") as mock_client:
            mock_client.lease.delete.side_effect = (
                blazar_exc.BlazarClientException(code=404)
            )
            client.delete_lease(lease_id)

            mock_client.lease.delete.assert_called_once_with(lease_id)

    def test_delete_lease_error(self):
        session = mock.Mock()
        client = blazar.BlazarClient(session)
        lease_id = "fake-id"
        with mock.patch.object(client, "client") as mock_client:
            mock_client.lease.delete.side_effect = (
                blazar_exc.BlazarClientException(code=500)
            )

            with self.assertRaises(blazar_exc.BlazarClientException):
                client.delete_lease(lease_id)

    def test_update_lease(self):
        session = mock.Mock()
        client = blazar.BlazarClient(session)
        lease_id = "fake-id"
        with mock.patch.object(client, "client") as mock_client:
            client.update_lease(
                lease_id,
                end_date=datetime.datetime(2022, 1, 1, 23, 59),
                foo="bar",
            )

            mock_client.lease.update.assert_called_once_with(
                lease_id, end_date="2022-01-01 23:59", foo="bar"
            )
