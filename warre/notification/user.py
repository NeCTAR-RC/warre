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

import os

import jinja2
from oslo_config import cfg
from oslo_log import log as logging
from stevedore import driver as stevedore_driver

from warre.common import clients
from warre.common import keystone


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


def send_message(reservation, event):
    handled_events = ['create', 'start', 'end', 'before_end']
    if event not in handled_events:
        LOG.error(f"Event {event} not handled by user notifications")

    notifier = stevedore_driver.DriverManager(
                namespace='warre.user.notifier',
                name=CONF.warre.user_notifier,
                invoke_on_load=True
            ).driver

    notifier.send_message(reservation, event)


class UserNotifierBase(object):

    def __init__(self):
        ks_session = keystone.KeystoneSession().get_session()
        self.ks_client = clients.get_admin_keystoneclient(ks_session)

    def send_message(self, reservation, status):
        raise NotImplementedError

    @staticmethod
    def render_template(tmpl, context={}):
        template_dir = os.path.realpath(os.path.join(os.path.dirname(__file__),
                                                     '../',
                                                     'templates'))
        LOG.debug(f"Using template_dir {template_dir}")
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))
        template = env.get_template(tmpl)
        template = template.render(context)
        return template

    def get_user(self, reservation):
        user = reservation.user_id
        user = self.ks_client.users.get(reservation.user_id)
        return user


class TaynacNotifier(UserNotifierBase):

    def send_message(self, reservation, event):
        k_session = keystone.KeystoneSession().get_session()
        taynac = clients.get_taynacclient(k_session)

        template_name = f'{event}.tmpl'
        user = self.get_user(reservation)
        context = {'reservation': reservation, 'user': user}
        subject = 'Nectar Reservation System Notification'
        body = self.render_template(template_name, context)

        message = taynac.messages.send(subject=subject,
                                       body=body,
                                       recipient=user.email)
        LOG.info(f"Created taynac message backend_id={message.backend_id}, "
                 f"requester={user.email}")
        return message.backend_id


class LoggingNotifier(UserNotifierBase):

    def send_message(self, reservation, event):
        user = self.get_user(reservation)
        context = {'reservation': reservation, 'user': user}
        template_name = f'{event}.tmpl'
        description = self.render_template(template_name, context)

        LOG.info("Send user %s notification:", user.email)
        LOG.info(description)
