"""Meridian Corp claims service (demo repository, intentionally vulnerable)."""
from flask import Flask, jsonify, request, send_file

import claims
import reports
import storage

app = Flask(__name__)


@app.route("/api/claims/search")
def search_claims():
    return jsonify(claims.find_by_holder(request.args.get("holder", "")))


@app.route("/api/claims/<claim_id>")
def get_claim(claim_id):
    return jsonify(claims.get(claim_id))


@app.route("/api/reports/export")
def export_report():
    path = reports.export_csv(request.args.get("format", "csv"), request.args.get("name", "claims"))
    return send_file(path)


@app.route("/api/reports/download")
def download_report():
    return send_file(reports.report_path(request.args.get("file", "")))


@app.route("/api/claims/import", methods=["POST"])
def import_claims():
    return jsonify(storage.load_snapshot(request.get_data()))


@app.route("/api/policy/upload", methods=["POST"])
def upload_policy():
    return jsonify(storage.load_policy(request.get_data(as_text=True)))
