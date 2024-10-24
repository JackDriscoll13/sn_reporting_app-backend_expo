# Database Models
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

# Local AWS Credential Objects (Used for validation)
from models.custom_types import AWSDatabaseCredentials


def connect_db(rds_connection: AWSDatabaseCredentials):
    """Returns a database session object."""
    
    DATABASE_URL = f"postgresql://{rds_connection.db_user}:{rds_connection.db_password}@{rds_connection.db_host}:{rds_connection.db_port}/{rds_connection.db_name}"
    print(DATABASE_URL)
    engine = create_engine(DATABASE_URL)

    # Test connection (this is slow so maybe we should remove it later): 
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print('Database connection successful')
            else: 
                print('Database connection failed')
    except Exception as e:
        print(f"Error during connection test: {e}")
        raise

    # Create a session and return it. 
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


