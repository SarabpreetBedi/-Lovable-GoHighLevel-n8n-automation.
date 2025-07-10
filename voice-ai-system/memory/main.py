from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import json
import logging
from datetime import datetime, timedelta
import redis
from loguru import logger

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title="Voice AI Memory System",
    description="Conversation memory and user preferences management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Redis client
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

# Configuration
MEMORY_TTL = int(os.getenv("MEMORY_TTL", 86400))  # 24 hours
MAX_MEMORY_SIZE = int(os.getenv("MAX_MEMORY_SIZE", 1000))
MEMORY_CLEANUP_INTERVAL = int(os.getenv("MEMORY_CLEANUP_INTERVAL", 3600))  # 1 hour

# Pydantic models
class ConversationEntry(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class UserPreferences(BaseModel):
    language: Optional[str] = "en"
    voice_speed: Optional[float] = 1.0
    voice_model: Optional[str] = "alloy"
    interruption_threshold: Optional[float] = 0.5
    max_conversation_length: Optional[int] = 50
    preferred_topics: Optional[List[str]] = None
    custom_settings: Optional[Dict[str, Any]] = None

class MemoryData(BaseModel):
    user_id: str
    conversation_history: List[ConversationEntry]
    preferences: UserPreferences
    last_interaction: str
    session_count: int = 0
    total_interactions: int = 0
    created_at: str
    updated_at: str

class MemoryUpdateRequest(BaseModel):
    conversation_history: Optional[List[ConversationEntry]] = None
    preferences: Optional[UserPreferences] = None
    metadata: Optional[Dict[str, Any]] = None

class MemoryResponse(BaseModel):
    user_id: str
    conversation_history: List[ConversationEntry]
    preferences: UserPreferences
    last_interaction: str
    session_count: int
    total_interactions: int
    memory_size: int
    ttl_remaining: int

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    redis_status: str
    memory_stats: Dict[str, Any]

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    # Get memory statistics
    try:
        memory_stats = {
            "total_keys": len(redis_client.keys("user_memory:*")),
            "memory_usage": redis_client.info()["used_memory_human"],
            "ttl_default": MEMORY_TTL
        }
    except Exception as e:
        memory_stats = {"error": str(e)}
    
    return HealthResponse(
        status="healthy" if redis_status == "healthy" else "unhealthy",
        timestamp=datetime.now().isoformat(),
        redis_status=redis_status,
        memory_stats=memory_stats
    )

# Get user memory
@app.get("/memory/{user_id}", response_model=MemoryResponse)
async def get_user_memory(user_id: str):
    """Get memory data for a specific user"""
    try:
        # Get memory from Redis
        memory_data = redis_client.get(f"user_memory:{user_id}")
        
        if not memory_data:
            # Create new memory for user
            default_preferences = UserPreferences()
            memory = MemoryData(
                user_id=user_id,
                conversation_history=[],
                preferences=default_preferences,
                last_interaction=datetime.now().isoformat(),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        else:
            memory = MemoryData(**json.loads(memory_data))
        
        # Calculate memory size and TTL
        memory_size = len(json.dumps(memory.dict()))
        ttl_remaining = redis_client.ttl(f"user_memory:{user_id}")
        
        return MemoryResponse(
            user_id=memory.user_id,
            conversation_history=memory.conversation_history,
            preferences=memory.preferences,
            last_interaction=memory.last_interaction,
            session_count=memory.session_count,
            total_interactions=memory.total_interactions,
            memory_size=memory_size,
            ttl_remaining=ttl_remaining
        )
        
    except Exception as e:
        logger.error(f"Error getting user memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user memory: {str(e)}")

# Update user memory
@app.post("/memory/{user_id}")
async def update_user_memory(user_id: str, request: MemoryUpdateRequest):
    """Update memory data for a specific user"""
    try:
        # Get existing memory or create new
        memory_data = redis_client.get(f"user_memory:{user_id}")
        
        if memory_data:
            memory = MemoryData(**json.loads(memory_data))
        else:
            # Create new memory
            memory = MemoryData(
                user_id=user_id,
                conversation_history=[],
                preferences=UserPreferences(),
                last_interaction=datetime.now().isoformat(),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        
        # Update conversation history
        if request.conversation_history:
            # Add new entries
            for entry in request.conversation_history:
                if not entry.timestamp:
                    entry.timestamp = datetime.now().isoformat()
                memory.conversation_history.append(entry)
            
            # Limit conversation history length
            max_length = memory.preferences.max_conversation_length or 50
            if len(memory.conversation_history) > max_length:
                memory.conversation_history = memory.conversation_history[-max_length:]
        
        # Update preferences
        if request.preferences:
            # Merge preferences
            current_prefs = memory.preferences.dict()
            new_prefs = request.preferences.dict(exclude_unset=True)
            current_prefs.update(new_prefs)
            memory.preferences = UserPreferences(**current_prefs)
        
        # Update metadata
        if request.metadata:
            # Store metadata separately
            redis_client.setex(
                f"user_metadata:{user_id}",
                MEMORY_TTL,
                json.dumps(request.metadata)
            )
        
        # Update timestamps and counters
        memory.last_interaction = datetime.now().isoformat()
        memory.updated_at = datetime.now().isoformat()
        memory.total_interactions += 1
        
        # Store in Redis
        redis_client.setex(
            f"user_memory:{user_id}",
            MEMORY_TTL,
            json.dumps(memory.dict())
        )
        
        return {
            "status": "success",
            "user_id": user_id,
            "memory_size": len(json.dumps(memory.dict())),
            "conversation_length": len(memory.conversation_history),
            "total_interactions": memory.total_interactions
        }
        
    except Exception as e:
        logger.error(f"Error updating user memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user memory: {str(e)}")

# Clear user memory
@app.delete("/memory/{user_id}")
async def clear_user_memory(user_id: str):
    """Clear memory data for a specific user"""
    try:
        # Delete memory and metadata
        redis_client.delete(f"user_memory:{user_id}")
        redis_client.delete(f"user_metadata:{user_id}")
        
        return {
            "status": "success",
            "message": f"Memory cleared for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error clearing user memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear user memory: {str(e)}")

# Get conversation summary
@app.get("/memory/{user_id}/summary")
async def get_conversation_summary(user_id: str):
    """Get a summary of the user's conversation history"""
    try:
        memory_data = redis_client.get(f"user_memory:{user_id}")
        
        if not memory_data:
            raise HTTPException(status_code=404, detail="User memory not found")
        
        memory = MemoryData(**json.loads(memory_data))
        
        # Create summary
        summary = {
            "user_id": user_id,
            "total_messages": len(memory.conversation_history),
            "user_messages": len([m for m in memory.conversation_history if m.role == "user"]),
            "assistant_messages": len([m for m in memory.conversation_history if m.role == "assistant"]),
            "session_count": memory.session_count,
            "total_interactions": memory.total_interactions,
            "last_interaction": memory.last_interaction,
            "preferences": memory.preferences.dict(),
            "recent_messages": memory.conversation_history[-10:] if memory.conversation_history else []
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get conversation summary: {str(e)}")

# Update conversation summary
@app.post("/memory/{user_id}/summary")
async def update_conversation_summary(user_id: str, summary_data: Dict[str, Any]):
    """Update conversation summary for a user"""
    try:
        # Store summary separately
        redis_client.setex(
            f"user_summary:{user_id}",
            MEMORY_TTL,
            json.dumps(summary_data)
        )
        
        return {
            "status": "success",
            "message": f"Summary updated for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error updating conversation summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update conversation summary: {str(e)}")

# Get user preferences
@app.get("/memory/{user_id}/preferences")
async def get_user_preferences(user_id: str):
    """Get user preferences"""
    try:
        memory_data = redis_client.get(f"user_memory:{user_id}")
        
        if not memory_data:
            # Return default preferences
            return UserPreferences()
        
        memory = MemoryData(**json.loads(memory_data))
        return memory.preferences
        
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user preferences: {str(e)}")

# Update user preferences
@app.put("/memory/{user_id}/preferences")
async def update_user_preferences(user_id: str, preferences: UserPreferences):
    """Update user preferences"""
    try:
        memory_data = redis_client.get(f"user_memory:{user_id}")
        
        if memory_data:
            memory = MemoryData(**json.loads(memory_data))
            memory.preferences = preferences
            memory.updated_at = datetime.now().isoformat()
            
            redis_client.setex(
                f"user_memory:{user_id}",
                MEMORY_TTL,
                json.dumps(memory.dict())
            )
        else:
            # Create new memory with preferences
            memory = MemoryData(
                user_id=user_id,
                conversation_history=[],
                preferences=preferences,
                last_interaction=datetime.now().isoformat(),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            
            redis_client.setex(
                f"user_memory:{user_id}",
                MEMORY_TTL,
                json.dumps(memory.dict())
            )
        
        return {
            "status": "success",
            "message": f"Preferences updated for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user preferences: {str(e)}")

# Memory cleanup endpoint
@app.post("/memory/cleanup")
async def cleanup_old_memories():
    """Clean up old memory entries"""
    try:
        # Get all memory keys
        memory_keys = redis_client.keys("user_memory:*")
        deleted_count = 0
        
        for key in memory_keys:
            # Check TTL
            ttl = redis_client.ttl(key)
            if ttl == -1:  # No TTL set
                # Set TTL for old entries
                redis_client.expire(key, MEMORY_TTL)
            elif ttl == -2:  # Key doesn't exist
                deleted_count += 1
        
        return {
            "status": "success",
            "message": f"Memory cleanup completed. {deleted_count} expired entries removed."
        }
        
    except Exception as e:
        logger.error(f"Error during memory cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Memory cleanup failed: {str(e)}")

# Get memory statistics
@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory system statistics"""
    try:
        memory_keys = redis_client.keys("user_memory:*")
        metadata_keys = redis_client.keys("user_metadata:*")
        summary_keys = redis_client.keys("user_summary:*")
        
        stats = {
            "total_users": len(memory_keys),
            "users_with_metadata": len(metadata_keys),
            "users_with_summaries": len(summary_keys),
            "memory_usage": redis_client.info()["used_memory_human"],
            "ttl_default": MEMORY_TTL,
            "max_memory_size": MAX_MEMORY_SIZE
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 