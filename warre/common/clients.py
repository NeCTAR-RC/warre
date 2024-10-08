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

from keystoneclient.v3 import client as ks_client
from novaclient import client as nova_client
from taynacclient import client as taynac_client


def get_admin_keystoneclient(sesh):
    return ks_client.Client(session=sesh)


def get_novaclient(sesh):
    return nova_client.Client("2.87", session=sesh)


def get_taynacclient(sesh):
    return taynac_client.Client("1", session=sesh)
