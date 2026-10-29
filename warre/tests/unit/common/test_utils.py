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

import datetime

from freezegun import freeze_time

from warre.common import utils
from warre.tests.unit import base


class TestNormaliseTime(base.TestCase):
    def test_none(self):
        self.assertIsNone(utils.normalise_time(None))

    def test_naive_strips_seconds_and_microseconds(self):
        timestamp = datetime.datetime(2030, 1, 1, 10, 30, 45, 123456)
        self.assertEqual(
            datetime.datetime(2030, 1, 1, 10, 30),
            utils.normalise_time(timestamp),
        )

    def test_aware_converted_to_naive_utc(self):
        tz = datetime.timezone(datetime.timedelta(hours=10))
        timestamp = datetime.datetime(
            2030, 1, 1, 10, 30, 45, 123456, tzinfo=tz
        )
        result = utils.normalise_time(timestamp)
        self.assertIsNone(result.tzinfo)
        self.assertEqual(datetime.datetime(2030, 1, 1, 0, 30), result)


class TestUtcnow(base.TestCase):
    def test_utcnow_is_naive(self):
        self.assertIsNone(utils.utcnow().tzinfo)

    @freeze_time("2021-01-27")
    def test_utcnow_respects_freezegun(self):
        self.assertEqual(datetime.datetime(2021, 1, 27), utils.utcnow())

    @freeze_time("2021-01-27 10:30:00+10:00")
    def test_utcnow_is_utc(self):
        self.assertEqual(datetime.datetime(2021, 1, 27, 0, 30), utils.utcnow())
