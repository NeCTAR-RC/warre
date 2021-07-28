"""add error reason to reservation

Revision ID: 732414abd491
Revises: 40707202a51b
Create Date: 2021-07-28 16:21:17.471945

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '732414abd491'
down_revision = '40707202a51b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('reservation', sa.Column('error_reason', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('reservation', 'error_reason')
    # ### end Alembic commands ###
