import os


def config():
    return {"JWKS_URL": os.getenv("JWKS_URL"), "AUDIENCE": os.getenv("JWT_AUDIENCE")}
