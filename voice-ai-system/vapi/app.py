from flask import Flask, jsonify, request, render_template_string
import os
import json
from datetime import datetime
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Professional configuration
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "America/New_York")
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "587"))
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

# Mock data for dashboard functionality
calls_data = []
analytics_data = {
    "total_calls": 0,
    "successful_calls": 0,
    "failed_calls": 0,
    "average_duration": 0,
    "sentiment_scores": {"positive": 0, "neutral": 0, "negative": 0},
    "timezone_distribution": {},
    "callback_scheduled": 0,
    "emails_sent": 0
}

# Professional email templates
EMAIL_TEMPLATES = {
    "call_summary": {
        "subject": "Your Call Summary - Professional Voice AI",
        "html": """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #3498db; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f8f9fa; }
                .summary { background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #3498db; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                .button { background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Call Summary</h1>
                    <p>Professional Voice AI System</p>
                </div>
                <div class="content">
                    <h2>Thank you for your call!</h2>
                    <p>Here's a summary of your conversation:</p>
                    <div class="summary">
                        <strong>Call ID:</strong> {{call_id}}<br>
                        <strong>Duration:</strong> {{duration}} seconds<br>
                        <strong>Date:</strong> {{date}}<br>
                        <strong>Sentiment:</strong> {{sentiment}}<br>
                        <strong>Key Points:</strong> {{key_points}}
                    </div>
                    <p>If you have any questions, please don't hesitate to reach out.</p>
                    <a href="{{callback_url}}" class="button">Schedule Follow-up</a>
                </div>
                <div class="footer">
                    <p>This is an automated message from the Professional Voice AI System</p>
                </div>
            </div>
        </body>
        </html>
        """
    },
    "followup": {
        "subject": "Follow-up from Your Recent Call",
        "html": """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #27ae60; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f8f9fa; }
                .details { background: white; padding: 15px; margin: 15px 0; border-left: 4px solid #27ae60; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                .button { background: #27ae60; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Follow-up</h1>
                    <p>Professional Voice AI System</p>
                </div>
                <div class="content">
                    <h2>We'd like to follow up on your recent call</h2>
                    <div class="details">
                        <strong>Call Date:</strong> {{call_date}}<br>
                        <strong>Follow-up Reason:</strong> {{reason}}<br>
                        <strong>Next Steps:</strong> {{next_steps}}
                    </div>
                    <p>Please let us know if you need any additional assistance.</p>
                    <a href="{{contact_url}}" class="button">Contact Us</a>
                </div>
                <div class="footer">
                    <p>This is an automated follow-up from the Professional Voice AI System</p>
                </div>
            </div>
        </body>
        </html>
        """
    }
}

def get_user_timezone(user_id):
    """Get user's timezone preference"""
    # In a real implementation, this would query the memory system
    return DEFAULT_TIMEZONE

def convert_to_user_timezone(timestamp, user_id):
    """Convert timestamp to user's timezone"""
    try:
        user_tz = pytz.timezone(get_user_timezone(user_id))
        utc_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        local_time = utc_time.astimezone(user_tz)
        return local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return timestamp

