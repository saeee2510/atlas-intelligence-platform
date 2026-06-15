# tests/test_tables.py

from src.db.postgres import engine
from sqlalchemy import inspect

inspector = inspect(engine)

print(inspector.get_table_names())