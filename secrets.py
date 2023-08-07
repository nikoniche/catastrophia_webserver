import json

with open("secrets.json", "r") as r:
    _SECRETS = json.load(r)


def secret(key: str):
    if key not in _SECRETS:
        raise Exception(f"Unknown key: {key}.")

    return _SECRETS[key]