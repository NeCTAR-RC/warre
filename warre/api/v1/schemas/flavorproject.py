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


class FlavorProjectSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = models.FlavorProject
        load_instance = True
        include_relationships = True
        datetimeformat = "%Y-%m-%dT%H:%M:%S%z"


class FlavorProjectCreateSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = models.FlavorProject
        load_instance = True
        include_fk = True
        exclude = ("id",)
        datetimeformat = "%Y-%m-%dT%H:%M:%S%z"


flavorproject = FlavorProjectSchema()
flavorprojects = FlavorProjectSchema(many=True)
flavorprojectcreate = FlavorProjectCreateSchema()
