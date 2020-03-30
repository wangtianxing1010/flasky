"""empty message

Revision ID: d8daca02cb94
Revises: 561947d1bc50
Create Date: 2018-08-21 21:45:43.815428

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8daca02cb94'
down_revision = '561947d1bc50'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('photos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('filename', sa.String(length=64), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('photos', schema=None) as batch_op:
        batch_op.drop_column('filename')

    # ### end Alembic commands ###