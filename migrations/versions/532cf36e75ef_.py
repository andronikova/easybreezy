"""empty message

Revision ID: 532cf36e75ef
Revises: 1b613ed64fed
Create Date: 2020-10-21 19:38:15.014848

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '532cf36e75ef'
down_revision = '1b613ed64fed'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_db',
    sa.Column('userid', sa.Integer(), nullable=False),
    sa.Column('email', sa.String(length=64), nullable=True),
    sa.Column('hash', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('userid')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_db')
    # ### end Alembic commands ###
