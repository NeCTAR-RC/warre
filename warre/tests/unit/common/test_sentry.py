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

import importlib.metadata
import os
import sys
from unittest import mock

from oslo_config import cfg

from warre.common import sentry
from warre.tests.unit import base


CONF = cfg.CONF
DSN = 'https://key@glitchtip.example.com/1'
RELEASE = 'warre@1.0.0'


@mock.patch('warre.common.sentry._get_release', return_value=RELEASE)
@mock.patch('warre.common.sentry.sentry_sdk')
class TestSentrySetup(base.TestCase):
    def test_setup_no_config(self, mock_sdk, mock_release):
        with mock.patch.dict(os.environ):
            os.environ.pop('SENTRY_DSN', None)
            self.assertFalse(sentry.setup())
        mock_sdk.init.assert_not_called()

    def test_setup_with_dsn(self, mock_sdk, mock_release):
        CONF.set_override('dsn', DSN, group='sentry')
        CONF.set_override('environment', 'testing', group='sentry')
        self.assertTrue(sentry.setup())
        mock_sdk.init.assert_called_once_with(
            dsn=DSN,
            environment='testing',
            release=RELEASE,
            auto_session_tracking=False,
        )
        mock_sdk.set_tag.assert_called_once_with(
            'command', os.path.basename(sys.argv[0])
        )

    def test_setup_dsn_only(self, mock_sdk, mock_release):
        CONF.set_override('dsn', DSN, group='sentry')
        self.assertTrue(sentry.setup())
        mock_sdk.init.assert_called_once_with(
            dsn=DSN,
            environment=None,
            release=RELEASE,
            auto_session_tracking=False,
        )

    def test_setup_dsn_from_environment(self, mock_sdk, mock_release):
        with mock.patch.dict(os.environ, {'SENTRY_DSN': DSN}):
            self.assertTrue(sentry.setup())
        mock_sdk.init.assert_called_once_with(
            dsn=DSN,
            environment=None,
            release=RELEASE,
            auto_session_tracking=False,
        )


class TestGetRelease(base.TestCase):
    def test_get_release(self):
        with mock.patch(
            'warre.common.sentry.importlib.metadata.version',
            return_value='1.0.0',
        ) as mock_version:
            self.assertEqual('warre@1.0.0', sentry._get_release())
        mock_version.assert_called_once_with('warre')

    def test_get_release_not_installed(self):
        with mock.patch(
            'warre.common.sentry.importlib.metadata.version',
            side_effect=importlib.metadata.PackageNotFoundError,
        ):
            self.assertIsNone(sentry._get_release())
