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


def format_reservation(reservation):
    return {
        'id': reservation.id,
        'flavor': format_flavor(reservation.flavor),
        'user_id': reservation.user_id,
        'project_id': reservation.project_id,
        'lease_id': reservation.lease_id,
        'start': reservation.start,
        'end': reservation.end,
        'instance_count': reservation.instance_count,
    }


def format_flavor(flavor):
    return {
        'id': flavor.id,
        'name': flavor.name,
        'vcpu': flavor.vcpu,
        'memory_mb': flavor.memory_mb,
        'disk_gb': flavor.disk_gb,
        'active': flavor.active,
        'category': flavor.category,
        'availability_zone': flavor.availability_zone,
        'start': flavor.start,
        'end': flavor.end,
    }
