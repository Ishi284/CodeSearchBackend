from dotenv import load_dotenv
import os
import pytz
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME: str = "Code Search API"
    PROJECT_VERSION: str = "1.0.0"
    
    # MongoDB Settings
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "code_search_db")
    
    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "my-secret-key-for-jwt")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # Model Paths
    MODEL_DIR: str = os.getenv("MODEL_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/embeddings"))
    SUPPORTED_LANGUAGES: list = ["go", "java", "javascript", "php", "python", "ruby"]
    
    # Default search settings
    DEFAULT_TOP_K: int = 3
    MAX_TOP_K: int = 20

    # Thêm cấu hình múi giờ
    TIMEZONE = "Asia/Ho_Chi_Minh"
    
    # Hàm tiện ích để lấy thời gian hiện tại theo múi giờ cấu hình
    @staticmethod
    def get_current_time():
        tz = pytz.timezone(Settings.TIMEZONE)
        return datetime.now(tz)

settings = Settings()