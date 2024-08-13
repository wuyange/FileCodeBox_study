"""initial migration1

Revision ID: b76650ae3ec2
Revises: 8beca80b5dbe
Create Date: 2024-08-13 17:36:16.180728

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b76650ae3ec2'
down_revision: Union[str, None] = '8beca80b5dbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
