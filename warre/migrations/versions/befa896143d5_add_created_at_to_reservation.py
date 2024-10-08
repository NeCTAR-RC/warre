#
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

"""add created_at to reservation

Revision ID: befa896143d5
Revises: 26497add4de7
Create Date: 2022-07-22 13:29:43.853104

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "befa896143d5"
down_revision = "26497add4de7"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "reservation", sa.Column("created_at", sa.DateTime(), nullable=True)
    )
    op.execute("UPDATE reservation SET created_at = '1970-01-01'")
    op.alter_column(
        "reservation",
        "created_at",
        nullable=False,
        existing_type=sa.DateTime(),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("reservation", "created_at")
    # ### end Alembic commands ###
