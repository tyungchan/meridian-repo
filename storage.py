import json

import yaml


def load_snapshot(blob):
    # Never unpickle untrusted data; parse as JSON instead (data only, no code execution).
    if isinstance(blob, (bytes, bytearray)):
        blob = blob.decode("utf-8")
    data = json.loads(blob)
    if not isinstance(data, (list, dict)):
        raise ValueError("Snapshot must be a JSON array or object")
    return {"records": len(data)}


def load_policy(text):
    # safe_load only constructs plain YAML types (no arbitrary Python objects).
    doc = yaml.safe_load(text)
    if not isinstance(doc, dict):
        raise ValueError("Policy document must be a mapping")
    rules = doc.get("rules", [])
    if rules is None:
        rules = []
    if not isinstance(rules, list):
        raise ValueError("Policy 'rules' must be a list")
    return {"name": doc.get("name"), "rules": len(rules)}
