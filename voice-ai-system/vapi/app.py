from flask import Flask, jsonify, request, render_template_string
import os
import json
from datetime import datetime

app = Flask(__name__)

# Mock data for dashboard functionality
calls_data = []
analytics_data = {
    "total_calls": 0,
    "successful_calls": 0,
    "failed_calls": 0,
    "average_duration": 0
}

@app.route('/', methods=['GET'])
def dashboard():
    """Main dashboard page"""
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Voice AI Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
            .calls-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .call-item { border-bottom: 1px solid #eee; padding: 10px 0; }
            .status-success { color: green; }
            .status-failed { color: red; }
            .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
            .btn:hover { background: #0056b3; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Voice AI Dashboard</h1>
                <p>Manage your voice AI calls and monitor performance</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h3>Total Calls</h3>
                    <div class="stat-number" id="total-calls">{{ analytics.total_calls }}</div>
                </div>
                <div class="stat-card">
                    <h3>Successful Calls</h3>
                    <div class="stat-number status-success" id="successful-calls">{{ analytics.successful_calls }}</div>
                </div>
                <div class="stat-card">
                    <h3>Failed Calls</h3>
                    <div class="stat-number status-failed" id="failed-calls">{{ analytics.failed_calls }}</div>
                </div>
                <div class="stat-card">
                    <h3>Avg Duration</h3>
                    <div class="stat-number" id="avg-duration">{{ analytics.average_duration }}s</div>
                </div>
            </div>
            
            <div class="calls-section">
                <h2>Recent Calls</h2>
                <button class="btn" onclick="startNewCall()">Start New Call</button>
                <div id="calls-list">
                    {% for call in calls %}
                    <div class="call-item">
                        <strong>Call ID:</strong> {{ call.id }} | 
                        <strong>Status:</strong> <span class="status-{{ call.status }}">{{ call.status }}</span> | 
                        <strong>Duration:</strong> {{ call.duration }}s | 
                        <strong>Time:</strong> {{ call.timestamp }}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <script>
            function startNewCall() {
                fetch('/api/v1/calls/start', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        alert('New call started: ' + data.call_id);
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
                        document.getElementById('failed-calls').textContent = data.failed_calls;
                        document.getElementById('avg-duration').textContent = data.average_duration + 's';
                    });
            }, 30000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, analytics=analytics_data, calls=calls_data)

@app.route('/api/v1/hello', methods=['GET'])
def hello_world():
    return jsonify(message="Hello, World!")

@app.route('/api/v1/greet', methods=['POST'])
def greet():
    data = request.get_json()
    name = data.get("name", "stranger")
    return jsonify(message=f"Hello, {name}!")

@app.route('/api/v1/calls/start', methods=['POST'])
def start_call():
    """Start a new voice AI call"""
    call_id = f"call_{len(calls_data) + 1}_{int(datetime.now().timestamp())}"
    new_call = {
        "id": call_id,
        "status": "initiated",
        "duration": 0,
        "timestamp": datetime.now().isoformat()
    }
    calls_data.append(new_call)
    analytics_data["total_calls"] += 1
    return jsonify({"call_id": call_id, "status": "started"})

@app.route('/api/v1/calls', methods=['GET'])
def get_calls():
    """Get all calls"""
    return jsonify(calls_data)

@app.route('/api/v1/analytics', methods=['GET'])
def get_analytics():
    """Get analytics data"""
    return jsonify(analytics_data)

@app.route('/api/v1/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    config = {
        "vapi_api_key": os.getenv("VAPI_API_KEY", "not_set"),
        "vapi_project_id": os.getenv("VAPI_PROJECT_ID", "not_set"),
        "openai_api_key": os.getenv("OPENAI_API_KEY", "not_set"),
        "status": "configured" if os.getenv("VAPI_API_KEY") else "not_configured"
    }
    return jsonify(config)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True) 