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

from unittest import mock

import flask_testing
from oslo_config import cfg
from oslo_context import context

from warre import app
from warre.common import keystone
from warre import extensions
from warre.extensions import db
from warre import models


PROJECT_ID = "ksprojectid1"
USER_ID = "ksuserid1"


class TestCase(flask_testing.TestCase):
    def create_app(self):
        return app.create_app(
            {
                "SECRET_KEY": "secret",
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            },
            conf_file="warre/tests/etc/warre.conf",
        )

    def setUp(self):
        super().setUp()
        self.addCleanup(mock.patch.stopall)
        db.create_all()
        self.context = context.RequestContext(
            user_id=USER_ID, project_id=PROJECT_ID
        )

    def tearDown(self):
        super().tearDown()
        db.session.remove()
        db.drop_all()
        cfg.CONF.reset()
        extensions.api.resources = []

    def create_flavor(
        self,
        name="test.small",
        description="Test Flavor",
        vcpu=4,
        memory_mb=1024,
        disk_gb=30,
        **kwargs,
    ):
        flavor = models.Flavor(
            name=name,
            description=description,
            vcpu=vcpu,
            memory_mb=memory_mb,
            disk_gb=disk_gb,
            **kwargs,
        )
        db.session.add(flavor)
        db.session.commit()
        return flavor

    def create_flavorproject(self, **kwargs):
        flavorproject = models.FlavorProject(**kwargs)
        db.session.add(flavorproject)
        db.session.commit()
        return flavorproject

    def create_maintenance_window(self, start, end, note=None, flavors=None):
        window = models.MaintenanceWindow(start=start, end=end, note=note)
        if flavors:
            window.flavors = flavors
        db.session.add(window)
        db.session.commit()
        return window

    def create_reservation(self, project_id=PROJECT_ID, **kwargs):
        reservation = models.Reservation(**kwargs)
        reservation.user_id = USER_ID
        reservation.project_id = project_id
        db.session.add(reservation)
        db.session.commit()
        return reservation


class TestKeystoneWrapper:
    def __init__(self, app, roles, system_scope=None, domain_id=None):
        self.app = app
        self.roles = roles
        self.system_scope = system_scope
        self.domain_id = domain_id
        self.project_id = None if (system_scope or domain_id) else PROJECT_ID

    def __call__(self, environ, start_response):
        cntx = context.RequestContext(
            roles=self.roles,
            project_id=self.project_id,
            user_id=USER_ID,
            system_scope=self.system_scope,
            domain_id=self.domain_id,
        )
        environ[keystone.REQUEST_CONTEXT_ENV] = cntx

        return self.app(environ, start_response)


class ApiTestCase(TestCase):
    ROLES = ["member"]
    SYSTEM_SCOPE = None
    DOMAIN_ID = None

    def setUp(self):
        super().setUp()
        self.init_context()

    def init_context(self):
        self.app.wsgi_app = TestKeystoneWrapper(
            self.app.wsgi_app,
            self.ROLES,
            system_scope=self.SYSTEM_SCOPE,
            domain_id=self.DOMAIN_ID,
        )
