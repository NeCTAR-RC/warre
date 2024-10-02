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

from oslo_config import cfg
from oslo_policy import policy


CONF = cfg.CONF
_POLICY_PATH = "/etc/warre/policy.yaml"


enforcer = policy.Enforcer(CONF, policy_file=_POLICY_PATH)

ADMIN_OR_OWNER_OR_WRITER = "admin_or_owner_or_writer"
ADMIN_OR_OWNER_OR_READER = "admin_or_owner_or_reader"
ADMIN_OR_READER = "admin_or_reader"
ADMIN_OR_WRITER = "admin_or_writer"
ADMIN_OR_OWNER = "admin_or_owner"


base_rules = [
    policy.RuleDefault(
        name="admin_required", check_str="role:admin or is_admin:1"
    ),
    policy.RuleDefault(
        name="reader",
        check_str="role:reader or role:read_only "
        "or role:cloud_admin or role:helpdesk",
    ),
    policy.RuleDefault(
        name="writer", check_str="role:cloud_admin or role:helpdesk"
    ),
    policy.RuleDefault(name="owner", check_str="project_id:%(project_id)s"),
    policy.RuleDefault(
        name=ADMIN_OR_OWNER, check_str="rule:admin_required or rule:owner"
    ),
    policy.RuleDefault(
        name=ADMIN_OR_OWNER_OR_READER,
        check_str="rule:admin_or_owner or rule:reader",
    ),
    policy.RuleDefault(
        name=ADMIN_OR_OWNER_OR_WRITER,
        check_str="rule:admin_or_owner or rule:writer",
    ),
    policy.RuleDefault(
        name=ADMIN_OR_READER, check_str="rule:admin_required or rule:reader"
    ),
    policy.RuleDefault(
        name=ADMIN_OR_WRITER, check_str="rule:admin_required or rule:writer"
    ),
]

FLAVOR_PREFIX = "warre:flavor:%s"

flavor_rules = [
    policy.DocumentedRuleDefault(
        name=FLAVOR_PREFIX % "get",
        check_str="",
        description="Show flavor details.",
        operations=[
            {"path": "/v1/flavors/{flavor_id}/", "method": "GET"},
            {"path": "/v1/flavors/{flavor_id}/", "method": "HEAD"},
        ],
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR_PREFIX % "list",
        check_str="",
        description="List flavors.",
        operations=[
            {"path": "/v1/flavors/", "method": "GET"},
            {"path": "/v1/flavors/", "method": "HEAD"},
        ],
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR_PREFIX % "create",
        check_str=f"rule:{ADMIN_OR_WRITER}",
        description="Create flavor.",
        operations=[{"path": "/v1/flavors/", "method": "POST"}],
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR_PREFIX % "list:all",
        check_str=f"rule:{ADMIN_OR_READER}",
        description="List all flavors.",
        operations=[{"path": "/v1/flavors/", "method": "GET"}],
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR_PREFIX % "update",
        check_str=f"rule:{ADMIN_OR_OWNER}",
        description="Update a flavor",
        operations=[{"path": "/v1/flavors/{flavor_id}/", "method": "PATCH"}],
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR_PREFIX % "delete",
        check_str=f"rule:{ADMIN_OR_WRITER}",
        description="Delete flavor.",
        operations=[{"path": "/v1/flavors/{flavor_id}/", "method": "DELETE"}],
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR_PREFIX % "get_restricted_fields",
        check_str=f"rule:{ADMIN_OR_READER}",
        description="View restricted flavor fields",
        operations=[
            {"path": "/v1/flavors/{flavor_id}/", "method": "GET"},
            {"path": "/v1/flavors/", "method": "GET"},
        ],
    ),
    policy.DocumentedRuleDefault(
        name=FLAVOR_PREFIX % "update_restricted_fields",
        check_str=f"rule:{ADMIN_OR_WRITER}",
        description="Update restricted flavor fields",
        operations=[{"path": "/v1/flavors/{flavor_id}/", "method": "PATCH"}],
    ),
]

