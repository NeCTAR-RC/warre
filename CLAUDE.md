# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run all tests: `tox -e py314`
- Run a single test module (stestr takes a regex, not a path): `tox -e py314 -- warre.tests.unit.test_manager`
- Run a single test class or method: `tox -e py314 -- warre.tests.unit.test_manager.TestFlavorFreeSlots`
- Run with coverage: `tox -e cover`
- Run lint checks: `tox -e pep8`
- Generate config sample: `tox -e genconfig`
- Generate policy sample: `tox -e genpolicy`

Always run tests before committing code.

## Project Overview

Warre is the Nectar Reservation System — a standalone OpenStack service that extends Blazar with fleet reservation management. It exposes a REST API for creating time-bounded reservations of compute flavors, enforces per-project quotas, and integrates with Blazar to provision actual resources.

## Architecture: Three Services

### warre-api (Flask REST API)
Entry point: `warre/cmd/api.py` → `warre/app.py:create_app()`

- Resources in `warre/api/v1/resources/`: flavors, reservations, flavor-project access, maintenance windows, quota limits
- Authentication via Keystone middleware; authorization via oslo.policy RBAC (`warre/common/policy.py`)
- Quota enforcement via oslo.limit (`warre/quota.py`) — limits per-project reservation count and total hours
- Reservation creation is synchronous to DB but async to Blazar: the API writes the record (status=`PENDING_CREATE`) and dispatches an RPC call to the worker

### warre-worker (Async Task Queue)
Entry point: `warre/cmd/worker.py` — runs via Cotyledon service manager

- `ConsumerService` (`warre/worker/consumer.py`): RPC listener; executes Blazar lease creation
- `PeriodicTaskService` (`warre/worker/periodic.py`): background jobs — deletes COMPLETE reservations older than 7 days, sends heartbeat notifications for ACTIVE reservations
- `Manager` (`warre/worker/manager.py`): business logic for worker tasks
- The worker uses a separate Keystone bot account (configured via `warre.bot_*` options) to call Blazar on behalf of users

### warre-notification (Event Consumer)
Entry point: `warre/cmd/notification.py`

- Listens to Blazar lease events via oslo.messaging
- `lease.event.start_lease` → sets reservation status to `ACTIVE`
- `lease.event.end_lease` → sets reservation status to `COMPLETE`
- `lease.event.before_end_lease` → sends expiry warning to user
- User notification driver is pluggable (stevedore): `logging` for dev, `taynac` for production

## Key Models (`warre/models.py`)

- **Flavor**: compute profile with `slots` (capacity limit), `max_length_hours`, optional `start`/`end` availability window, `is_public` flag, and many-to-many `projects` for private access
- **MaintenanceWindow**: time range linked to flavors (many-to-many); occupies all slots during its window
- **Reservation**: links a user/project to a flavor+Blazar lease; tracks `status` (`PENDING_CREATE` → `ALLOCATED` → `ACTIVE` → `COMPLETE`/`ERROR`), `instance_count`, and `start`/`end` UTC datetimes

## Free Slot Calculation (`warre/manager.py`)

The most complex business logic. `flavor_free_slots()` computes available time windows for a flavor:

1. Collects all active reservations and maintenance windows as (timestamp, "start"/"end") tuples
2. Sorts and iterates to track current slot usage over time
3. Identifies segments where `usage < flavor.slots` with sufficient contiguous duration
4. Returns a list of `(start, end)` windows where a reservation could fit

Tests for this algorithm are extensive — see `warre/tests/unit/test_manager.py`.

## Quota Model

Quotas count reservations in states `PENDING_CREATE`, `ALLOCATED`, and `ACTIVE` (not `COMPLETE` or `ERROR`). Two resource types are enforced: reservation count and total reserved hours (computed from `start`/`end` on each reservation).

## Testing Patterns

- `TestCase` (`warre/tests/unit/base.py`): Flask test client + in-memory SQLite DB
- `ApiTestCase`: adds a mock Keystone auth context
- Helper factories on the base class: `create_flavor()`, `create_reservation()`, `create_maintenance_window()`, etc.
- Coverage minimum: 90%
