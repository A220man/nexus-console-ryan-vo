#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from alembic.config import Config
from alembic import command

alembic_cfg = Config("alembic.ini")
alembic_cfg.set_main_option("sqlalchemy.url", "sqlite:///dev.db")
command.revision(alembic_cfg, autogenerate=True, message="Initial migration for core domain models")
