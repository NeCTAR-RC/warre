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


from blazarclient import client as blazarclient
from warre.common import keystone


class BlazarClient(object):

    def __init__(self, session=None):
        if session is None:
            session = keystone.KeystoneSession().get_session()
        self.client = blazarclient.Client(
            session=session,
            service_type='reservation')

    def create_lease(self, reservation):
        reservation_info = {
            'resource_type': 'virtual:instance',
            'amount': 1,
            'vcpus': reservation.flavor.vcpu,
            'memory_mb': reservation.flavor.memory_mb,
            'disk_gb': reservation.flavor.disk_gb,
            'affinity': False,
            'resource_properties': reservation.flavor.properties,
        }
        name = 'Reservation %s' % reservation.id
        start = reservation.start.strftime('%Y-%m-%d %H:%M')
        end = reservation.end.strftime('%Y-%m-%d %H:%M')
        lease = self.client.lease.create(
            name=name, start=start, end=end,
            reservations=[reservation_info], events=[])
        return lease

    def delete_lease(self, lease_id):
        self.client.lease.delete(lease_id)
