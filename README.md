# Warre

Nectar Reservation System, warre is a type of beehive.

## Overview

Warre is a standalone project that supports reservations in the Nectar Cloud.
It uses Blazar for the actual reservations within openstack but provides some enhancements.
Ideally these will be merged into Blazar at a later time but for speed of development warre was born.

## Warre Concepts

### Flavors

A flavor in warre is much like a flavor in nova, an operator can define a flavor that is in turn used
by blazar to create a nova flavor. A warre flavor has some additional attributes:
 * properties - Blazar host properties
 * max_length_hours - Max length of a single reservation in hours
 * slots - Total available slots available for this flavor.
 * start / end - Optional window during which the flavor can be reserved.

#### Permissions

A flavor can be public or private. A project can be granted access to a private flavor.

### Reservations

A reservation maps directly to a lease in blazar. It mainly exists so we can do things
like quotas etc.

#### Reservation States

 * PENDING_CREATE - Reservation is pending creation in blazar
 * ALLOCATED - Reservation has been successfully created in blazar
 * ACTIVE - Reservation is active
 * COMPLETE - Reservation is finished
 * ERROR - Reservation failed to create in blazar

### Maintenance Windows

A maintenance window is a period of time, with an optional note, during which
one or more flavors cannot be reserved. A window applies only to the flavors
linked to it through `flavor_ids`. For its whole duration it occupies every
slot of each linked flavor.

Maintenance windows interact with reservations as follows:
 * Creating a reservation that overlaps a maintenance window for its flavor
   fails with `Reservation conflicts with a maintenance window`.
 * Free slot calculations, including the capacity check when a reservation
   is created or extended, treat the window as fully booked.
 * Creating or updating a maintenance window fails with HTTP 409 if it
   overlaps a reservation in the PENDING_CREATE, ALLOCATED or ACTIVE state
   on any of its flavors.
 * Callers that pass the `warre:reservation:create:bypass_maintenance`
   policy (admin only by default) can create reservations that overlap a
   maintenance window. This is intended for testing during maintenance.

A window must end after it starts and cannot start in the past. Times use
the format `YYYY-MM-DDTHH:MM:SS+00:00`, for example
`2026-11-01T09:00:00+00:00`. The warre-worker deletes maintenance
windows once they have ended.

Endpoints:
 * `GET /v1/maintenancewindows/` - List maintenance windows, ordered by start
 * `POST /v1/maintenancewindows/` - Create a window with `start`, `end`,
   optional `note` and optional `flavor_ids`
 * `GET /v1/maintenancewindows/<id>/` - Show a window
 * `PATCH /v1/maintenancewindows/<id>/` - Update a window. Passing
   `flavor_ids` replaces the linked flavors, and an empty list removes them all.
 * `DELETE /v1/maintenancewindows/<id>/` - Delete a window

### Free Slots

`GET /v1/flavors/<id>/freeslots/` returns the time windows in which a flavor
has at least one free slot. Clients use it to find when a reservation of a
given length fits: pick a returned window that is at least as long as the
reservation you want.

Query parameters:
 * `start` - Start of the search period as a date (`YYYY-MM-DD`). Defaults to now.
 * `end` - End of the search period as a date (`YYYY-MM-DD`). Defaults to
   365 days from now.

The response is a list of objects with `start` and `end` keys. The
calculation counts reservations in the PENDING_CREATE, ALLOCATED and ACTIVE
states and any maintenance windows for the flavor. It also limits the
search period to the flavor's own `start` and `end`, if set. An inactive
flavor, or one whose `end` has passed, returns an empty list.

## API Summary

| Endpoint | Methods |
| --- | --- |
| `/v1/flavors/` | GET, POST |
| `/v1/flavors/<id>/` | GET, PATCH, DELETE |
| `/v1/flavors/<id>/freeslots/` | GET |
| `/v1/flavorprojects/` | GET, POST |
| `/v1/flavorprojects/<id>/` | DELETE |
| `/v1/maintenancewindows/` | GET, POST |
| `/v1/maintenancewindows/<id>/` | GET, PATCH, DELETE |
| `/v1/reservations/` | GET, POST |
| `/v1/reservations/<id>/` | GET, PATCH, DELETE |
| `/v1/limits/` | GET |

