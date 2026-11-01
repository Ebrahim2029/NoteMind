
import os
from utils.security import create_access_token
from app_config import app_settings

if __name__ == "__main__":
    token = create_access_token(
        user_id=os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000001"),
        username=os.getenv("DEV_USERNAME", "alice"),
        roles=(os.getenv("DEV_ROLES", "user").split(",")),
        secret=app_settings.JWT_SECRET,
        alg=getattr(app_settings, "JWT_ALG", "HS256"),
        expires_minutes=int(os.getenv("DEV_EXP", "120")),
    )
    print(token)
print("Access token created successfully")