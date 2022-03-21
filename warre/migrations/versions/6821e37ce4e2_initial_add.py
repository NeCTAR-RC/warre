"""Initial Add

Revision ID: 6821e37ce4e2
Revises: 
Create Date: 2021-03-22 15:46:13.620042

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6821e37ce4e2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('flavor',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('description', sa.String(length=255), nullable=True),
    sa.Column('vcpu', sa.Integer(), nullable=False),
    sa.Column('memory_mb', sa.Integer(), nullable=False),
    sa.Column('disk_gb', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('properties', sa.String(length=255), nullable=True),
    sa.Column('max_length_hours', sa.Integer(), nullable=False),
    sa.Column('slots', sa.Integer(), nullable=False),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('flavor_project',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.String(length=64), nullable=False),
    sa.Column('flavor_id', sa.String(length=64), nullable=False),
    sa.ForeignKeyConstraint(['flavor_id'], ['flavor.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('project_id', 'flavor_id')
    )
    op.create_table('reservation',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('project_id', sa.String(length=64), nullable=False),
    sa.Column('flavor_id', sa.String(length=64), nullable=False),
    sa.Column('lease_id', sa.String(length=64), nullable=True),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('start', sa.DateTime(), nullable=False),
    sa.Column('end', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['flavor_id'], ['flavor.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('reservation')
    op.drop_table('flavor_project')
    op.drop_table('flavor')
    # ### end Alembic commands ###