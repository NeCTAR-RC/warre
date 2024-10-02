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


@mock.patch("warre.notification.endpoints.user")
@mock.patch("warre.common.rpc.get_notifier")
@mock.patch("warre.app.create_app")
class TestEndpoints(base.TestCase):
    def test_sample_start(self, mock_app, mock_get_notifier, mock_user):
        self._test_sample("lease.event.start_lease", models.Reservation.ACTIVE)
        notifier = mock_get_notifier.return_value
        notifier.info.assert_called_once_with(
            self.context, "warre.reservation.start", mock.ANY
        )
        mock_user.send_message.assert_called_once_with(mock.ANY, "start")

    def test_sample_end(self, mock_app, mock_get_notifier, mock_user):
        self._test_sample("lease.event.end_lease", models.Reservation.COMPLETE)
        notifier = mock_get_notifier.return_value
        notifier.info.assert_called_once_with(
            self.context, "warre.reservation.end", mock.ANY
        )
        mock_user.send_message.assert_called_once_with(mock.ANY, "end")

    def test_sample_before_end(self, mock_app, mock_get_notifier, mock_user):
        self._test_sample(
            "lease.event.before_end", models.Reservation.ALLOCATED
        )

        notifier = mock_get_notifier.return_value
        notifier.info.assert_not_called()
        mock_user.send_message.assert_called_once_with(mock.ANY, "before_end")

    def test_sample_unknown_lease(
        self, mock_app, mock_get_notifier, mock_user
    ):
        self._test_sample(
            "lease.event.end_lease",
            models.Reservation.ALLOCATED,
            lease_id=None,
        )

        notifier = mock_get_notifier.return_value
        notifier.info.assert_not_called()
        mock_user.send_message.assert_not_called()

    def _test_sample(self, event, status, lease_id="test-lease-id"):
        flavor = self.create_flavor()
        reservation = self.create_reservation(
            flavor_id=flavor.id,
            status=models.Reservation.ALLOCATED,
            start=datetime(2021, 2, 1),
            end=datetime(2021, 3, 1),
        )
        reservation.lease_id = "test-lease-id"
        db.session.add(reservation)
        db.session.commit()

        payload = [
            {
                "event_type": event,
                "traits": [
                    ["lease_id", 1, lease_id],
                    ["user_id", 1, "615e48919bb94abba759e35c69cee01a"],
                    ["end_date", 4, "2021-04-23T06:00:00"],
                    ["service", 1, "blazar.lease"],
                    ["tenant_id", 1, "094ae1e2c08f4eddb444a9d9db71ab40"],
                    [
                        "request_id",
                        1,
                        "req-930eebd7-283f-4a72-9a7e-0cc41720e30c",
                    ],
                    ["project_id", 1, "094ae1e2c08f4eddb444a9d9db71ab40"],
                    ["start_date", 4, "2021-04-23T05:10:00"],
                ],
                "message_signature": "1bf6be8b0a16a4040c4d3451028052a417e4a365b",  # noqa
                "raw": {},
                "generated": "2021-04-23T05:09:58.392627",
                "message_id": "9e1a8bbd-25d6-4db9-81eb-c142a8def002",
            }
        ]

        ep = endpoints.NotificationEndpoints()
        self.assertEqual(models.Reservation.ALLOCATED, reservation.status)

        ep.sample(self.context, "pub-id", "event", payload, {})
        reservation = db.session.query(models.Reservation).get(reservation.id)
        self.assertEqual(status, reservation.status)
