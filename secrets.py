import json
import os

# differentiates between REPL-IT secrets and local system
ON_REPLIT = False


def secret(key: str):
    if not ON_REPLIT:
        # local way of saving environmental variables

        with open("secrets.json", "r") as r:
            _SECRETS = json.load(r)

        if key not in _SECRETS:
            raise Exception(f"Unknown key: {key}.")

        return _SECRETS[key]
    else:
        # repl-it way of getting environmental variables
        return os.getenv(key)
