import re
import os
import sys
import plistlib
import time

import requests
from io import BytesIO
from hashlib import sha256
from zipfile import ZipFile, Path


ipa_file = sys.argv[1]
with ZipFile(ipa_file, 'r') as ipa:
    app_name = None
    for i in ipa.filelist:
        r = re.search(r"^Payload/(.+?)\.app/$", i.filename)
        if r:
            app_name = r.group(1)
            break
    if not app_name:
        raise Exception("*.app folder not found in ipa!")
        
    with ipa.open("Payload/{}.app/Info.plist".format(app_name), "r") as f:
        info_plist = plistlib.load(f)
        binary_name = info_plist["CFBundleExecutable"]
        identifier = info_plist["CFBundleIdentifier"]

    with ipa.open("Payload/{}.app/{}".format(app_name, binary_name), "r") as f:
        binary = f.read()

    
    ipazip_io = BytesIO()
    with ZipFile(ipazip_io, "w") as ipazip:
        def addfile(fn):
            with ipa.open(fn, "r") as f:
                with ipazip.open(fn, "w") as nf:
                    nf.write(f.read())
        addfile("Payload/{}.app/Info.plist".format(app_name))
        addfile("Payload/{}.app/{}".format(app_name, binary_name))
        for path in Path(ipa, "Payload/{}.app/SC_Info/".format(app_name)).iterdir():
            addfile(path.at)

    bundleID = "{}/{}.app/{}".format(identifier, app_name, binary_name)

# push to server
DECRYPT_SERVER = os.environ["DECRYPT_SERVER"]
DECRYPT_SERVER_TOKEN = os.environ["DECRYPT_SERVER_TOKEN"]
print("Uploading to server...")
r = requests.post("https://{}/submit".format(DECRYPT_SERVER), files={
    "token": DECRYPT_SERVER_TOKEN,
    "binary": ipazip_io.getvalue(),
    "sc_info": bundleID,
    "hash": sha256(ipazip_io.getbuffer()).hexdigest()
})
print(r)
task_id = int(r.text)
assert r.status_code == 200

# wait for result
result_url = "https://{}/upload/{}/decrypted".format(DECRYPT_SERVER, task_id)
while requests.head(result_url).status_code == 404:
    print("Waiting for decryption...")
    time.sleep(10)

print("Downloading decrypted binary...")
result = requests.get(result_url)
assert result.status_code == 200
if result.content.startswith(b"error"):
    print("Decryption Error: %s" % result.text)
    sys.exit(1)
with open(binary_name, "wb") as f:
    f.write(result.content)
print("All success.")
