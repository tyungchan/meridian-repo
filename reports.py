import os
import re
import subprocess

REPORT_DIR = "/var/meridian/reports"

_ALLOWED_FORMATS = {"csv"}
_SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,127}$")


def _safe_join(base, filename):
    """Join filename to base and ensure the result stays inside base."""
    if not isinstance(filename, str) or not filename or "\x00" in filename:
        raise ValueError("Invalid filename")
    base_real = os.path.realpath(base)
    candidate = os.path.realpath(os.path.join(base_real, filename))
    if os.path.commonpath([base_real, candidate]) != base_real or candidate == base_real:
        raise ValueError("Invalid filename")
    return candidate


def export_csv(fmt, name):
    if fmt not in _ALLOWED_FORMATS:
        raise ValueError("Unsupported format")
    if not isinstance(name, str) or not _SAFE_NAME_RE.fullmatch(name):
        raise ValueError("Invalid report name")
    out = _safe_join(REPORT_DIR, name + "." + fmt)
    with open(out, "wb") as fh:
        subprocess.run(
            ["sqlite3", "-csv", "claims.db", "select * from claims"],
            stdout=fh,
            check=True,
        )
    subprocess.run(["gzip", "-f", "--", out], check=True)
    return out + ".gz"


def report_path(filename):
    return _safe_join(REPORT_DIR, filename)
