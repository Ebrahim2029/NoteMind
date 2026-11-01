from sqlalchemy import create_engine, text
from app_config import app_settings


def cleanup_database():
    engine = create_engine(
        f"postgresql://{app_settings.POSTGRES_USER}:{app_settings.POSTGRES_PASSWORD}@"
        f"{app_settings.POSTGRES_HOST}:{app_settings.POSTGRES_PORT}/{app_settings.POSTGRES_DB}"
    )
    with engine.connect() as conn:
        # احذف البيانات بالترتيب الصحيح بسبب القيود (FK)
        conn.execute(text("TRUNCATE TABLE notes CASCADE"))
        conn.execute(text("TRUNCATE TABLE notebooks CASCADE"))
        conn.execute(text("TRUNCATE TABLE users CASCADE"))
        conn.commit()
        print("Database cleanup completed.")

    

cleanup_database()