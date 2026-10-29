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

from unittest import mock

from warre.common import rpc
from warre.tests.unit import base


@mock.patch('warre.common.rpc.messaging.Notifier')
@mock.patch('warre.common.rpc.messaging.get_notification_transport')
@mock.patch('warre.common.rpc.messaging.get_rpc_transport')
class TestRpcInit(base.TestCase):
    def setUp(self):
        super().setUp()
        # Keep the transports created by create_app() for the rest of the
        # suite and start each test from an uninitialised state.
        saved = (rpc.TRANSPORT, rpc.NOTIFICATION_TRANSPORT, rpc.NOTIFIER)
        self.addCleanup(self._restore, saved)
        rpc.TRANSPORT = rpc.NOTIFICATION_TRANSPORT = rpc.NOTIFIER = None

    @staticmethod
    def _restore(saved):
        rpc.TRANSPORT, rpc.NOTIFICATION_TRANSPORT, rpc.NOTIFIER = saved

    def test_init(self, mock_rpc, mock_notif, mock_notifier):
        rpc.init()

        mock_rpc.assert_called_once()
        mock_notif.assert_called_once()
        mock_notifier.assert_called_once_with(mock_notif.return_value)
        self.assertEqual(mock_rpc.return_value, rpc.TRANSPORT)
        self.assertEqual(mock_notif.return_value, rpc.NOTIFICATION_TRANSPORT)
        self.assertEqual(mock_notifier.return_value, rpc.NOTIFIER)

    def test_init_twice_reuses_transports(
        self, mock_rpc, mock_notif, mock_notifier
    ):
        rpc.init()
        transport = rpc.TRANSPORT
        notification_transport = rpc.NOTIFICATION_TRANSPORT
        notifier = rpc.NOTIFIER

        rpc.init()

        mock_rpc.assert_called_once()
        mock_notif.assert_called_once()
        mock_notifier.assert_called_once()
        self.assertIs(transport, rpc.TRANSPORT)
        self.assertIs(notification_transport, rpc.NOTIFICATION_TRANSPORT)
        self.assertIs(notifier, rpc.NOTIFIER)

    def test_cleanup_then_init_creates_new_transports(
        self, mock_rpc, mock_notif, mock_notifier
    ):
        rpc.init()
        transport = rpc.TRANSPORT
        notification_transport = rpc.NOTIFICATION_TRANSPORT

        rpc.cleanup()

        transport.cleanup.assert_called_once_with()
        notification_transport.cleanup.assert_called_once_with()
        self.assertIsNone(rpc.TRANSPORT)
        self.assertIsNone(rpc.NOTIFICATION_TRANSPORT)
        self.assertIsNone(rpc.NOTIFIER)

        rpc.init()

        self.assertEqual(2, mock_rpc.call_count)
        self.assertEqual(2, mock_notif.call_count)
        self.assertEqual(2, mock_notifier.call_count)
        self.assertIsNotNone(rpc.TRANSPORT)
        self.assertIsNotNone(rpc.NOTIFICATION_TRANSPORT)
        self.assertIsNotNone(rpc.NOTIFIER)
