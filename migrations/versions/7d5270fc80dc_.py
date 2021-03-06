"""empty message

Revision ID: 7d5270fc80dc
Revises: 2474dfde2124
Create Date: 2020-10-27 16:26:28.835451

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d5270fc80dc'
down_revision = '2474dfde2124'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_db', sa.Column('reserve_account', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user_db', 'reserve_account')
    # ### end Alembic commands ###
