# Voice AI System Architecture Documentation

## System Overview

This voice AI system integrates multiple services to provide a comprehensive voice interaction platform with advanced features including email integration, timezone handling, callback systems, follow-up logic, and more.

## Core Services

### 1. VAPI (Voice API) - Port 3000
- **Purpose**: Main voice interaction interface
- **Features**: 
  - DTMF (Dual-Tone Multi-Frequency) processing
  - End call detection and handling
  - Callback system integration
  - Real-time voice processing
- **Connections**: Redis (cache), PostgreSQL (storage), Callback System, DTMF Handler, End Call Handler

### 2. n8n Workflows - Port 5678
- **Purpose**: Workflow automation and orchestration
- **Features**:
  - Email integration and automation
  - Timezone-aware scheduling
  - Follow-up logic implementation
  - File processing workflows
  - Integration with external services
- **Connections**: Elasticsearch (search), Email Service, Timezone Handler, Follow-up Logic

### 3. RAG System - Port 8080
- **Purpose**: Retrieval-Augmented Generation for intelligent responses
- **Features**:
  - Vector search capabilities
  - Document processing and indexing
  - Context-aware responses
  - Integration with Supabase for authentication
- **Connections**: Pinecone Vector DB, Supabase

### 4. Memory Service - Port 8001
- **Purpose**: Conversation memory and context management
- **Features**:
  - User conversation history
  - Context preservation
  - Session management
- **Connections**: Redis (cache), PostgreSQL (persistent storage)

## Data Storage Layer

### Databases
- **Redis**: Caching and session management
- **PostgreSQL**: Persistent data storage
- **Elasticsearch**: Search and indexing
- **Pinecone**: Vector database for RAG
- **Supabase**: Authentication and additional storage

## Integration Services

### Email Integration
```python
# Example n8n workflow for email handling
{
  "email_node": {
    "type": "n8n-nodes-base.emailSend",
    "config": {
      "to": "{{ $json.recipient }}",
      "subject": "Voice AI Follow-up",
      "body": "Thank you for your call..."
    }
  }
}
```

### Timezone Handling
```python
# Example timezone-aware scheduling
import pytz
from datetime import datetime

def get_user_timezone(user_id):
    # Get user's timezone from database
    user_tz = pytz.timezone('America/New_York')
    return user_tz

def schedule_followup(user_id, callback_time):
    user_tz = get_user_timezone(user_id)
    local_time = user_tz.localize(callback_time)
    # Schedule in n8n or external scheduler
```

### Callback System
```python
# Example callback endpoint
@app.post("/callback")
async def handle_callback(callback_data: CallbackRequest):
    # Process callback data
    # Trigger n8n workflow
    # Update database
    return {"status": "processed"}
```

### Follow-up Logic
```python
# Example follow-up workflow in n8n
{
  "trigger": "schedule",
  "actions": [
    {
      "type": "http_request",
      "url": "{{ $json.callback_url }}",
      "method": "POST"
    },
    {
      "type": "email_send",
      "to": "{{ $json.user_email }}"
    }
  ]
}
```

### DTMF Processing
```python
# Example DTMF handler in VAPI
@app.post("/dtmf")
async def handle_dtmf(dtmf_data: DTMFRequest):
    digit = dtmf_data.digit
    call_id = dtmf_data.call_id
    
    # Process DTMF input
    if digit == "1":
        # Handle option 1
        return {"action": "option_1"}
    elif digit == "2":
        # Handle option 2
        return {"action": "option_2"}
```

### End Call Detection
```python
# Example end call handler
@app.post("/endcall")
async def handle_end_call(end_call_data: EndCallRequest):
    call_id = end_call_data.call_id
    
    # Log call end
    await log_call_end(call_id)
    
    # Trigger follow-up workflow
    await trigger_followup_workflow(call_id)
    
    # Send summary email
    await send_call_summary(call_id)
```

## Supabase Integration

### Authentication
```python
from supabase import create_client

supabase = create_client(
    "https://your-project.supabase.co",
    "your-anon-key"
)

# User authentication
def authenticate_user(token):
    user = supabase.auth.get_user(token)
    return user
```

### Data Storage
```python
# Store call data
def store_call_data(call_id, data):
    result = supabase.table('calls').insert({
        'call_id': call_id,
        'data': data,
        'timestamp': datetime.now()
    }).execute()
```

## Infrastructure & Monitoring

### Nginx Proxy
- Routes traffic to appropriate services
- Handles SSL termination
- Load balancing

### Docker Compose
- Orchestrates all services
- Manages networking
- Environment configuration

### Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards
- **Kibana**: Log analysis and search

## Configuration

### Environment Variables
```env
# Core Services
VAPI_PORT=3000
N8N_PORT=5678
RAG_PORT=8080
MEMORY_PORT=8001

# Database Connections
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://user:pass@localhost:5432/voice_ai
ELASTICSEARCH_URL=http://localhost:9200

# External Services
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENVIRONMENT=your-environment

# Email Configuration
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Timezone
DEFAULT_TIMEZONE=America/New_York
```

## Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  vapi:
    build: ./vapi
    ports:
      - "3000:3000"
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://user:pass@postgres:5432/voice_ai
  
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=password
  
  rag:
    build: ./rag
    ports:
      - "8080:8080"
    environment:
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
  
  memory:
    build: ./memory
    ports:
      - "8001:8001"
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://user:pass@postgres:5432/voice_ai
```

## Usage Examples

### 1. Email Follow-up Workflow
1. User completes call
2. VAPI triggers n8n workflow
3. n8n sends follow-up email
4. Email includes call summary and next steps

### 2. Timezone-Aware Scheduling
1. User provides timezone preference
2. System stores in Supabase
3. Follow-up calls scheduled in user's timezone
4. n8n workflows respect timezone settings

### 3. DTMF Menu System
1. User presses key during call
2. VAPI processes DTMF input
3. System routes to appropriate handler
4. Response generated based on selection

### 4. End Call Processing
1. Call ends (detected by VAPI)
2. Call data stored in PostgreSQL
3. Follow-up workflow triggered in n8n
4. Summary email sent to user

## Security Considerations

- All external API keys stored in environment variables
- Supabase handles authentication and authorization
- HTTPS enforced through Nginx
- Database connections use SSL
- Regular security updates for all containers

## Monitoring and Logging

- Prometheus collects metrics from all services
- Grafana dashboards show system health
- Kibana provides log analysis
- Custom alerts for critical issues
- Call quality metrics tracked

## Future Enhancements

- Multi-language support
- Advanced AI model integration
- Real-time transcription
- Sentiment analysis
- Advanced analytics dashboard
- Mobile app integration 