List endpoints accept a `limit` query parameter and return `results`,
`total` and, when there are more pages, a `next` link. `PATCH` on a
reservation extends its end time.

## Quotas

There are 2 quotas you can set on a project
1. reservation - Total number of reservations a project can have in the
   PENDING_CREATE, ALLOCATED or ACTIVE state.
2. hours - Sum of hours for those reservations, multiplied by each
   reservation's instance count.

### Setting up quotas

Warre uses oslo-limit for quotas.

On new installs you need to first register the 2 limits and set defaults
See: `openstack registered limit create`

To set quota for a specific project see `openstack limit create`

## Policy and Scopes

Warre uses oslo.policy for authorisation. Every rule declares
`scope_types`, and `[oslo_policy] enforce_scope` and `enforce_new_defaults`
default to `True`. Domain-scoped tokens are rejected.

All rules accept both system and project scope except
`warre:reservation:create` and `warre:reservation:create:bypass_maintenance`,
which accept project scope only. Tokens without a project (for example
system-scoped tokens) cannot create reservations and must pass `project_id`
to `/v1/limits/`.

The default base rules are:
 * `admin_required` - `role:admin or is_admin:1`
 * `reader` - the `read_only`, `cloud_admin` or `helpdesk` role, or the
   `reader` role on a system-scoped token (`system_reader`)
 * `writer` - the `cloud_admin` or `helpdesk` role
 * `owner` - the token's project matches the resource's project

Most rules combine these. For example, creating, updating and deleting
flavors, flavor projects and maintenance windows requires `admin_or_writer`,
and `all_projects` listings require `admin_or_reader`. Creating a
reservation requires the `member` role.

To generate a sample policy file listing every rule and its default, run:

    tox -e genpolicy

This writes `etc/warre/policy.yaml.sample`.

## Configuration

Warre reads its configuration from `/etc/warre/warre.conf` by default. The
main groups and options an operator needs are:
 * `[DEFAULT]` - `auth_strategy` (`keystone` by default, or `noauth` or
   `testing`), `transport_url` for oslo.messaging, and logging options
 * `[database]` - `connection` (SQLAlchemy URL) and `connection_recycle_time`
 * `[keystone_authtoken]` - keystonemiddleware settings used by warre-api
   when `auth_strategy` is `keystone`
 * `[service_auth]` - Keystone credentials warre uses for its own calls to
   Keystone, Blazar and other services
 * `[blazar]` - `interface`, the endpoint interface used to reach Blazar
   (default `public`)
 * `[warre]` - `bot_auth_url`, `bot_user_id`, `bot_role_id` and
   `bot_password` for the bot account the worker uses to create leases in
   the reservation's project, and `user_notifier` (`taynac` by default, or
   `logging`)
 * `[worker]` - `workers` (default 1) and `periodic_task_interval` in
   seconds (default 1800)
 * `[flask]` - `secret_key`, `host` (default `0.0.0.0`) and `port`
   (default 5000) for warre-api
 * `[sentry]` - `dsn` and `environment`. Error reporting is disabled if `dsn`
   is not set.
 * `[oslo_policy]` - policy enforcement settings, see Policy and Scopes

To generate a sample configuration file with every option, run:

    tox -e genconfig

This writes `etc/warre/warre.conf.sample`.

## Client

See https://github.com/NeCTAR-RC/python-warreclient

## Components

### warre-api

Flask restful API server

### warre-worker

Handles async tasks: creating leases in blazar. It also runs periodic tasks
that delete COMPLETE reservations more than 7 days after they end, delete
finished maintenance windows and send exists notifications for ACTIVE
reservations.

### warre-notification
Handles notifications from blazar and updates warre reservations accordingly.
Notification will change the state of a reservations:
 `lease.event.start_lease` -> ACTIVE
 `lease.event.end_lease` -> COMPLETE

It also handles `lease.event.before_end_lease`, which does not change the
reservation state. For all three events warre sends the user a message
through the configured user notifier driver. The driver is pluggable through
the `warre.user.notifier` entry point:
 * `taynac` - Sends the message to the user's email address through Taynac
   (default)
 * `logging` - Writes the message to the log
