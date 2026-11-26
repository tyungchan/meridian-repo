import sqlite3

from config import DB_PATH


def _db():
    return sqlite3.connect(DB_PATH)


def find_by_holder(holder):
    db = _db()
    query = "SELECT id, holder, amount, status FROM claims WHERE holder LIKE '%" + holder + "%'"
    return db.execute(query).fetchall()


def get(claim_id):
    db = _db()
    return db.execute("SELECT * FROM claims WHERE id = %s" % claim_id).fetchone()
