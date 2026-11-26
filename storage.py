import pickle

import yaml


def load_snapshot(blob):
    data = pickle.loads(blob)
    return {"records": len(data)}


def load_policy(text):
    doc = yaml.load(text, Loader=yaml.Loader)
    return {"name": doc.get("name"), "rules": len(doc.get("rules", []))}