FLAVORPROJECT_PREFIX = "warre:flavorproject:%s"

flavorproject_rules = [
    policy.DocumentedRuleDefault(
        name=FLAVORPROJECT_PREFIX % "get",
        check_str=f"rule:{ADMIN_OR_READER}",
        description="Show flavorproject details.",
        operations=[
            {"path": "/v1/flavorprojects/{flavor_id}/", "method": "GET"},
            {"path": "/v1/flavorprojects/{flavor_id}/", "method": "HEAD"},
        ],
    ),
    policy.DocumentedRuleDefault(
        name=FLAVORPROJECT_PREFIX % "list",
        check_str=f"rule:{ADMIN_OR_READER}",
        description="List flavorprojects.",
        operations=[
            {"path": "/v1/flavorprojects/", "method": "GET"},
            {"path": "/v1/flavorprojects/", "method": "HEAD"},
        ],
    ),
    policy.DocumentedRuleDefault(
        name=FLAVORPROJECT_PREFIX % "create",
        check_str=f"rule:{ADMIN_OR_WRITER}",
        description="Create flavorproject.",
        operations=[{"path": "/v1/flavorprojects/", "method": "POST"}],
    ),
    policy.DocumentedRuleDefault(
        name=FLAVORPROJECT_PREFIX % "delete",
        check_str=f"rule:{ADMIN_OR_WRITER}",
        description="Delete flavorproject.",
        operations=[
            {"path": "/v1/flavorprojects/{flavor_id}/", "method": "DELETE"}
        ],
    ),
]

limits_rules = [
    policy.DocumentedRuleDefault(
        name="warre:limits:list:all",
        check_str=f"rule:{ADMIN_OR_READER}",
        description="List limits for any project",
        operations=[{"path": "/v1/limits/", "method": "GET"}],
    ),
]

RESERVATION_PREFIX = "warre:reservation:%s"

reservation_rules = [
    policy.DocumentedRuleDefault(
        name=RESERVATION_PREFIX % "get",
        check_str=f"rule:{ADMIN_OR_OWNER_OR_READER}",
        description="Show reservation details.",
        operations=[
            {"path": "/v1/reservations/{reservation_id}/", "method": "GET"},
            {"path": "/v1/reservations/{reservation_id}/", "method": "HEAD"},
        ],
    ),
    policy.DocumentedRuleDefault(
        name=RESERVATION_PREFIX % "list",
        check_str="",
        description="List reservations.",
        operations=[
            {"path": "/v1/reservations/", "method": "GET"},
            {"path": "/v1/reservations/", "method": "HEAD"},
        ],
    ),
    policy.DocumentedRuleDefault(
        name=RESERVATION_PREFIX % "list:all",
        check_str=f"rule:{ADMIN_OR_READER}",
        description="List all reservations.",
        operations=[{"path": "/v1/reservations/", "method": "GET"}],
    ),
    policy.DocumentedRuleDefault(
        name=RESERVATION_PREFIX % "update",
        check_str=f"rule:{ADMIN_OR_OWNER}",
        description="Update a reservation",
        operations=[
            {"path": "/v1/reservations/{reservation_id}/", "method": "PATCH"}
        ],
    ),
    policy.DocumentedRuleDefault(
        name=RESERVATION_PREFIX % "delete",
        check_str=f"rule:{ADMIN_OR_OWNER}",
        description="Delete reservation.",
        operations=[
            {"path": "/v1/reservations/{reservation_id}/", "method": "DELETE"}
        ],
    ),
]

enforcer.register_defaults(base_rules)
enforcer.register_defaults(flavor_rules)
enforcer.register_defaults(flavorproject_rules)
enforcer.register_defaults(limits_rules)
enforcer.register_defaults(reservation_rules)


def list_rules():
    return (
        base_rules
        + flavor_rules
        + flavorproject_rules
        + limits_rules
        + reservation_rules
    )
