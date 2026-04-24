# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Add maintenance window

Revision ID: a1b2c3d4e5f6
Revises: 2de2c31ac6e2
Create Date: 2026-04-24 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "2de2c31ac6e2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "maintenance_window",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("start", sa.DateTime(), nullable=False),
        sa.Column("end", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "maintenance_window_flavor",
        sa.Column(
            "maintenance_window_id", sa.String(length=64), nullable=False
        ),
        sa.Column("flavor_id", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["maintenance_window_id"], ["maintenance_window.id"]
        ),
        sa.ForeignKeyConstraint(
            ["flavor_id"], ["flavor.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("maintenance_window_id", "flavor_id"),
    )


def downgrade():
    op.drop_table("maintenance_window_flavor")
    op.drop_table("maintenance_window")
