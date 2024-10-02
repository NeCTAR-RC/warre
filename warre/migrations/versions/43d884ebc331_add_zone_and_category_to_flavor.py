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

"""Add zone and category to flavor

Revision ID: 43d884ebc331
Revises: b4a78f028f92
Create Date: 2022-05-27 13:27:04.210655

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "43d884ebc331"
down_revision = "b4a78f028f92"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "flavor", sa.Column("category", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "flavor",
        sa.Column("availability_zone", sa.String(length=64), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("flavor", "availability_zone")
    op.drop_column("flavor", "category")
    # ### end Alembic commands ###
