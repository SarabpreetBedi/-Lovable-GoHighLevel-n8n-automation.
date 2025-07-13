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
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI app
app = FastAPI(
    title="Voice AI Professional Memory System",
    description="Advanced conversation memory and user preferences management with timezone support",
    version="2.0.0"
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
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "America/New_York")

# Pydantic models
class ConversationEntry(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None
    confidence: Optional[float] = None
    sentiment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class UserPreferences(BaseModel):
    language: Optional[str] = "en"
    voice_speed: Optional[float] = 1.0
    voice_model: Optional[str] = "alloy"
    interruption_threshold: Optional[float] = 0.5
    max_conversation_length: Optional[int] = 50
    preferred_topics: Optional[List[str]] = None
    timezone: Optional[str] = DEFAULT_TIMEZONE
    email_preferences: Optional[Dict[str, Any]] = None
    callback_preferences: Optional[Dict[str, Any]] = None
    custom_settings: Optional[Dict[str, Any]] = None

class CallbackRequest(BaseModel):
    user_id: str
    callback_type: str  # "email", "sms", "call"
    scheduled_time: str
    timezone: str
    message: Optional[str] = None
    priority: Optional[str] = "normal"

class EmailTemplate(BaseModel):
    template_id: str
    subject: str
    body: str
    variables: Optional[Dict[str, str]] = None

class MemoryData(BaseModel):
    user_id: str
    conversation_history: List[ConversationEntry]
    preferences: UserPreferences
    last_interaction: str
    session_count: int = 0
    total_interactions: int = 0
    created_at: str
    updated_at: str
    callbacks: Optional[List[Dict[str, Any]]] = None
    email_history: Optional[List[Dict[str, Any]]] = None

class MemoryUpdateRequest(BaseModel):
    conversation_history: Optional[List[ConversationEntry]] = None
    preferences: Optional[UserPreferences] = None
    metadata: Optional[Dict[str, Any]] = None
    callback_data: Optional[CallbackRequest] = None
    email_data: Optional[Dict[str, Any]] = None

class MemoryResponse(BaseModel):
    user_id: str
    conversation_history: List[ConversationEntry]
    preferences: UserPreferences
    last_interaction: str
    session_count: int
    total_interactions: int
    memory_size: int
    ttl_remaining: int
    timezone_info: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    redis_status: str
    memory_stats: Dict[str, Any]
    timezone_support: bool

# Timezone utility functions
def get_user_timezone(user_id: str) -> str:
    """Get user's timezone from memory or return default"""
    try:
        memory_data = redis_client.get(f"user_memory:{user_id}")
        if memory_data:
            memory = MemoryData(**json.loads(memory_data))
            return memory.preferences.timezone or DEFAULT_TIMEZONE
        return DEFAULT_TIMEZONE
    except Exception:
        return DEFAULT_TIMEZONE

def convert_to_user_timezone(timestamp: str, user_id: str) -> str:
    """Convert timestamp to user's timezone"""
    try:
        user_tz = pytz.timezone(get_user_timezone(user_id))
        utc_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        local_time = utc_time.astimezone(user_tz)
        return local_time.isoformat()
    except Exception as e:
        logger.error(f"Timezone conversion error: {e}")
        return timestamp

def schedule_callback(callback_data: CallbackRequest) -> Dict[str, Any]:
    """Schedule a callback for the user"""
    try:
        # Store callback in Redis with TTL
        callback_key = f"user_callback:{callback_data.user_id}:{callback_data.scheduled_time}"
        callback_info = {
            "user_id": callback_data.user_id,
            "callback_type": callback_data.callback_type,
            "scheduled_time": callback_data.scheduled_time,
            "timezone": callback_data.timezone,
            "message": callback_data.message,
            "priority": callback_data.priority,
            "status": "scheduled"
        }
        
        # Calculate TTL based on scheduled time
        scheduled_dt = datetime.fromisoformat(callback_data.scheduled_time)
        now = datetime.now(pytz.timezone(callback_data.timezone))
        ttl_seconds = int((scheduled_dt - now).total_seconds())
        
        if ttl_seconds > 0:
            redis_client.setex(callback_key, ttl_seconds, json.dumps(callback_info))
            return {"status": "scheduled", "callback_id": callback_key, "ttl": ttl_seconds}
        else:
            return {"status": "failed", "error": "Scheduled time is in the past"}
            
    except Exception as e:
        logger.error(f"Callback scheduling error: {e}")
        return {"status": "failed", "error": str(e)}

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with timezone support"""
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
            "callback_keys": len(redis_client.keys("user_callback:*")),
            "memory_usage": redis_client.info()["used_memory_human"],
            "ttl_default": MEMORY_TTL
        }
    except Exception as e:
        memory_stats = {"error": str(e)}
    
    return HealthResponse(
        status="healthy" if redis_status == "healthy" else "unhealthy",
        timestamp=datetime.now().isoformat(),
        redis_status=redis_status,
        memory_stats=memory_stats,
        timezone_support=True
    )

# Get user memory
@app.get("/memory/{user_id}", response_model=MemoryResponse)
async def get_user_memory(user_id: str):
    """Get memory data for a specific user with timezone conversion"""
    try:
        # Get memory from Redis
        memory_data = redis_client.get(f"user_memory:{user_id}")
        
        if not memory_data:
            # Create new memory for user
            default_preferences = UserPreferences(timezone=DEFAULT_TIMEZONE)
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
        
        # Convert timestamps to user timezone
        user_tz = get_user_timezone(user_id)
        for entry in memory.conversation_history:
            if entry.timestamp:
                entry.timestamp = convert_to_user_timezone(entry.timestamp, user_id)
        
        # Calculate memory size and TTL
        memory_size = len(json.dumps(memory.dict()))
        ttl_remaining = redis_client.ttl(f"user_memory:{user_id}")
        
        # Get timezone info
        timezone_info = {
            "user_timezone": user_tz,
            "current_time": datetime.now(pytz.timezone(user_tz)).isoformat(),
            "utc_offset": datetime.now(pytz.timezone(user_tz)).utcoffset().total_seconds() / 3600
        }
        
        return MemoryResponse(
            user_id=memory.user_id,
            conversation_history=memory.conversation_history,
            preferences=memory.preferences,
            last_interaction=memory.last_interaction,
            session_count=memory.session_count,
            total_interactions=memory.total_interactions,
            memory_size=memory_size,
            ttl_remaining=ttl_remaining,
            timezone_info=timezone_info
        )
        
    except Exception as e:
        logger.error(f"Error getting user memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user memory: {str(e)}")

# Update user memory
@app.post("/memory/{user_id}")
async def update_user_memory(user_id: str, request: MemoryUpdateRequest):
    """Update memory data for a specific user with enhanced features"""
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
                preferences=UserPreferences(timezone=DEFAULT_TIMEZONE),
                last_interaction=datetime.now().isoformat(),
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
        
        # Update conversation history
        if request.conversation_history:
            # Add new entries with timezone conversion
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
        
        # Handle callback data
        if request.callback_data:
            callback_result = schedule_callback(request.callback_data)
            if memory.callbacks is None:
                memory.callbacks = []
            memory.callbacks.append(callback_result)
        
        # Handle email data
        if request.email_data:
            if memory.email_history is None:
                memory.email_history = []
            memory.email_history.append({
                **request.email_data,
                "timestamp": datetime.now().isoformat()
            })
        
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
            "total_interactions": memory.total_interactions,
            "timezone": memory.preferences.timezone,
            "callback_scheduled": bool(request.callback_data),
            "email_sent": bool(request.email_data)
        }
        
    except Exception as e:
        logger.error(f"Error updating user memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user memory: {str(e)}")

# Schedule callback endpoint
@app.post("/memory/{user_id}/callback")
async def schedule_user_callback(user_id: str, callback_data: CallbackRequest):
    """Schedule a callback for a user"""
    try:
        # Ensure user_id matches
        callback_data.user_id = user_id
        
        # Schedule the callback
        result = schedule_callback(callback_data)
        
        # Update user memory with callback info
        memory_data = redis_client.get(f"user_memory:{user_id}")
        if memory_data:
            memory = MemoryData(**json.loads(memory_data))
            if memory.callbacks is None:
                memory.callbacks = []
            memory.callbacks.append(result)
            
            redis_client.setex(
                f"user_memory:{user_id}",
                MEMORY_TTL,
                json.dumps(memory.dict())
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error scheduling callback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule callback: {str(e)}")

# Get user callbacks
@app.get("/memory/{user_id}/callbacks")
async def get_user_callbacks(user_id: str):
    """Get all callbacks for a user"""
    try:
        callback_keys = redis_client.keys(f"user_callback:{user_id}:*")
        callbacks = []
        
        for key in callback_keys:
            callback_data = redis_client.get(key)
            if callback_data:
                callbacks.append(json.loads(callback_data))
        
        return {
            "user_id": user_id,
            "callbacks": callbacks,
            "total": len(callbacks)
        }
        
    except Exception as e:
        logger.error(f"Error getting user callbacks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user callbacks: {str(e)}")

# Clear user memory
@app.delete("/memory/{user_id}")
async def clear_user_memory(user_id: str):
    """Clear memory data for a specific user"""
    try:
        # Delete memory and metadata
        redis_client.delete(f"user_memory:{user_id}")
        redis_client.delete(f"user_metadata:{user_id}")
        
        # Delete callbacks
        callback_keys = redis_client.keys(f"user_callback:{user_id}:*")
        for key in callback_keys:
            redis_client.delete(key)
        
        return {
            "status": "success",
            "message": f"Memory and callbacks cleared for user {user_id}"
        }
        
    except Exception as e:
        logger.error(f"Error clearing user memory: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear user memory: {str(e)}")

# Get conversation summary
@app.get("/memory/{user_id}/summary")
async def get_conversation_summary(user_id: str):
    """Get a summary of the user's conversation history with timezone conversion"""
    try:
        memory_data = redis_client.get(f"user_memory:{user_id}")
        
        if not memory_data:
            raise HTTPException(status_code=404, detail="User memory not found")
        
        memory = MemoryData(**json.loads(memory_data))
        
        # Convert timestamps to user timezone
        user_tz = get_user_timezone(user_id)
        for entry in memory.conversation_history:
            if entry.timestamp:
                entry.timestamp = convert_to_user_timezone(entry.timestamp, user_id)
        
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
            "timezone": user_tz,
            "recent_messages": memory.conversation_history[-10:] if memory.conversation_history else [],
            "callbacks": memory.callbacks or [],
            "email_history": memory.email_history or []
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
            return UserPreferences(timezone=DEFAULT_TIMEZONE)
        
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
            "message": f"Preferences updated for user {user_id}",
            "timezone": preferences.timezone
        }
        
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update user preferences: {str(e)}")

