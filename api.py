from flask import Flask, request, jsonify, render_template_string, Response, redirect, url_for
from storage import DatabaseManager
from pathlib import Path
import os
import csv
import io
import json

app = Flask(__name__)
# Set proper DB path (relative to this file)
db_path = Path(os.path.dirname(os.path.abspath(__file__))) / "data" / "focus_guard.db"
db_path.parent.mkdir(parents=True, exist_ok=True)
db = DatabaseManager(db_path)

# Register custom jinja filter
app.jinja_env.filters['from_json'] = json.loads

@app.route('/')
def home():
    """Redirect root to dashboard."""
    return redirect(url_for('dashboard'))

@app.route('/submit-data', methods=['POST'])
def submit_data():
    """POST /submit-data: Receive student session data."""
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    required_fields = ["student_name", "teacher_key", "duration_mins", "distractions", "focus_score", "goals"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    db.save_session(
        data["student_name"],
        data["teacher_key"],
        data["duration_mins"],
        data["distractions"],
        data["focus_score"],
        data["goals"]
    )

    return jsonify({"success": "Data saved correctly"}), 201

@app.route('/api/teacher/<teacher_key>/periodic')
def api_periodic_data(teacher_key):
    period = request.args.get('period', 'daily')
    data = db.get_periodic_aggregation(teacher_key, period)
    return jsonify([{
        "period": row[0],
        "avg_focus": round(row[1], 2),
        "total_distractions": row[2],
        "total_duration": row[3]
    } for row in data])

@app.route('/export-csv/<teacher_key>')
def export_csv(teacher_key):
    """Export student data as CSV."""
    sessions = db.get_student_sessions(teacher_key)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Timestamp', 'Duration (m)', 'Distractions', 'Focus Score', 'Goals'])
    for s in sessions:
        writer.writerow([s['student_name'], s['timestamp'], s['duration_mins'], s['distractions'], s['focus_score'], s['goals']])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=focus_guard_report_{teacher_key}.csv"}
    )

