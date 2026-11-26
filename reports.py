import os
import subprocess

REPORT_DIR = "/var/meridian/reports"


def export_csv(fmt, name):
    out = os.path.join(REPORT_DIR, name + "." + fmt)
    subprocess.call("sqlite3 -csv claims.db 'select * from claims' > " + out + " && gzip -f " + out, shell=True)
    return out + ".gz"


def report_path(filename):
    return os.path.join(REPORT_DIR, filename)