# Memory cleanup endpoint
@app.post("/memory/cleanup")
async def cleanup_old_memories():
    """Clean up old memory entries and expired callbacks"""
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
        
        # Clean up expired callbacks
        callback_keys = redis_client.keys("user_callback:*")
        expired_callbacks = 0
        
        for key in callback_keys:
            ttl = redis_client.ttl(key)
            if ttl == -2:  # Key doesn't exist
                expired_callbacks += 1
                redis_client.delete(key)
        
        return {
            "status": "success",
            "message": f"Memory cleanup completed. {deleted_count} expired entries and {expired_callbacks} expired callbacks removed."
        }
        
    except Exception as e:
        logger.error(f"Error during memory cleanup: {e}")
        raise HTTPException(status_code=500, detail=f"Memory cleanup failed: {str(e)}")

# Get memory statistics
@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory system statistics with callback info"""
    try:
        memory_keys = redis_client.keys("user_memory:*")
        metadata_keys = redis_client.keys("user_metadata:*")
        summary_keys = redis_client.keys("user_summary:*")
        callback_keys = redis_client.keys("user_callback:*")
        
        stats = {
            "total_users": len(memory_keys),
            "users_with_metadata": len(metadata_keys),
            "users_with_summaries": len(summary_keys),
            "active_callbacks": len(callback_keys),
            "memory_usage": redis_client.info()["used_memory_human"],
            "ttl_default": MEMORY_TTL,
            "max_memory_size": MAX_MEMORY_SIZE,
            "timezone_support": True,
            "default_timezone": DEFAULT_TIMEZONE
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get memory stats: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 
