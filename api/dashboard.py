"""Static HTML for the interactive dashboard served at ``/viewer``."""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Flu Data Analytics Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                 color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }
        .report-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                      gap: 20px; margin: 20px 0; }
        .report-card { background: white; padding: 20px; border-radius: 8px;
                      box-shadow: 0 2px 4px rgba(0,0,0,0.1); cursor: pointer;
                      transition: transform 0.2s; }
        .report-card:hover { transform: translateY(-5px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
        .report-card h3 { margin-top: 0; color: #667eea; }
        .export-section { background: white; padding: 20px; border-radius: 8px;
                        margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .export-buttons { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 15px; }
        button { padding: 12px 24px; font-size: 16px; cursor: pointer;
                background: #667eea; color: white; border: none;
                border-radius: 5px; margin: 5px; transition: background 0.3s; }
        button:hover { background: #5568d3; }
        .export-btn { background: #27ae60; padding: 10px 20px; }
        .export-btn:hover { background: #229954; }
        .results { background: white; padding: 20px; border-radius: 8px;
                  margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        table { border-collapse: collapse; width: 100%; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #667eea; color: white; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        tr:hover { background-color: #f0f0f0; }
        h2 { color: #333; margin-top: 0; }
        h3 { color: #667eea; margin-bottom: 10px; }
        .error { color: #e74c3c; padding: 20px; background: #fadbd8; border-radius: 5px; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .metric-value { font-size: 32px; font-weight: bold; color: #667eea; }
        .metric-label { font-size: 14px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Flu Data Analytics Dashboard</h1>
            <p>Washington State respiratory illness surveillance and healthcare impact</p>
        </div>

        <div class="export-section">
            <h3>Export Data Tables (CSV)</h3>
            <p>Download raw data tables for further analysis</p>
            <div class="export-buttons">
                <button class="export-btn" onclick="exportCSV('county_region')">County Region</button>
                <button class="export-btn" onclick="exportCSV('temporal')">Temporal</button>
                <button class="export-btn" onclick="exportCSV('illness')">Illness Data</button>
                <button class="export-btn" onclick="exportCSV('healthcare')">Healthcare</button>
                <button class="export-btn" onclick="exportCSV('historics')">Historical</button>
            </div>
        </div>

        <div class="report-grid">
            <div class="report-card" onclick="loadReport('weekly-trends')">
                <h3>Weekly Trends</h3>
                <p>Track flu activity patterns over time</p>
            </div>
            <div class="report-card" onclick="loadReport('healthcare-impact')">
                <h3>Healthcare Impact by ACH Region</h3>
                <p>Hospital and ER utilization by region</p>
            </div>
            <div class="report-card" onclick="loadReport('historical-summary')">
                <h3>Historical Summary</h3>
                <p>Historical flu season trends</p>
            </div>
        </div>

        <div id="results"></div>
    </div>

    <script>
        function exportCSV(tableName) {
            window.location.href = `/api/export/csv?table=${tableName}`;
        }

        async function loadReport(reportType) {
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '<div class="loading">Loading report...</div>';
            try {
                const response = await fetch(`/api/reports/${reportType}`);
                const data = await response.json();
                if (data.error) {
                    resultsDiv.innerHTML = `<div class="error">Error: ${data.error}</div>`;
                    return;
                }
                displayReport(reportType, data);
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
            }
        }

        function displayReport(reportType, data) {
            const resultsDiv = document.getElementById('results');
            let html = '<div class="results">';
            html += `<h2>${getReportTitle(reportType)}</h2>`;
            if (data.summary) {
                html += '<div style="margin: 20px 0;">';
                for (const [key, value] of Object.entries(data.summary)) {
                    html += `<div class="metric"><div class="metric-value">${value}</div>
                             <div class="metric-label">${key}</div></div>`;
                }
                html += '</div>';
            }
            if (data.data && data.data.length > 0) {
                html += createTable(data.data);
            } else {
                html += '<p>No data available</p>';
            }
            html += '</div>';
            resultsDiv.innerHTML = html;
        }

        function getReportTitle(reportType) {
            const titles = {
                'weekly-trends': 'Weekly Flu Activity Trends',
                'healthcare-impact': 'Healthcare Impact by ACH Region',
                'historical-summary': 'Historical Flu Season Summary'
            };
            return titles[reportType] || reportType;
        }

        function createTable(records) {
            if (records.length === 0) return '<p>No records</p>';
            const headers = Object.keys(records[0]);
            let html = '<table><thead><tr>';
            headers.forEach(header => {
                html += `<th>${header.replace(/_/g, ' ').toUpperCase()}</th>`;
            });
            html += '</tr></thead><tbody>';
            records.forEach(record => {
                html += '<tr>';
                headers.forEach(header => {
                    let value = record[header];
                    if (value !== null && typeof value === 'number') {
                        value = value.toLocaleString();
                    }
                    html += `<td>${value !== null ? value : 'N/A'}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
            return html;
        }
    </script>
</body>
</html>
"""
