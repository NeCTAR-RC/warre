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

from unittest import mock

from oslo_config import cfg

from warre.tests.unit import base
from warre.worker import periodic


class TestPeriodicTaskService(base.TestCase):
    @mock.patch("warre.worker.periodic.threading.Thread")
    @mock.patch("warre.worker.periodic.periodics.PeriodicWorker")
    def test_run_uses_configured_interval(self, mock_worker, mock_thread):
        # The interval is set after the module has been imported, as happens
        # when the config file is parsed in the worker's main().
        cfg.CONF.set_override("periodic_task_interval", 60, group="worker")
        self.addCleanup(
            cfg.CONF.clear_override, "periodic_task_interval", group="worker"
        )
        manager = mock.Mock()
        service = periodic.PeriodicTaskService(0, cfg.CONF, manager)

        service.run()

        mock_worker.assert_called_once()
        callables = mock_worker.call_args[0][0]
        tasks = {c[0].__name__: c[0] for c in callables}
        self.assertEqual(
            {
                "clean_old_reservations",
                "clean_old_maintenance_windows",
                "notify_exists",
            },
            set(tasks),
        )
        for task in tasks.values():
            self.assertEqual(60, task._periodic_spacing)

        mock_thread.assert_called_once_with(
            target=mock_worker.return_value.start, daemon=True
        )
        mock_thread.return_value.start.assert_called_once_with()

        for name, task in tasks.items():
            task()
            getattr(manager, name).assert_called_once_with()

    def test_terminate(self):
        service = periodic.PeriodicTaskService(0, cfg.CONF, mock.Mock())
        service.worker = mock.Mock()
        service.t = mock.Mock()

        service.terminate()

        service.worker.stop.assert_called_once_with()
        service.worker.wait.assert_called_once_with()
        service.t.join.assert_called_once_with()
