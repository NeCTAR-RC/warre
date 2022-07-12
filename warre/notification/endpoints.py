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

import functools

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from sqlalchemy import exc as s_exc

from warre import app
from warre.common import notifications
from warre.common import rpc
from warre.extensions import db
from warre import models
from warre.notification import user


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def app_context(f):
    @functools.wraps(f)
    def decorated(self, *args, **kwargs):
        with self.app.app_context():
            return f(self, *args, **kwargs)
    return decorated


class NotificationEndpoints(object):

    def __init__(self):
        self.app = app.create_app(init_config=False)
        self.notifier = rpc.get_notifier()

    def sample(self, ctxt, publisher_id, event_type, payload, metadata):
        try:
            LOG.debug('Processing notification for payload %s', payload)
            traits = {d[0]: d[2] for d in payload[0]['traits']}
            event_type = payload[0].get('event_type')
            if event_type == 'lease.event.end_lease':
                event = 'end'
            elif event_type == 'lease.event.start_lease':
                event = 'start'
            elif event_type == 'lease.event.before_end':
                event = 'before_end'
            else:
                LOG.debug("Received unhandled event %s", event_type)
                return
            self._handle_event(ctxt, traits['lease_id'], event)
        except Exception:
            LOG.exception('Unable to handle notification: %s', payload)

        return messaging.NotificationResult.HANDLED

    def _handle_event(self, ctxt, lease_id, event):
        try:
            reservation = db.session.query(models.Reservation) \
                .filter_by(lease_id=lease_id).one()
        except s_exc.InvalidRequestError as e:
            LOG.error("No reservation with lease ID %s", lease_id)
            LOG.exception(e)
        else:
            status = None
            if event == 'start':
                status = models.Reservation.ACTIVE
            elif event == 'end':
                status = models.Reservation.COMPLETE

            if status:
                self._update_reservation(ctxt, reservation, status, event)

            user.send_message(reservation, event)

    @app_context
    def _update_reservation(self, ctxt, reservation, status, event):
        reservation.status = status
        db.session.add(reservation)
        db.session.commit()

        self.notifier.info(ctxt, f'warre.reservation.{event}',
                           notifications.format_reservation(reservation))

        LOG.info("Updated reservation %s to %s", reservation.id, status)
