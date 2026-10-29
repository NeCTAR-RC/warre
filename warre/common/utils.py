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


def normalise_time(timestamp):
    """Normalize time in arbitrary timezone to UTC naive object.

    Also truncate to the whole minute by removing the seconds and
    microseconds.
    """

    if timestamp is None:
        return timestamp
    timestamp = timestamp.replace(second=0, microsecond=0)
    offset = timestamp.utcoffset()
    if offset is None:
        return timestamp
    return timestamp.replace(tzinfo=None) - offset


def utcnow():
    """Return the current time as a naive datetime in UTC.

    Replaces the deprecated datetime.datetime.utcnow(). The database
    columns and existing comparisons all use naive UTC datetimes, so
    the timezone is stripped after reading the aware current time.
    """
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
