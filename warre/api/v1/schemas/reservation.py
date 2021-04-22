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


class ReservationSchema(ma.SQLAlchemyAutoSchema):

    class Meta(object):
        model = models.Reservation
        load_instance = True
        include_relationships = True


class ReservationCreateSchema(ma.SQLAlchemyAutoSchema):

    class Meta(object):
        model = models.Reservation
        load_instance = True
        include_fk = True
        exclude = ('id', 'user_id', 'project_id', 'status', 'lease_id')


reservation = ReservationSchema()
reservations = ReservationSchema(many=True)
reservationcreate = ReservationCreateSchema()
