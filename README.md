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

## Quotas

There are 2 quotas you can set on a project
1. reservation - Total number of reservations in any state a project can have.
2. hours - Sum of hours for all reservations a project can have.

### Setting up quotas

Warre uses oslo-limit for quotas.

On new installs you need to first register the 2 limits and set defaults
See: `openstack registered limit create`

To set quota for a specific project see `openstack limit create`

## Client

See https://github.com/NeCTAR-RC/python-warreclient

## Components

### warre-api

Flask restful API server

### warre-worker

Handles async tasks, currently this is only creating leases in blazar.

### warre-notification
Handles notifications from blazar and updates warre reservations accordingly.
Notification will change the state of a reservations:
 `lease.event.start_lease` -> ACTIVE
 `lease.event.end_lease` -> COMPLETE
