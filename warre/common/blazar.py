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
from blazarclient import exception as blazar_exc
from warre.common import keystone


LEASE_DATE_FORMAT = "%Y-%m-%d %H:%M"


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
            'amount': reservation.instance_count,
            'vcpus': reservation.flavor.vcpu,
            'memory_mb': reservation.flavor.memory_mb,
            'disk_gb': reservation.flavor.disk_gb,
            'ephemeral_gb': reservation.flavor.ephemeral_gb,
            'affinity': None,
            'resource_properties': reservation.flavor.properties,
            'extra_specs': reservation.flavor.extra_specs,
        }
        name = 'Reservation %s' % reservation.id
        start = reservation.start.strftime(LEASE_DATE_FORMAT)
        end = reservation.end.strftime(LEASE_DATE_FORMAT)
        lease = self.client.lease.create(
            name=name, start=start, end=end,
            reservations=[reservation_info], events=[])
        return lease

    def delete_lease(self, lease_id):
        try:
            self.client.lease.delete(lease_id)
        except blazar_exc.BlazarClientException as e:
            if e.kwargs.get('code') != 404:
                raise e

    def update_lease(self, lease_id, **kwargs):
        if 'end_date' in kwargs:
            kwargs['end_date'] = kwargs['end_date'].strftime(LEASE_DATE_FORMAT)
        self.client.lease.update(lease_id, **kwargs)
