"""empty message

Revision ID: 78eae4ca4b2f
Revises: 4b3510a88c5b
Create Date: 2020-11-05 18:40:29.812159

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78eae4ca4b2f'
down_revision = '4b3510a88c5b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('history_db', sa.Column('expenses_name', sa.ARRAY(sa.String()), nullable=True))
    op.add_column('history_db', sa.Column('expenses_value', sa.ARRAY(sa.Integer()), nullable=True))
    op.add_column('history_db', sa.Column('goals_name', sa.ARRAY(sa.String()), nullable=True))
    op.add_column('history_db', sa.Column('goals_to_pay', sa.ARRAY(sa.Integer()), nullable=True))
    op.add_column('history_db', sa.Column('goals_value', sa.ARRAY(sa.Integer()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('history_db', 'goals_value')
    op.drop_column('history_db', 'goals_to_pay')
    op.drop_column('history_db', 'goals_name')
    op.drop_column('history_db', 'expenses_value')
    op.drop_column('history_db', 'expenses_name')
    # ### end Alembic commands ###
