# Voice AI System Screenshots

This directory contains screenshots of the Voice AI system components for documentation and setup guidance.

## Required Screenshots

### 1. VAPI Dashboard
**File**: `vapi-dashboard.png`
**Description**: VAPI dashboard showing:
- Active calls and their status
- Assistant configuration
- Voice model settings
- Webhook configuration
- Call analytics and metrics

### 2. n8n Workflow
**File**: `n8n-workflow.png`
**Description**: n8n workflow canvas showing:
- Voice webhook trigger
- RAG query processing
- Memory update nodes
- VAPI response integration
- Error handling and logging

### 3. RAG Knowledge Base
**File**: `rag-interface.png`
**Description**: RAG system interface showing:
- Document ingestion status
- Knowledge base search results
- Query processing
- Vector storage metrics
- Document management

### 4. Memory System
**File**: `memory-system.png`
**Description**: Memory management dashboard showing:
- User conversation history
- Memory storage statistics
- User preferences
- Session management
- Memory cleanup operations

### 5. Grafana Dashboard
**File**: `grafana-dashboard.png`
**Description**: Grafana monitoring dashboard showing:
- Voice call metrics
- System performance
- Error rates
- Response times
- Resource utilization

### 6. Kibana Analytics
**File**: `kibana-analytics.png`
**Description**: Kibana analytics showing:
- Document search analytics
- User interaction patterns
- System logs
- Performance metrics
- Error analysis

### 7. System Architecture
**File**: `system-architecture.png`
**Description**: High-level system diagram showing:
- Component relationships
- Data flow
- API connections
- Service dependencies

### 8. Docker Compose Status
**File**: `docker-compose-status.png`
**Description**: Docker Compose status showing:
- All services running
- Container health
- Resource usage
- Network connectivity

## Screenshot Guidelines

### Quality Requirements
- **Resolution**: Minimum 1920x1080
- **Format**: PNG or JPG
- **File Size**: Maximum 2MB per screenshot
- **Clarity**: Clear, readable text and UI elements

### Content Guidelines
- Show relevant data and metrics
- Include timestamps when applicable
- Highlight important configuration settings
- Demonstrate successful operations
- Show error states when relevant

### Naming Convention
- Use descriptive filenames
- Include component name
- Add date if needed
- Use lowercase with hyphens

## Setup Instructions

1. **Start the system**:
   ```bash
   docker-compose up -d
   ```

2. **Access each component**:
   - VAPI: http://localhost:3000
   - n8n: http://localhost:5678
   - RAG API: http://localhost:8000/docs
   - Memory API: http://localhost:8001/docs
   - Grafana: http://localhost:3001
   - Kibana: http://localhost:5601

3. **Capture screenshots**:
   - Use browser developer tools for high-quality screenshots
   - Ensure all relevant information is visible
   - Include navigation and context

4. **Update documentation**:
   - Reference screenshots in setup guides
   - Include in troubleshooting sections
   - Use for training materials

## Maintenance

- Update screenshots when UI changes
- Keep screenshots current with latest versions
- Archive old screenshots for version history
- Document any UI changes in release notes 