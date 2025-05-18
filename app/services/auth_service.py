from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import UserCreate, UserInDB, User
from app.db.mongodb import get_database
from datetime import datetime
from bson import ObjectId

class AuthService:
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        db = await get_database()
        user_collection = db[settings.DATABASE_NAME]["users"]
        
        # Check if user exists
        existing_user = await user_collection.find_one({
            "$or": [
                {"username": user_data.username},
                {"email": user_data.email}
            ]
        })
        
        if existing_user:
            raise ValueError("Username or email already registered")
        
        # Create user - here we ensure _id is set
        user_dict = {
            "_id": ObjectId(),  # Explicitly create ObjectId
            **user_data.dict(),
            "hashed_password": get_password_hash(user_data.password),
            "created_at": settings.get_current_time()
        }
        
        user_in_db = UserInDB(**user_dict)
        
        # Store with explicit _id
        await user_collection.insert_one(user_in_db.dict(by_alias=True))
        
        # Return user without password
        created_user = await user_collection.find_one({"_id": user_dict["_id"]})
        return User(**created_user)
    
    async def get_user(self, user_id: str) -> User:
        """Get user by ID"""
        db = await get_database()
        user_collection = db[settings.DATABASE_NAME]["users"]
        
        user = await user_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise ValueError("User not found")
        
        return User(**user)
    
    async def update_user(self, user_id: str, update_data: dict) -> User:
        """Update user data"""
        db = await get_database()
        user_collection = db[settings.DATABASE_NAME]["users"]
        
        # If password is provided, hash it
        if "password" in update_data and update_data["password"]:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        # Update user
        await user_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        # Return updated user
        updated_user = await user_collection.find_one({"_id": ObjectId(user_id)})
        return User(**updated_user)

# Create singleton instance
auth_service = AuthService()