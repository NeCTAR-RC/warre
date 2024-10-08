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

"""Add extra-specs to reservation

Revision ID: f08f1d5a7dfa
Revises: 6821e37ce4e2
Create Date: 2021-04-07 17:57:30.003513

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f08f1d5a7dfa"
down_revision = "6821e37ce4e2"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("flavor", sa.Column("extra_specs", sa.JSON(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("flavor", "extra_specs")
    # ### end Alembic commands ###
