"""empty message

Revision ID: 783f2ffc432a
Revises: aed58246b474
Create Date: 2018-02-27 17:33:10.343369

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '783f2ffc432a'
down_revision = 'aed58246b474'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('evaluations', 'month',
               existing_type=mysql.VARCHAR(length=16),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('evaluations', 'month',
               existing_type=mysql.VARCHAR(length=16),
               nullable=True)
    # ### end Alembic commands ###
