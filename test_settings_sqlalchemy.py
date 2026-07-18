#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from webcms.admin.admin_api import AdminAPI
from webcms.core.response import Response

# Minimal Setting model for testing
Base = declarative_base()
class Setting(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(String(1000))
    type = Column(String(50))

# Setup SQLite in memory
engine = create_engine('sqlite:///:memory:')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()

# Create API with SQLAlchemy session
api = AdminAPI(db=db)

# Mock request
class MockRequest:
    def __init__(self, json_data=None):
        self.json = json_data

# Monkey-patch _is_kosdb to False for SQLAlchemy path
api._is_kosdb = lambda: False

# GET default settings
req = MockRequest()
resp = api.get_settings(req)
print("GET defaults:", resp.body)

# UPDATE site_name
req = MockRequest({"site_name": "My SQL Site", "posts_per_page": "25"})
resp = api.update_settings(req)
print("UPDATE:", resp.body)

# GET persisted settings
req = MockRequest()
resp = api.get_settings(req)
print("GET after update:", resp.body)

# Verify DB rows
rows = db.query(Setting).all()
print("DB rows:", [(r.key, r.value, r.type) for r in rows])

assert resp.body['settings']['site_name'] == 'My SQL Site'
assert resp.body['settings']['posts_per_page'] == 25
print("SQLAlchemy path: OK")
