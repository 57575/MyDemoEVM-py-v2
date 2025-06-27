# project/config_test.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASE = {"driver": "sqlite", "database": "accounts.db"}

SQLALCHEMY_DATABASE_URI = f"{DATABASE['driver']}:///{BASE_DIR}/{DATABASE['database']}"
SQLALCHEMY_TRACK_MODIFICATIONS = False

MOCK_DATABASE_URI = "sqlite:///:memory:"
