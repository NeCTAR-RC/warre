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

from oslo_config import cfg

from warre import models
from warre.notification import user
from warre.tests.unit import base

CONF = cfg.CONF


class TestUserNotifierBase(base.TestCase):
    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.flavor = self.create_flavor()
        self.reservation = self.create_reservation(
            flavor_id=self.flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1),
        )

    def test_render_template(self):
        self.reservation.compute_flavor = "foo123455"
        notifier = user.UserNotifierBase()
        template = notifier.render_template(
            "create.tmpl",
            {"reservation": self.reservation, "user": mock.Mock()},
        )
        self.assertIn("2021-02-01 00:00:00", template)
        self.assertIn("2021-03-01 00:00:00", template)
        self.assertIn(
            f"reservation:{self.reservation.compute_flavor}", template
        )

    def test_get_user(self):
        notifier = user.UserNotifierBase()
        kuser = mock.Mock()
        with mock.patch.object(notifier, "ks_client") as mock_ksclient:
            mock_ksclient.users.get.return_value = kuser
            output = notifier.get_user(self.reservation)
            mock_ksclient.users.get.assert_called_once_with(
                self.reservation.user_id
            )
            self.assertEqual(kuser, output)


class TestTaynacNotifier(TestUserNotifierBase):
    @mock.patch("warre.common.clients.get_taynacclient")
    def test_send_message(self, mock_client):
        notifier = user.TaynacNotifier()
        taynac = mock_client.return_value
        taynac.messages.send.return_value = mock.Mock(backend_id="23")

        with mock.patch.object(notifier, "get_user") as mock_get_user:
            kuser = mock.Mock()
            mock_get_user.return_value = kuser
            ticket_id = notifier.send_message(self.reservation, "create")
            taynac.messages.send.assert_called_once_with(
                subject="Nectar Reservation System Notification",
                body=mock.ANY,
                recipient=kuser.email,
            )

            self.assertEqual("23", ticket_id)