@app.route('/dashboard', methods=['GET'])
def dashboard():
    """Detailed teacher dashboard with advanced analytics and session tracking."""
    teacher_key = request.args.get('teacher_key', '')
    reports = db.get_summary_stats(teacher_key) if teacher_key else []
    
    # Get total stats for the summary cards
    total_students = len(reports)
    avg_class_focus = sum(r[3] for r in reports) / total_students if total_students > 0 else 0
    total_hours = sum(r[2] for r in reports) / 60 if total_students > 0 else 0

    # Get raw sessions for the detailed log
    sessions = db.get_student_sessions(teacher_key)[:20] if teacher_key else []

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Teacher AI Analytics - Focus Guard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            :root { 
                --bg: #030712; --card: #111827; --card-border: #1f2937;
                --text: #f9fafb; --text-muted: #9ca3af;
                --accent: #38bdf8; --success: #10b981; --warn: #f59e0b; --danger: #ef4444;
            }
            body { 
                font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); 
                margin: 0; padding: 20px; line-height: 1.5;
            }
            .container { max-width: 1200px; margin: auto; }
            header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
            
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
            .stat-card { background: var(--card); padding: 1.5rem; border-radius: 12px; border: 1px solid var(--card-border); }
            .stat-value { font-size: 2rem; font-weight: 700; color: var(--accent); margin-bottom: 0.25rem; }
            .stat-label { color: var(--text-muted); font-size: 0.875rem; text-transform: uppercase; letter-spacing: 0.05em; }

            .card { background: var(--card); border: 1px solid var(--card-border); padding: 1.5rem; border-radius: 16px; margin-bottom: 1.5rem; overflow: hidden; }
            .card-title { font-size: 1.25rem; font-weight: 600; margin-bottom: 1.5rem; display: flex; align-items: center; gap: 0.5rem; }
            
            .charts-grid { display: grid; grid-template-columns: 1.5fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem; }
            
            table { width: 100%; border-collapse: collapse; text-align: left; }
            th { padding: 12px; border-bottom: 2px solid var(--card-border); color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; }
            td { padding: 14px 12px; border-bottom: 1px solid var(--card-border); font-size: 0.9375rem; }
            
            .badge { padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
            .badge-success { background: rgba(16, 185, 129, 0.1); color: var(--success); }
            .badge-warn { background: rgba(245, 158, 11, 0.1); color: var(--warn); }
            .badge-danger { background: rgba(239, 68, 68, 0.1); color: var(--danger); }

            input, button { padding: 12px 18px; border-radius: 8px; border: 1px solid var(--card-border); font-family: inherit; }
            input { background: #1f2937; color: white; width: 280px; transition: border-color 0.2s; }
            input:focus { outline: none; border-color: var(--accent); }
            button { background: var(--accent); color: #030712; border: none; font-weight: 700; cursor: pointer; transition: opacity 0.2s; }
            button:hover { opacity: 0.9; }

            .export-btn { background: var(--success); color: white; text-decoration: none; padding: 10px 20px; border-radius: 8px; font-size: 0.875rem; font-weight: 600; }
            
            .goal-chip { background: #374151; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin: 2px; display: inline-block; }
        </style>
    </head>
    <body onload="initCharts()">
        <div class="container">
            <header>
                <div>
                    <h1 style="margin: 0;">Focus Guard <span style="color:var(--accent)">AI</span></h1>
                    <p style="color: var(--text-muted); margin: 0;">Education & Insight Platform</p>
                </div>
                <form method="get" style="display: flex; gap: 12px; align-items: center;">
                    <input type="text" name="teacher_key" value="{{ teacher_key }}" placeholder="Access Key (8-chars)">
                    <button type="submit">Sync Data</button>
                    {% if teacher_key %}
                        <a href="/export-csv/{{ teacher_key }}" class="export-btn">Download CSV</a>
                    {% endif %}
                </form>
            </header>

            {% if teacher_key %}
            <!-- Summary Stats -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{{ total_students }}</div>
                    <div class="stat-label">Active Students</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ "%.1f"|format(avg_class_focus) }}%</div>
                    <div class="stat-label">Class Avg Focus</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{{ "%.1f"|format(total_hours) }}</div>
                    <div class="stat-label">Total Deep Work Hours</div>
                </div>
            </div>

            <div class="charts-grid">
                <div class="card">
                    <div class="card-title">📈 Group Retention Trend</div>
                    <canvas id="focusChart" height="140"></canvas>
                </div>
                <div class="card">
                    <div class="card-title">🎯 Efficiency Ratio</div>
                    <canvas id="ratioChart"></canvas>
                </div>
            </div>

            <div class="card">
                <div class="card-title">👥 Student Performance Ranking</div>
                <table id="studentTable">
                    <thead>
                        <tr>
                            <th>Student</th>
                            <th>Sessions</th>
                            <th>Total Time</th>
                            <th>Avg Focus</th>
                            <th>Distractions</th>
                            <th>Current Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in reports %}
                        <tr>
                            <td style="font-weight: 600;">{{ row[0] }}</td>
                            <td>{{ row[1] }}</td>
                            <td>{{ row[2] }} min</td>
                            <td style="font-weight: 700;">
                                <span style="color: {{ '#10b981' if row[3] > 80 else ('#ef4444' if row[3] < 50 else '#f59e0b') }}">
                                    {{ "%.1f"|format(row[3]) }}%
                                </span>
                            </td>
                            <td>{{ row[4] }}</td>
                            <td>
                                {% if row[3] < 50 %}
                                <span class="badge badge-danger">Needs Intervention</span>
                                {% elif row[3] < 75 %}
                                <span class="badge badge-warn">Moderate</span>
                                {% else %}
                                <span class="badge badge-success">High Engagement</span>
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="card">
                <div class="card-title">🕒 Recent Session Log (Detailed)</div>
                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Student</th>
                            <th>Dur</th>
                            <th>Score</th>
                            <th>Goals Tracked</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for s in sessions %}
                        <tr>
                            <td style="color: var(--text-muted); font-size: 0.8rem;">{{ s.timestamp }}</td>
                            <td>{{ s.student_name }}</td>
                            <td>{{ s.duration_mins }}m</td>
                            <td>{{ "%.1f"|format(s.focus_score) }}%</td>
                            <td>
                                {% set goals_list = s.goals | from_json if s.goals and s.goals != '[]' else [] %}
                                {% for goal in goals_list %}
                                    <span class="goal-chip">{{ goal }}</span>
                                {% else %}
                                    <span style="color: var(--text-muted); font-style: italic;">No specific goals</span>
                                {% endfor %}
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <script>
                async function initCharts() {
                    const resp = await fetch('/api/teacher/{{ teacher_key }}/periodic?period=daily');
                    const data = await resp.json();
                    
                    const ctxLine = document.getElementById('focusChart').getContext('2d');
                    new Chart(ctxLine, {
                        type: 'line',
                        data: {
                            labels: data.map(d => d.period),
                            datasets: [{
                                label: 'Class Focus %',
                                data: data.map(d => d.avg_focus),
                                borderColor: '#38bdf8',
                                borderWidth: 3,
                                pointBackgroundColor: '#38bdf8',
                                fill: true,
                                backgroundColor: 'rgba(56, 189, 248, 0.05)',
                                tension: 0.4
                            }]
                        },
                        options: { 
                            responsive: true,
                            plugins: { legend: { display: false } },
                            scales: { 
                                y: { min: 0, max: 100, grid: { color: '#1f2937' }, ticks: { color: '#9ca3af' } },
                                x: { grid: { display: false }, ticks: { color: '#9ca3af' } }
                            }
                        }
                    });

                    const ctxPie = document.getElementById('ratioChart').getContext('2d');
                    const totalDists = data.reduce((a, b) => a + b.total_distractions, 0);
                    const totalDuration = data.reduce((a, b) => a + b.total_duration, 0);
                    
                    new Chart(ctxPie, {
                        type: 'doughnut',
                        data: {
                            labels: ['Total Work (m)', 'Distractions'],
                            datasets: [{
                                data: [totalDuration, totalDists],
                                backgroundColor: ['#10b981', '#ef4444'],
                                borderWidth: 0,
                                hoverOffset: 10
                            }]
                        },
                        options: {
                            plugins: {
                                legend: { position: 'bottom', labels: { color: '#9ca3af', padding: 20 } }
                            },
                        }
                    });

                    // Auto-refresh every 30 seconds to be less intrusive
                    setTimeout(() => location.reload(), 30000);
                }
            </script>
            {% else %}
            <div class="card" style="text-align: center; padding: 6rem 2rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem;">🎓</div>
                <h2 style="color: var(--accent); margin-top: 0;">Educator Access Terminal</h2>
                <p style="color: var(--text-muted); max-width: 500px; margin: auto;">Enter your secure teacher access key to visualize class performance metrics, download historical reports, and monitor real-time focus trends.</p>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, 
                                  teacher_key=teacher_key, 
                                  reports=reports, 
                                  total_students=total_students,
                                  avg_class_focus=avg_class_focus,
                                  total_hours=total_hours,
                                  sessions=sessions)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
