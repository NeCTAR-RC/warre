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
from oslo_log import log
from oslo_utils import uuidutils

from warre.common import exceptions
from warre.extensions import db


CONF = cfg.CONF
LOG = log.getLogger(__name__)


class Flavor(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(255))
    vcpu = db.Column(db.Integer, nullable=False)
    memory_mb = db.Column(db.Integer, nullable=False)
    disk_gb = db.Column(db.Integer, nullable=False)
    # active
    # properties

    def __init__(self, name, description, vcpu, memory_mb, disk_gb):
        self.id = uuidutils.generate_uuid()
        self.name = name
        self.description = description
        self.vcpu = vcpu
        self.memory_mb = memory_mb
        self.disk_gb = disk_gb

    def __repr__(self):
        return "<Flavor '%s', '%s')>" % (self.id, self.name)


class Reservation(db.Model):

    PENDING_CREATE = 'PENDING_CREATE'
    ERROR = 'ERROR'
    ALLOCATED = 'ALLOCATED'

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(64), nullable=False)
    project_id = db.Column(db.String(64), nullable=False)
    flavor_id = db.Column(db.String(64), db.ForeignKey(Flavor.id),
                          nullable=False)
    flavor = db.relationship("Flavor")
    lease_id = db.Column(db.String(64))
    status = db.Column(db.String(16))

    def __init__(self, flavor_id):
        self.id = uuidutils.generate_uuid()
        self.status = self.PENDING_CREATE
        flavor = db.session.query(Flavor).get(flavor_id)
        if not flavor:
            raise exceptions.FlavorDoesNotExist()
        self.flavor_id = flavor_id

    def __repr__(self):
        return "<Reservation '%s')>" % self.id
