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

from warre.extensions import ma
from warre import models


class FlavorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = models.Flavor
        load_instance = True
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"


class FlavorFreeSlotSchema(ma.Schema):
    start = ma.DateTime()
    end = ma.DateTime()

    class Meta:
        datetimeformat = "%Y-%m-%dT%H:%M:%S+00:00"


class FlavorCreateSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = models.Flavor
        load_instance = True
        datetimeformat = "%Y-%m-%dT%H:%M:%S%z"
        exclude = ("id",)


class FlavorUpdateSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = models.Flavor
        load_instance = True
        datetimeformat = "%Y-%m-%dT%H:%M:%S%z"
        exclude = ("id", "vcpu", "memory_mb", "disk_gb", "properties")


flavor = FlavorSchema()
flavors = FlavorSchema(many=True)
flavorcreate = FlavorCreateSchema()
flavorupdate = FlavorUpdateSchema(partial=True)
freeslots = FlavorFreeSlotSchema(many=True)