def send_professional_email(to_email, template_name, variables):
    """Send professional email using templates"""
    if not EMAIL_USERNAME or not EMAIL_PASSWORD:
        return {"status": "error", "message": "Email configuration not set"}
    
    try:
        template = EMAIL_TEMPLATES.get(template_name)
        if not template:
            return {"status": "error", "message": "Template not found"}
        
        # Render template with variables
        html_content = template["html"]
        for key, value in variables.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = template["subject"]
        msg['From'] = EMAIL_USERNAME
        msg['To'] = to_email
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(EMAIL_SMTP_HOST, EMAIL_SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            server.send_message(msg)
        
        return {"status": "success", "message": "Email sent successfully"}
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to send email: {str(e)}"}

@app.route('/', methods=['GET'])
def dashboard():
    """Professional dashboard page"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice AI Professional Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #f5f7fa; }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 25px; margin-bottom: 30px; }
            .stat-card { background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); transition: transform 0.2s; }
            .stat-card:hover { transform: translateY(-2px); }
            .stat-number { font-size: 2.5em; font-weight: bold; color: #667eea; margin-bottom: 10px; }
            .stat-label { color: #666; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }
            .calls-section { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 30px; }
            .call-item { border-bottom: 1px solid #eee; padding: 15px 0; display: flex; justify-content: space-between; align-items: center; }
            .status-success { color: #27ae60; font-weight: bold; }
            .status-failed { color: #e74c3c; font-weight: bold; }
            .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 25px; border: none; border-radius: 25px; cursor: pointer; font-size: 16px; transition: all 0.3s; }
            .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
            .professional-features { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
            .feature-item { padding: 20px; border-left: 4px solid #667eea; background: #f8f9fa; border-radius: 5px; }
            .feature-title { font-weight: bold; color: #2c3e50; margin-bottom: 10px; }
            .feature-desc { color: #666; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Voice AI Professional Dashboard</h1>
                <p>Enterprise-Grade Voice AI Platform with Advanced Features</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number" id="total-calls">{{ analytics.total_calls }}</div>
                    <div class="stat-label">Total Calls</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number status-success" id="successful-calls">{{ analytics.successful_calls }}</div>
                    <div class="stat-label">Successful Calls</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="avg-duration">{{ analytics.average_duration }}s</div>
                    <div class="stat-label">Avg Duration</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="emails-sent">{{ analytics.emails_sent }}</div>
                    <div class="stat-label">Emails Sent</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="callbacks-scheduled">{{ analytics.callback_scheduled }}</div>
                    <div class="stat-label">Callbacks Scheduled</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="positive-sentiment">{{ analytics.sentiment_scores.positive }}</div>
                    <div class="stat-label">Positive Sentiment</div>
                </div>
            </div>
            
            <div class="calls-section">
                <h2>Recent Calls</h2>
                <button class="btn" onclick="startNewCall()">Start New Professional Call</button>
                <div id="calls-list">
                    {% for call in calls %}
                    <div class="call-item">
                        <div>
                            <strong>Call ID:</strong> {{ call.id }} | 
                            <strong>Status:</strong> <span class="status-{{ call.status }}">{{ call.status }}</span> | 
                            <strong>Duration:</strong> {{ call.duration }}s | 
                            <strong>Time:</strong> {{ call.timestamp }}
                        </div>
                        <div>
                            <strong>Sentiment:</strong> {{ call.sentiment or 'neutral' }} | 
                            <strong>Timezone:</strong> {{ call.timezone or 'UTC' }}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="professional-features">
                <h2>Professional Features</h2>
                <div class="feature-grid">
                    <div class="feature-item">
                        <div class="feature-title">Advanced Email Integration</div>
                        <div class="feature-desc">Professional email templates with timezone-aware scheduling and delivery tracking</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-title">Timezone Handling</div>
                        <div class="feature-desc">Automatic timezone detection and user-specific scheduling with PyTZ integration</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-title">Multi-channel Callbacks</div>
                        <div class="feature-desc">Professional callback system supporting email, SMS, calls, and calendar invites</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-title">Real-time Sentiment Analysis</div>
                        <div class="feature-desc">AI-powered emotion detection with escalation thresholds and trend analysis</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-title">Enterprise Security</div>
                        <div class="feature-desc">SSL encryption, audit logging, and comprehensive security measures</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-title">Professional Monitoring</div>
                        <div class="feature-desc">Prometheus/Grafana/Kibana stack with custom metrics and alerting</div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            function startNewCall() {
                fetch('/api/v1/calls/start', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        alert('New professional call started: ' + data.call_id);
                        location.reload();
                    });
            }
            
            // Auto-refresh every 30 seconds
            setInterval(() => {
                fetch('/api/v1/analytics')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('total-calls').textContent = data.total_calls;
                        document.getElementById('successful-calls').textContent = data.successful_calls;
                        document.getElementById('avg-duration').textContent = data.average_duration + 's';
                        document.getElementById('emails-sent').textContent = data.emails_sent;
                        document.getElementById('callbacks-scheduled').textContent = data.callback_scheduled;
                        document.getElementById('positive-sentiment').textContent = data.sentiment_scores.positive;
                    });
            }, 30000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, analytics=analytics_data, calls=calls_data)

@app.route('/api/v1/hello', methods=['GET'])
def hello_world():
    return jsonify(message="Hello from Professional Voice AI System!")

@app.route('/api/v1/greet', methods=['POST'])
def greet():
    data = request.get_json()
    name = data.get("name", "stranger")
    return jsonify(message=f"Hello, {name}! Welcome to the Professional Voice AI System.")

@app.route('/api/v1/calls/start', methods=['POST'])
def start_call():
    """Start a new professional voice AI call"""
    call_id = f"call_{len(calls_data) + 1}_{int(datetime.now().timestamp())}"
    new_call = {
        "id": call_id,
        "status": "initiated",
        "duration": 0,
        "timestamp": datetime.now().isoformat(),
        "sentiment": "neutral",
        "timezone": DEFAULT_TIMEZONE
    }
    calls_data.append(new_call)
    analytics_data["total_calls"] += 1
    return jsonify({"call_id": call_id, "status": "started", "timezone": DEFAULT_TIMEZONE})

@app.route('/api/v1/calls', methods=['GET'])
def get_calls():
    """Get all calls with timezone conversion"""
    calls_with_timezone = []
    for call in calls_data:
        call_copy = call.copy()
        call_copy["timestamp"] = convert_to_user_timezone(call["timestamp"], "default")
        calls_with_timezone.append(call_copy)
    return jsonify(calls_with_timezone)

@app.route('/api/v1/analytics', methods=['GET'])
def get_analytics():
    """Get professional analytics data"""
    return jsonify(analytics_data)

@app.route('/api/v1/config', methods=['GET'])
def get_config():
    """Get current professional configuration"""
    config = {
        "vapi_api_key": os.getenv("VAPI_API_KEY", "not_set"),
        "vapi_project_id": os.getenv("VAPI_PROJECT_ID", "not_set"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", "not_set"),
        "email_configured": bool(EMAIL_USERNAME and EMAIL_PASSWORD),
        "timezone_default": DEFAULT_TIMEZONE,
        "professional_features": {
            "email_templates": True,
            "timezone_handling": True,
            "callback_system": True,
            "sentiment_analysis": True,
            "security": True,
            "monitoring": True
        },
        "status": "professional_configured" if os.getenv("VAPI_API_KEY") else "not_configured"
    }
    return jsonify(config)

@app.route('/api/v1/email/send', methods=['POST'])
def send_email():
    """Send professional email using templates"""
    data = request.get_json()
    to_email = data.get("to")
    template_name = data.get("template", "call_summary")
    variables = data.get("variables", {})
    
    if not to_email:
        return jsonify({"status": "error", "message": "Recipient email required"})
    
    result = send_professional_email(to_email, template_name, variables)
    if result["status"] == "success":
        analytics_data["emails_sent"] += 1
    
    return jsonify(result)

@app.route('/api/v1/callback/schedule', methods=['POST'])
def schedule_callback():
    """Schedule a professional callback"""
    data = request.get_json()
    user_id = data.get("user_id")
    callback_type = data.get("callback_type", "email")
    scheduled_time = data.get("scheduled_time")
    timezone = data.get("timezone", DEFAULT_TIMEZONE)
    message = data.get("message", "")
    
    # In a real implementation, this would integrate with the memory system
    callback_id = f"callback_{user_id}_{int(datetime.now().timestamp())}"
    
    analytics_data["callback_scheduled"] += 1
    
    return jsonify({
        "status": "success",
        "callback_id": callback_id,
        "scheduled_time": scheduled_time,
        "timezone": timezone,
        "type": callback_type
    })

@app.route('/api/v1/sentiment/analyze', methods=['POST'])
def analyze_sentiment():
    """Analyze sentiment of text"""
    data = request.get_json()
    text = data.get("text", "")
    
    # Simple sentiment analysis (in production, use a proper NLP service)
    positive_words = ["good", "great", "excellent", "happy", "satisfied", "love", "like"]
    negative_words = ["bad", "terrible", "awful", "angry", "frustrated", "hate", "dislike"]
    
    text_lower = text.lower()
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        sentiment = "positive"
        analytics_data["sentiment_scores"]["positive"] += 1
    elif negative_count > positive_count:
        sentiment = "negative"
        analytics_data["sentiment_scores"]["negative"] += 1
    else:
        sentiment = "neutral"
        analytics_data["sentiment_scores"]["neutral"] += 1
    
    return jsonify({
        "sentiment": sentiment,
        "confidence": 0.8,
        "positive_score": positive_count,
        "negative_score": negative_count
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True) 
