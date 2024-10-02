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

from freezegun import freeze_time

from warre.common import notifications
from warre.extensions import db
from warre import models
from warre.tests.unit import base
from warre.worker import manager as worker_manager


@mock.patch("warre.app.create_app")
class TestManager(base.TestCase):
    @mock.patch("warre.worker.manager.user")
    @mock.patch("warre.common.blazar.BlazarClient")
    def test_create_lease(self, mock_blazar, mock_user, mock_app):
        blazar_client = mock_blazar.return_value
        flavor = self.create_flavor()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
        )

        fake_lease = {
            "id": "fake-lease-id",
            "reservations": [{"flavor_id": "fake-nova-flavor"}],
        }
        blazar_client.create_lease.return_value = fake_lease
        manager = worker_manager.Manager()

        with mock.patch.object(manager, "get_bot_session") as get_session:
            session = get_session.return_value

            manager.create_lease(reservation.id)
            mock_blazar.assert_called_once_with(session=session)

            self.assertEqual("fake-lease-id", reservation.lease_id)
            self.assertEqual("fake-nova-flavor", reservation.compute_flavor)
            self.assertEqual("ALLOCATED", reservation.status)
            mock_user.send_message.assert_called_once_with(
                reservation, "create"
            )

    @mock.patch("warre.worker.manager.user")
    @mock.patch("warre.common.blazar.BlazarClient")
    def test_create_lease_error(self, mock_blazar, mock_user, mock_app):
        blazar_client = mock_blazar.return_value
        flavor = self.create_flavor()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            start=datetime.datetime(2021, 1, 1),
            end=datetime.datetime(2021, 1, 2),
        )

        blazar_client.create_lease.side_effect = Exception("Bad ERROR")
        manager = worker_manager.Manager()

        with mock.patch.object(manager, "get_bot_session") as get_session:
            session = get_session.return_value

            manager.create_lease(reservation.id)
            mock_blazar.assert_called_once_with(session=session)

            self.assertIsNone(reservation.lease_id)
            self.assertEqual("ERROR", reservation.status)
            self.assertEqual("Bad ERROR", reservation.status_reason)
            mock_user.send_message.assert_not_called()

    @freeze_time("2021-01-27")
    def test_clean_old_reservations(self, mock_app):
        flavor = self.create_flavor()
        self.create_reservation(
            flavor_id=flavor.id,
            status="ACTIVE",
            start=datetime.datetime(2021, 1, 10),
            end=datetime.datetime(2021, 1, 20),
        )
        self.create_reservation(
            flavor_id=flavor.id,
            status="COMPLETE",
            start=datetime.datetime(2021, 1, 10),
            end=datetime.datetime(2021, 1, 20),
        )
        self.create_reservation(
            flavor_id=flavor.id,
            status="COMPLETE",
            start=datetime.datetime(2021, 1, 3),
            end=datetime.datetime(2021, 1, 19),
        )

        reservations = db.session.query(models.Reservation).all()
        self.assertEqual(3, len(reservations))
        manager = worker_manager.Manager()
        manager.clean_old_reservations()
        reservations = db.session.query(models.Reservation).all()
        self.assertEqual(2, len(reservations))

    @freeze_time("2021-01-27")
    @mock.patch("warre.common.rpc.get_notifier")
    def test_notify_exists(self, mock_get_notifier, mock_app):
        notifier = mock_get_notifier.return_value

        flavor = self.create_flavor()
        res = self.create_reservation(
            flavor_id=flavor.id,
            status="ACTIVE",
            start=datetime.datetime(2021, 1, 10),
            end=datetime.datetime(2021, 1, 30),
        )
        self.create_reservation(
            flavor_id=flavor.id,
            status="COMPLETE",
            start=datetime.datetime(2021, 1, 3),
            end=datetime.datetime(2021, 2, 20),
        )

        manager = worker_manager.Manager()
        manager.notify_exists()

        notifier.info.assert_called_once_with(
            mock.ANY,
            "warre.reservation.exists",
            notifications.format_reservation(res),
        )

    @freeze_time("2021-01-27")
    @mock.patch("warre.common.rpc.get_notifier")
    def test_notify_exists_bad_active(self, mock_get_notifier, mock_app):
        notifier = mock_get_notifier.return_value

        flavor = self.create_flavor()
        res = self.create_reservation(
            flavor_id=flavor.id,
            status="ACTIVE",
            start=datetime.datetime(2021, 1, 10),
            end=datetime.datetime(2021, 1, 26),
        )
        self.create_reservation(
            flavor_id=flavor.id,
            status="COMPLETE",
            start=datetime.datetime(2021, 1, 3),
            end=datetime.datetime(2021, 2, 20),
        )

        manager = worker_manager.Manager()
        manager.notify_exists()

        notifier.info.assert_not_called()
        res_new = db.session.query(models.Reservation).get(res.id)
        self.assertEqual(models.Reservation.COMPLETE, res_new.status)

    @freeze_time("2021-01-27")
    @mock.patch("warre.common.clients.get_novaclient")
    @mock.patch("warre.common.rpc.get_notifier")
    def test_notify_exists_in_use(
        self, mock_get_notifier, mock_nova, mock_app
    ):
        notifier = mock_get_notifier.return_value

        flavor = self.create_flavor()
        res = self.create_reservation(
            flavor_id=flavor.id,
            status="ACTIVE",
            start=datetime.datetime(2021, 1, 10),
            end=datetime.datetime(2021, 1, 30),
        )
        res.compute_flavor = "compute-flavor-id"

        nova_client = mock_nova.return_value
        nova_client.servers.list.return_value = [mock.Mock()]
        manager = worker_manager.Manager()
        manager.notify_exists()

        nova_client.servers.list.assert_called_once_with(
            search_opts={
                "all_tenants": True,
                "tenant_id": res.project_id,
                "flavor": res.compute_flavor,
            }
        )
        notifier.info.assert_has_calls(
            [
                mock.call(
                    mock.ANY,
                    "warre.reservation.in_use",
                    notifications.format_reservation(res),
                ),
                mock.call(
                    mock.ANY,
                    "warre.reservation.exists",
                    notifications.format_reservation(res),
                ),
            ]
        )

    @freeze_time("2021-01-27")
    @mock.patch("warre.common.clients.get_novaclient")
    @mock.patch("warre.common.rpc.get_notifier")
    def test_notify_exists_not_in_use(
        self, mock_get_notifier, mock_nova, mock_app
    ):
        notifier = mock_get_notifier.return_value

        flavor = self.create_flavor()
        res = self.create_reservation(
            flavor_id=flavor.id,
            status="ACTIVE",
            start=datetime.datetime(2021, 1, 10),
            end=datetime.datetime(2021, 1, 30),
        )
        res.compute_flavor = "compute-flavor-id"

        nova_client = mock_nova.return_value
        nova_client.servers.list.return_value = []
        manager = worker_manager.Manager()
        manager.notify_exists()

        nova_client.servers.list.assert_called_once_with(
            search_opts={
                "all_tenants": True,
                "tenant_id": res.project_id,
                "flavor": res.compute_flavor,
            }
        )
        notifier.info.assert_has_calls(
            [
                mock.call(
                    mock.ANY,
                    "warre.reservation.exists",
                    notifications.format_reservation(res),
                ),
            ]
        )
