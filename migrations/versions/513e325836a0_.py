"""empty message

Revision ID: 513e325836a0
Revises: 78eae4ca4b2f
Create Date: 2020-11-05 18:42:31.796350

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '513e325836a0'
down_revision = '78eae4ca4b2f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('history_salary_db')
    op.drop_table('history_accounts_db')
    op.drop_table('history_expenses_db')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('history_expenses_db',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('to_pay', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('date', sa.DATE(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='history_expenses_db_pkey')
    )
    op.create_table('history_accounts_db',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(length=128), autoincrement=False, nullable=True),
    sa.Column('to_pay', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('value', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('date', sa.DATE(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='history_accounts_db_pkey')
    )
    op.create_table('history_salary_db',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('userid', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('value', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('date', sa.DATE(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='history_salary_db_pkey')
    )
    # ### end Alembic commands ###
