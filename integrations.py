import requests


def fetch_provider_status(url):
    return requests.get(url, timeout=5).text


def evaluate_rule(expression, claim):
    return eval(expression, {"claim": claim})
