"""empty message

Revision ID: 31624a3df7c3
Revises: 440b3339ae7d
Create Date: 2020-10-28 18:15:37.771208

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31624a3df7c3'
down_revision = '440b3339ae7d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('history_accounts_db',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('userid', sa.Integer(), nullable=True),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('to_pay', sa.Integer(), nullable=True),
    sa.Column('value', sa.Integer(), nullable=True),
    sa.Column('date', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_column('history_expenses_db', 'value')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('history_expenses_db', sa.Column('value', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_table('history_accounts_db')
    # ### end Alembic commands ###
