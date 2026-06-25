"""HTTP routes: health check, dashboard, JSON reports, and CSV export."""

from __future__ import annotations

import csv
from io import StringIO

from flask import Blueprint, Response, jsonify, render_template_string, request
from sqlalchemy import text

from api import queries
from api.dashboard import DASHBOARD_HTML
from flu_pipeline.config import APP_SCHEMA
from flu_pipeline.db.engine import get_engine
from flu_pipeline.db.schema import TABLES

bp = Blueprint("flu", __name__)

# Whitelist of exportable tables, derived from the canonical registry.
EXPORTABLE_TABLES = {table.name for table in TABLES}


def _rows_to_dicts(result) -> list[dict]:
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]


@bp.route("/")
def home():
    return jsonify(
        {
            "message": "Flu Data Pipeline API",
            "status": "running",
            "endpoints": {
                "/health": "Check API and database health",
                "/viewer": "Interactive data viewer",
                "/api/reports/weekly-trends": "Weekly flu activity trends",
                "/api/reports/healthcare-impact": "Healthcare impact by ACH region",
                "/api/reports/historical-summary": "Historical flu season summary",
                "/api/export/csv?table=<table_name>": "Export a table as CSV",
            },
        }
    )


@bp.route("/health")
def health():
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as JSON
        return jsonify({"status": "unhealthy", "error": str(exc)}), 500


@bp.route("/viewer")
def viewer():
    return render_template_string(DASHBOARD_HTML)


@bp.route("/api/reports/weekly-trends")
def weekly_trends():
    try:
        with get_engine().connect() as conn:
            data = _rows_to_dicts(conn.execute(queries.WEEKLY_TRENDS))

        for row in data:
            if row.get("avg_percent_positive") is not None:
                row["avg_percent_positive"] = f"{row['avg_percent_positive']:.2f}%"

        summary = {}
        if data:
            summary["Latest Week"] = str(data[0]["week_end"]) if data[0]["week_end"] else "N/A"
            summary["Avg County %"] = data[0]["avg_percent_positive"] or "N/A"
            summary["Illness Type"] = data[0]["respiratory_illness_type"]
        return jsonify({"data": data, "summary": summary}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


@bp.route("/api/reports/healthcare-impact")
def healthcare_impact():
    try:
        with get_engine().connect() as conn:
            data = _rows_to_dicts(conn.execute(queries.HEALTHCARE_IMPACT))

        for row in data:
            if row.get("avg_hospitalization_percent") is not None:
                row["avg_hospitalization_percent"] = f"{row['avg_hospitalization_percent']:.2f}%"
            if row.get("avg_er_visit_percent") is not None:
                row["avg_er_visit_percent"] = f"{row['avg_er_visit_percent']:.2f}%"
            if row.get("avg_hospital_to_er_ratio") is not None:
                row["avg_hospital_to_er_ratio"] = f"{row['avg_hospital_to_er_ratio']:.3f}"
            if row.get("avg_population_density") is not None:
                row["avg_population_density"] = f"{row['avg_population_density']:.1f}"

        summary = {
            "ACH Regions": len(data),
            "Total Counties": sum(
                d["counties_in_region"] for d in data if d.get("counties_in_region")
            ),
        }
        return jsonify({"data": data, "summary": summary}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


@bp.route("/api/reports/historical-summary")
def historical_summary():
    try:
        with get_engine().connect() as conn:
            data = _rows_to_dicts(conn.execute(queries.HISTORICAL_SUMMARY))

        for row in data:
            for col in ("peak_ili_percent", "average_wili_percent", "peak_vs_avg_diff"):
                if row.get(col) is not None:
                    row[col] = f"{row[col]:.2f}%"

        summary = {}
        if data:
            peaks = [
                float(d["peak_ili_percent"].rstrip("%"))
                for d in data
                if d.get("peak_ili_percent")
            ]
            summary = {
                "Years Tracked": len(data),
                "Highest Peak": f"{max(peaks):.2f}%" if peaks else "N/A",
            }
        return jsonify({"data": data, "summary": summary}), 200
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500


@bp.route("/api/export/csv")
def export_csv():
    table = request.args.get("table", "")
    if table not in EXPORTABLE_TABLES:
        return (
            jsonify(
                {"error": f"Invalid table. Choose from: {', '.join(sorted(EXPORTABLE_TABLES))}"}
            ),
            400,
        )

    try:
        # ``table`` is validated against the registry whitelist above, so this
        # identifier is safe to interpolate.
        query = text(f"SELECT * FROM {APP_SCHEMA}.{table} LIMIT 1000")
        with get_engine().connect() as conn:
            result = conn.execute(query)
            columns = result.keys()
            rows = result.fetchall()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        writer.writerows(rows)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={table}.csv"},
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": str(exc)}), 500
