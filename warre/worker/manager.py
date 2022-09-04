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
import functools

from keystoneauth1 import loading
from keystoneauth1 import session
from oslo_config import cfg
from oslo_context import context
from oslo_log import log as logging

from warre import app
from warre.common import blazar
from warre.common import clients
from warre.common import keystone
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


class Manager(object):

    def __init__(self):
        self.app = app.create_app(init_config=False)
        self.notifier = rpc.get_notifier()

    @app_context
    def create_lease(self, reservation_id):
        LOG.info("Creating Blazar lease for %s", reservation_id)
        reservation = db.session.query(models.Reservation).filter_by(
            id=reservation_id).first()
        bot_session = self.get_bot_session(reservation.project_id)
        blazar_client = blazar.BlazarClient(session=bot_session)
        try:
            lease = blazar_client.create_lease(reservation)
        except Exception as e:
            reservation.status = models.Reservation.ERROR
            reservation.status_reason = str(e)
            LOG.exception(e)
        else:
            reservation.lease_id = lease['id']
            reservation.compute_flavor = lease.get(
                'reservations')[0].get('flavor_id')
            reservation.status = models.Reservation.ALLOCATED
            LOG.info("Created Blazar lease with ID %s", reservation.lease_id)
        db.session.add(reservation)
        db.session.commit()
        if reservation.status == models.Reservation.ALLOCATED:
            user.send_message(reservation, 'create')

    def ensure_bot_access(self, project_id):
        k_session = keystone.KeystoneSession().get_session()
        client = clients.get_admin_keystoneclient(k_session)
        client.roles.grant(user=CONF.warre.bot_user_id, project=project_id,
                           role=CONF.warre.bot_role_id)

    def get_bot_session(self, project_id):
        self.ensure_bot_access(project_id)
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(auth_url=CONF.warre.bot_auth_url,
                                        user_id=CONF.warre.bot_user_id,
                                        password=CONF.warre.bot_password,
                                        project_id=project_id,
                                        user_domain_id='default',
                                        project_domain_id='default')
        return session.Session(auth=auth)

    @app_context
    def clean_old_reservations(self):
        LOG.info("Cleaning old reservations")
        now = datetime.datetime.now()
        week_ago = now - datetime.timedelta(days=7)
        reservations = db.session.query(models.Reservation)\
                                .filter_by(status=models.Reservation.COMPLETE)\
                                .filter(models.Reservation.end < week_ago)\
                                .all()
        for reservation in reservations:
            LOG.info(f"Deleting finished reservation {reservation}")
            db.session.delete(reservation)
        db.session.commit()

    @app_context
    def notify_exists(self):
        reservations = db.session.query(models.Reservation)\
                                .filter_by(status=models.Reservation.ACTIVE)\
                                .all()

        ctxt = context.RequestContext()
        k_session = keystone.KeystoneSession().get_session()
        nova = clients.get_novaclient(k_session)
        for reservation in reservations:
            if reservation.end < datetime.datetime.now():
                LOG.warn(f"Reservation {reservation} has ended but still "
                         "active, marking as COMPLETE")
                reservation.status = models.Reservation.COMPLETE
                db.session.add(reservation)
                db.session.commit()
                continue
            if reservation.compute_flavor:
                opts = {"all_tenants": True,
                        'tenant_id': reservation.project_id,
                        'flavor': reservation.compute_flavor}
                instances = nova.servers.list(search_opts=opts)
                if instances:
                    LOG.debug(f"Sending in_use notification for {reservation}")
                    self.notifier.info(ctxt, 'warre.reservation.in_use',
                                       notifications.format_reservation(
                                           reservation))
            LOG.debug(f"Sending exists notification for {reservation}")
            self.notifier.info(ctxt, 'warre.reservation.exists',
                               notifications.format_reservation(reservation))
