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

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging

from warre.worker import api
from warre.worker import manager as worker_manager


CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class Endpoints(object):

    target = messaging.Target(version=api.API_VERSION)

    def __init__(self):
        self.manager = worker_manager.Manager()

    def create_lease(self, ctxt, reservation_id):
        self.manager.create_lease(reservation_id)
