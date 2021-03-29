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

import cotyledon
from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_messaging.rpc import dispatcher

from warre.notification import endpoints


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ConsumerService(cotyledon.Service):

    def __init__(self, worker_id, conf):
        super(ConsumerService, self).__init__(worker_id)
        self.conf = conf
        self.topic = 'warre-notification'
        self.server = conf.host
        self.endpoints = []
        self.access_policy = dispatcher.DefaultRPCAccessPolicy
        self.message_listener = None

    def run(self):
        LOG.info('Starting consumer...')
        transport = messaging.get_notification_transport(CONF)
        targets = [
            messaging.Target(exchange='ceilometer',
                             topic='warre')
        ]
        self.endpoints = [endpoints.NotificationEndpoints()]
        self.message_listener = messaging.get_notification_listener(
            transport, targets, self.endpoints, executor='threading')
        self.message_listener.start()

    def terminate(self):
        if self.message_listener:
            LOG.info('Stopping consumer...')
            self.message_listener.stop()

            LOG.info('Consumer successfully stopped.  Waiting for '
                     'final messages to be processed...')
            self.message_listener.wait()
        if self.endpoints:
            LOG.info('Shutting down endpoint notification executors...')
            for e in self.endpoints:
                try:
                    e.worker.executor.shutdown()
                except AttributeError:
                    pass
        super(ConsumerService, self).terminate()
