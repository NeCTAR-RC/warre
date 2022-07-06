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

import threading

import cotyledon
from futurist import periodics
from oslo_config import cfg
from oslo_log import log as logging


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PeriodicTaskService(cotyledon.Service):

    def __init__(self, worker_id, conf, manager):
        super().__init__(worker_id)
        self.conf = conf
        self.server = conf.host
        self.worker = None
        self.t = None
        self.endpoints = []
        self.manager = manager

    @periodics.periodic(CONF.worker.periodic_task_interval)
    def clean_old_reservations(self):
        LOG.info("Running periodic task clean_old_reservations")
        self.manager.clean_old_reservations()

    @periodics.periodic(CONF.worker.periodic_task_interval)
    def notify_exists(self):
        """Send reservation exists notifications

        Used for usage and auditing purposes
        """
        LOG.info("Sending reservation exists notifications")
        self.manager.notify_exists()

    def run(self):
        LOG.info('Starting peridoic task thread...')

        callables = [
            (self.clean_old_reservations, (), {}),
            (self.notify_exists, (), {}),
        ]
        self.worker = periodics.PeriodicWorker(callables)
        self.t = threading.Thread(target=self.worker.start, daemon=True)
        self.t.start()

    def terminate(self):
        if self.worker:
            self.worker.stop()
            self.worker.wait()
        if self.t:
            self.t.join()

        super().terminate()
