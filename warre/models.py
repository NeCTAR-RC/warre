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

import math

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
    active = db.Column(db.Boolean())
    properties = db.Column(db.String(255))
    max_length_hours = db.Column(db.Integer, nullable=False)
    slots = db.Column(db.Integer, nullable=False)
    is_public = db.Column(db.Boolean(), default=True)
    extra_specs = db.Column(db.JSON)
    start = db.Column(db.DateTime())
    end = db.Column(db.DateTime())
    projects = db.relationship("FlavorProject", back_populates="flavor",
                                   lazy='dynamic', cascade="all,delete")

    def __init__(self, name, vcpu, memory_mb, disk_gb, description=None,
                 active=True, properties=None, max_length_hours=504, slots=1,
                 is_public=True, extra_specs={}, start=None, end=None):
        self.id = uuidutils.generate_uuid()
        self.name = name
        self.description = description
        self.vcpu = vcpu
        self.memory_mb = memory_mb
        self.disk_gb = disk_gb
        self.active = active
        self.max_length_hours = max_length_hours
        self.slots = slots
        self.properties = properties
        self.is_public = is_public
        self.extra_specs = extra_specs
        self.start = start
        self.end = end

    def __repr__(self):
        return "<Flavor '%s', '%s')>" % (self.id, self.name)


class FlavorProject(db.Model):

    __table_args__ = (
        db.UniqueConstraint('project_id', 'flavor_id'),
    )
    id = db.Column(db.String(64), primary_key=True)
    project_id = db.Column(db.String(64), nullable=False)
    flavor_id = db.Column(db.String(64), db.ForeignKey(Flavor.id),
                          nullable=False)
    flavor = db.relationship("Flavor")

    def __init__(self, project_id, flavor_id):
        self.id = uuidutils.generate_uuid()
        self.project_id = project_id
        flavor = db.session.query(Flavor).get(flavor_id)
        if not flavor:
            raise exceptions.FlavorDoesNotExist()
        self.flavor_id = flavor_id


class Reservation(db.Model):

    PENDING_CREATE = 'PENDING_CREATE'
    ERROR = 'ERROR'
    ALLOCATED = 'ALLOCATED'
    ACTIVE = 'ACTIVE'
    COMPLETE = 'COMPLETE'

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(64), nullable=False)
    project_id = db.Column(db.String(64), nullable=False)
    flavor_id = db.Column(db.String(64), db.ForeignKey(Flavor.id),
                          nullable=False)
    flavor = db.relationship("Flavor")
    lease_id = db.Column(db.String(64))
    status = db.Column(db.String(16), nullable=False)
    start = db.Column(db.DateTime(), nullable=False)
    end = db.Column(db.DateTime(), nullable=False)
    instance_count = db.Column(db.Integer(), nullable=False, default=1)
    status_reason = db.Column(db.String(255))

    def __init__(self, flavor_id, start, end, status=PENDING_CREATE,
            instance_count=1):
        self.id = uuidutils.generate_uuid()
        self.status = status
        flavor = db.session.query(Flavor).get(flavor_id)
        if not flavor:
            raise exceptions.FlavorDoesNotExist()
        self.flavor_id = flavor_id
        self.start = start
        self.end = end
        self.instance_count = instance_count

    def __repr__(self):
        return "<Reservation '%s')>" % self.id

    @property
    def total_hours(self):
        length_seconds = (self.end - self.start).total_seconds()
        return math.ceil(length_seconds / 60 / 60)
