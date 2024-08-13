"""initial migration1

Revision ID: e9253b39fc7c
Revises: b76650ae3ec2
Create Date: 2024-08-13 17:53:59.678843

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9253b39fc7c'
down_revision: Union[str, None] = 'b76650ae3ec2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
