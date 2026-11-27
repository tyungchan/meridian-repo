"""Meridian Corp claims service (demo repository, intentionally vulnerable)."""
import json
import os
import re

import yaml
from flask import Flask, abort, jsonify, request, send_file, session

import claims
import reports
import storage

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MiB request body limit

_HOLDER_RE = re.compile(r"^[A-Za-z0-9 .,'@_-]{1,128}$")
_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_REPORT_FILE_RE = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9_.-]{0,127}$")
_ALLOWED_FORMATS = frozenset({"csv"})
# Roles explicitly granted access to report export/download (deny by default).
_REPORT_ROLES = frozenset({"admin", "reports"})


def _current_user():
    """Return the authenticated user id from the server-side session, or None."""
    return session.get("user_id")


def _require_user():
    """Abort with 401 unless the request carries an authenticated session."""
    user = _current_user()
    if user is None:
        abort(401)
    return user


def _require_report_access():
    """Require an authenticated user holding an explicitly allowed report role."""
    user = _require_user()
    role = session.get("role")
    if role not in _REPORT_ROLES:
        abort(403)
    return user


def _claim_owner(claim):
    if isinstance(claim, dict):
        for key in ("owner_id", "user_id", "holder_id", "holder"):
            if key in claim:
                return claim[key]
    return getattr(claim, "owner_id", None)


@app.route("/api/claims/search")
def search_claims():
    user = _require_user()
    holder = request.args.get("holder", "")
    if not _HOLDER_RE.fullmatch(holder):
        abort(400, description="Invalid holder parameter.")
    results = claims.find_by_holder(holder) or []
    # Scope results to claims owned by the authenticated user.
    owned = [c for c in results if str(_claim_owner(c)) == str(user)]
    return jsonify(owned)


@app.route("/api/claims/<claim_id>")
def get_claim(claim_id):
    user = _current_user()
    if user is None:
        abort(401)
    claim = claims.get(claim_id)
    # Deny by default: return a generic 404 when the claim is missing or not owned.
    if claim is None or str(_claim_owner(claim)) != str(user):
        abort(404)
    return jsonify(claim)


@app.route("/api/reports/export")
def export_report():
    _require_report_access()
    fmt = request.args.get("format", "csv")
    name = request.args.get("name", "claims")
    if fmt not in _ALLOWED_FORMATS:
        abort(400, description="Unsupported format.")
    if not _NAME_RE.fullmatch(name):
        abort(400, description="Invalid report name.")
    path = reports.export_csv(fmt, name)
    return send_file(path)


@app.route("/api/reports/download")
def download_report():
    _require_report_access()
    filename = request.args.get("file", "")
    if (
        not _REPORT_FILE_RE.fullmatch(filename)
        or ".." in filename
        or os.path.basename(filename) != filename
    ):
        abort(400, description="Invalid file name.")
    path = reports.report_path(filename)
    base_dir = getattr(reports, "REPORTS_DIR", None)
    resolved = os.path.realpath(path)
    if base_dir is not None:
        base_resolved = os.path.realpath(base_dir)
        if os.path.commonpath([resolved, base_resolved]) != base_resolved:
            abort(404)
    if not os.path.isfile(resolved):
        abort(404)
    return send_file(resolved)


@app.route("/api/claims/import", methods=["POST"])
def import_claims():
    # Never unpickle untrusted data; accept JSON only.
    try:
        data = json.loads(request.get_data(as_text=True))
    except (ValueError, UnicodeDecodeError):
        abort(400, description="Invalid JSON payload.")
    return jsonify(data)


@app.route("/api/policy/upload", methods=["POST"])
def upload_policy():
    # Use the safe YAML loader to prevent arbitrary object construction.
    try:
        policy = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        abort(400, description="Invalid YAML payload.")
    return jsonify(policy)
