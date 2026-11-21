from sqlalchemy.exc import SQLAlchemyError

from database import engine

try:
    with engine.connect() as connection:
        print("PostgreSQL connected successfully!")

except SQLAlchemyError as e:
    print("Connection failed:", e)
