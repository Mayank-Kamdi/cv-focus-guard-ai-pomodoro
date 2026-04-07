from flask import Flask, request, jsonify, render_template_string, Response
from storage import DatabaseManager
from pathlib import Path
import os
import csv
import io

app = Flask(__name__)
# Set proper DB path (relative to this file)
db_path = Path(os.path.dirname(os.path.abspath(__file__))) / "data" / "focus_guard.db"
db_path.parent.mkdir(parents=True, exist_ok=True)
db = DatabaseManager(db_path)

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
    """Enhanced teacher dashboard with Chart.js."""
    teacher_key = request.args.get('teacher_key', '')
    reports = db.get_summary_stats(teacher_key) if teacher_key else []

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Teacher Dashboard - Focus Guard AI</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root { --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --accent: #38bdf8; }
            body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
            .container { max-width: 1100px; margin: auto; }
            header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
            .card { background: var(--card); padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 6px -1px #0000001a; margin-bottom: 1.5rem; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #334155; }
            th { cursor: pointer; color: var(--accent); }
            .focus-high { color: #4ade80; font-weight: bold; }
            .focus-mid { color: #fbbf24; }
            .focus-low { color: #f87171; font-weight: bold; }
            .alert-tag { background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; }
            input, button { padding: 10px 15px; border-radius: 6px; border: 1px solid #334155; }
            input { background: #0f172a; color: white; width: 250px; }
            button { background: var(--accent); color: #0f172a; border: none; font-weight: bold; cursor: pointer; }
            .charts-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }
            .export-btn { background: #10b981; color: white; text-decoration: none; padding: 10px 15px; border-radius: 6px; font-size: 0.9rem; }
        </style>
    </head>
    <body onload="initCharts()">
        <div class="container">
            <header>
                <h1>Focus Guard <span style="color:var(--accent)">AI</span> Dashboard</h1>
                <form method="get" style="display: flex; gap: 10px;">
                    <input type="text" name="teacher_key" value="{{ teacher_key }}" placeholder="Teacher Access Key">
                    <button type="submit">Sync</button>
                    {% if teacher_key %}
                        <a href="/export-csv/{{ teacher_key }}" class="export-btn">Export CSV</a>
                    {% endif %}
                </form>
            </header>

            {% if teacher_key %}
            <div class="charts-grid">
                <div class="card">
                    <h3>Focus Performance Over Time</h3>
                    <canvas id="focusChart" height="150"></canvas>
                </div>
                <div class="card">
                    <h3>Focus vs Distraction Distribution</h3>
                    <canvas id="ratioChart"></canvas>
                </div>
            </div>

            <div class="card">
                <h3>Live Student Monitoring</h3>
                <table id="studentTable">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0)">Student Name</th>
                            <th onclick="sortTable(1)">Sessions</th>
                            <th onclick="sortTable(2)">Total Time</th>
                            <th onclick="sortTable(3)">Avg Focus Score</th>
                            <th onclick="sortTable(4)">Distractions</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in reports %}
                        <tr>
                            <td>{{ row[0] }}</td>
                            <td>{{ row[1] }}</td>
                            <td>{{ row[2] }}m</td>
                            <td class="{{ 'focus-high' if row[3] > 80 else ('focus-low' if row[3] < 50 else 'focus-mid') }}">
                                {{ "%.1f"|format(row[3]) }}%
                            </td>
                            <td>{{ row[4] }}</td>
                            <td>
                                {% if row[3] < 50 %}
                                <span class="alert-tag">Needs Attention</span>
                                {% else %}
                                <span style="color: #4ade80">● Stable</span>
                                {% endif %}
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
                                label: 'Avg Focus %',
                                data: data.map(d => d.avg_focus),
                                borderColor: '#38bdf8',
                                fill: true,
                                backgroundColor: 'rgba(56, 189, 248, 0.1)',
                                tension: 0.3
                            }]
                        },
                        options: { scales: { y: { min: 0, max: 100 } } }
                    });

                    const ctxPie = document.getElementById('ratioChart').getContext('2d');
                    const totalDists = data.reduce((a, b) => a + b.total_distractions, 0);
                    const totalFocus = data.reduce((a, b) => a + b.avg_focus, 0) / (data.length || 1);
                    
                    new Chart(ctxPie, {
                        type: 'doughnut',
                        data: {
                            labels: ['Avg Focus', 'Total Distractions'],
                            datasets: [{
                                data: [totalFocus, totalDists],
                                backgroundColor: ['#38bdf8', '#f87171']
                            }]
                        }
                    });

                    // Auto-refresh every 10 seconds
                    setTimeout(() => location.reload(), 10000);
                }

                function sortTable(n) {
                    var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
                    table = document.getElementById("studentTable");
                    switching = true;
                    dir = "asc";
                    while (switching) {
                        switching = false;
                        rows = table.rows;
                        for (i = 1; i < (rows.length - 1); i++) {
                            shouldSwitch = false;
                            x = rows[i].getElementsByTagName("TD")[n];
                            y = rows[i + 1].getElementsByTagName("TD")[n];
                            if (dir == "asc") {
                                if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {
                                    shouldSwitch = true;
                                    break;
                                }
                            } else if (dir == "desc") {
                                if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {
                                    shouldSwitch = true;
                                    break;
                                }
                            }
                        }
                        if (shouldSwitch) {
                            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                            switching = true;
                            switchcount ++;
                        } else {
                            if (switchcount == 0 && dir == "asc") {
                                dir = "desc";
                                switching = true;
                            }
                        }
                    }
                }
            </script>
            {% else %}
            <div class="card" style="text-align: center; padding: 4rem;">
                <h2 style="color: var(--accent)">Welcome, Educator</h2>
                <p>Please enter your 8-character teacher key to access student reports and real-time focus analytics.</p>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, teacher_key=teacher_key, reports=reports)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
