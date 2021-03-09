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


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class NotificationEndpoints(object):

    def sample(self, ctxt, publisher_id, event_type, payload, metadata):
        try:
            traits = {d[0]: d[2] for d in payload[0]['traits']}
            LOG.debug('Processing notification for %s', traits['resource_id'])
            # resource_id = traits['resource_id']
            # Send events to worker?
        except Exception:
            LOG.exception('Unable to handle notification: %s', payload)

        return messaging.NotificationResult.HANDLED
