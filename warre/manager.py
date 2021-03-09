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


from warre.common import blazar
from warre.extensions import db
from warre.worker import api as worker_api


class Manager(object):

    def __init__(self):
        self.worker_api = worker_api.WorkerAPI()
        self.blazar = blazar.BlazarClient()

    def create_reservation(self, context, reservation):
        reservation.project_id = context.project_id
        reservation.user_id = context.user_id
        db.session.add(reservation)
        db.session.commit()
        self.worker_api.create_lease(context, reservation.id)
        return reservation

    def delete_reservation(self, context, reservation):
        if reservation.lease_id:
            self.blazar.delete_lease(reservation.lease_id)

        db.session.delete(reservation)
        db.session.commit()
