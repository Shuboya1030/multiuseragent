"""Upload task documents to OwnCloud before the agent starts (runs inside the task container via /utils/init.sh)."""
import logging
import os
import requests
from requests.auth import HTTPBasicAuth
from config import OWNCLOUD_URL, OWNCLOUD_USERNAME, OWNCLOUD_PASSWORD

logging.basicConfig(level=logging.INFO)
AUTH = HTTPBasicAuth(OWNCLOUD_USERNAME, OWNCLOUD_PASSWORD)
DAV = f"{OWNCLOUD_URL}/remote.php/webdav"
SRC = "/utils/owncloud_docs"


def mkcol(path):
    r = requests.request("MKCOL", f"{DAV}/{path}", auth=AUTH)
    logging.info(f"MKCOL {path}: {r.status_code}")


def upload(local, remote):
    with open(local, "rb") as f:
        r = requests.put(f"{DAV}/{remote}", data=f, auth=AUTH)
    logging.info(f"PUT {remote}: {r.status_code}")
    r.raise_for_status()


if __name__ == "__main__":
    mkcol("Documents")
    mkcol("Documents/Procurement")
    for name in sorted(os.listdir(SRC)):
        upload(os.path.join(SRC, name), f"Documents/Procurement/{name}")
