#!/usr/bin/env python
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

import sys

import cotyledon
from cotyledon import oslo_config_glue
from oslo_config import cfg

from warre.common import service
from warre.worker import consumer
from warre.worker import manager
from warre.worker import periodic

CONF = cfg.CONF


def main():
    service.prepare_service(sys.argv)

    sm = cotyledon.ServiceManager()

    m = manager.Manager()
    sm.add(consumer.ConsumerService, workers=CONF.worker.workers,
           args=(CONF, m))
    sm.add(periodic.PeriodicTaskService, workers=CONF.worker.workers,
           args=(CONF, m))
    oslo_config_glue.setup(sm, CONF, reload_method="mutate")
    sm.run()


if __name__ == "__main__":
    main()
