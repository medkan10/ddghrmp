from sqlalchemy import create_engine

# SQLite DB connection
engine = create_engine('sqlite:///db/app_data.db')

def get_engine():
    return engine
