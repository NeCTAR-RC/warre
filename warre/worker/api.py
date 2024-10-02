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

import oslo_messaging

from warre.common import rpc

# Current API version
API_VERSION = "1.0"


class WorkerAPI:
    """Worker api

    Version history:

    1.0 - Add create_lease
    """

    def __init__(self):
        target = oslo_messaging.Target(
            topic="warre-worker", version=API_VERSION
        )
        self._client = rpc.get_client(target)

    def create_lease(self, ctxt, reservation_id):
        cctxt = self._client.prepare(version="1.0")
        cctxt.cast(ctxt, "create_lease", reservation_id=reservation_id)
