from pathlib import Path
from urllib.parse import quote
import requests
from config import OWNCLOUD_URL, OWNCLOUD_USERNAME, OWNCLOUD_PASSWORD
s=requests.Session();s.auth=(OWNCLOUD_USERNAME,OWNCLOUD_PASSWORD)
base=OWNCLOUD_URL+'/remote.php/webdav/'
parts=['Documents','Study21','SecureScan']
for n in range(1,len(parts)+1):
    r=s.request('MKCOL',base+'/'.join(parts[:n]),timeout=30)
    if r.status_code not in (201,405):r.raise_for_status()
for p in sorted(Path('/utils/task_documents').glob('*.md')):
    r=s.put(base+'/'.join(parts)+'/'+quote(p.name),data=p.read_bytes(),timeout=30);r.raise_for_status()

