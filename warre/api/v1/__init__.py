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

from warre.api.v1.resources import flavor
from warre.api.v1.resources import flavorproject
from warre.api.v1.resources import limits
from warre.api.v1.resources import reservation


def initialize_resources(api):
    api.add_resource(flavor.FlavorList, "/v1/flavors/")
    api.add_resource(flavor.Flavor, "/v1/flavors/<id>/")
    api.add_resource(flavor.FlavorFreeSlot, "/v1/flavors/<id>/freeslots/")

    api.add_resource(flavorproject.FlavorProjectList, "/v1/flavorprojects/")
    api.add_resource(flavorproject.FlavorProject, "/v1/flavorprojects/<id>/")

    api.add_resource(reservation.ReservationList, "/v1/reservations/")
    api.add_resource(reservation.Reservation, "/v1/reservations/<id>/")

    api.add_resource(limits.Limits, "/v1/limits/")
