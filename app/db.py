import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL") or "postgresql://employee_review_db_user:Fu6A89inRV3dVJdFhF3ZdXYkmcBNr3Rl@dpg-d1fdsf7gi27c73cng7ug-a.oregon-postgres.render.com/employee_review_db"


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
