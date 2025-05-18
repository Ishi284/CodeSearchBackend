from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List
from datetime import datetime
from bson import ObjectId

from app.core.config import settings
from app.models.user import User
from app.models.chat import ChatSession, ChatSessionCreate, ChatSessionUpdate, ChatMessageCreate, ChatMessage
from app.core.security import get_current_user
from app.db.mongodb import get_database
from app.services.code_search import code_search_service

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatSession)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new chat session"""
    db = await get_database()
    chat_collection = db[settings.DATABASE_NAME]["chat_sessions"]
    
    new_session = ChatSession(
        _id=ObjectId(),
        user_id=ObjectId(current_user.id),
        title=session_data.title,
        messages=[],
        created_at=settings.get_current_time(),
        updated_at=settings.get_current_time()
    )
    
    result = await chat_collection.insert_one(new_session.dict(by_alias=True))
    
    created_session = await chat_collection.find_one({"_id": result.inserted_id})
    return ChatSession(**created_session)

@router.get("/", response_model=List[ChatSession])
async def get_chat_sessions(current_user: User = Depends(get_current_user)):
    """Get all chat sessions for current user"""
    db = await get_database()
    chat_collection = db[settings.DATABASE_NAME]["chat_sessions"]
    
    cursor = chat_collection.find({"user_id": ObjectId(current_user.id)})
    sessions = await cursor.to_list(length=100)
    
    return [ChatSession(**session) for session in sessions]

@router.get("/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a chat session by ID"""
    db = await get_database()
    chat_collection = db[settings.DATABASE_NAME]["chat_sessions"]
    
    session = await chat_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return ChatSession(**session)

@router.patch("/{session_id}", response_model=ChatSession)
async def update_chat_session(
    session_id: str,
    update_data: ChatSessionUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a chat session"""
    db = await get_database()
    chat_collection = db[settings.DATABASE_NAME]["chat_sessions"]
    
    # Check if session exists and belongs to user
    session = await chat_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Update session
    update_dict = update_data.dict(exclude_unset=True)
    if update_dict:
        update_dict["updated_at"] = settings.get_current_time()
        await chat_collection.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": update_dict}
        )
    
    # Return updated session
    updated_session = await chat_collection.find_one({"_id": ObjectId(session_id)})
    return ChatSession(**updated_session)

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a chat session"""
    db = await get_database()
    chat_collection = db[settings.DATABASE_NAME]["chat_sessions"]
    
    # Check if session exists and belongs to user
    session = await chat_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Delete session
    await chat_collection.delete_one({"_id": ObjectId(session_id)})
    return None

@router.post("/{session_id}/messages", response_model=ChatSession)
async def add_chat_message(
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user)
):
    """Add a message to a chat session and perform code search"""
    db = await get_database()
    chat_collection = db[settings.DATABASE_NAME]["chat_sessions"]
    
    # Check if session exists and belongs to user
    session = await chat_collection.find_one({
        "_id": ObjectId(session_id),
        "user_id": ObjectId(current_user.id)
    })
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Perform code search
    search_results = await code_search_service.search(
        query=message_data.message,
        language=message_data.language,
        top_k=3  # Default to 5 results
    )
    
    # Create new message
    new_message = ChatMessage(
        message=message_data.message,
        language=message_data.language,
        timestamp=settings.get_current_time(),
        results=search_results
    )
    
    # Add message to session
    await chat_collection.update_one(
        {"_id": ObjectId(session_id)},
        {
            "$push": {"messages": new_message.dict()},
            "$set": {"updated_at": settings.get_current_time()}
        }
    )
    
    # Return updated session
    updated_session = await chat_collection.find_one({"_id": ObjectId(session_id)})
    return ChatSession(**updated_session)