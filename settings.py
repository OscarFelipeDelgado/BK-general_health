import os

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "bk-general-health.onrender.com",
]

RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)