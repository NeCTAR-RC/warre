"""add status

Revision ID: 17a247d2d32e
Revises: 147fc7ff582d
Create Date: 2021-03-04 14:43:02.239439

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17a247d2d32e'
down_revision = '147fc7ff582d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reservation', sa.Column('status', sa.String(length=16), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('reservation', 'status')
    # ### end Alembic commands ###
