import re
import os
import sys
import plistlib
import time

import requests
from io import BytesIO
from hashlib import sha256
from zipfile import ZipFile


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

    with ipa.open("Payload/{}.app/{}".format(app_name, binary_name), "r") as f:
        binary = f.read()

    sc_zip_io = BytesIO()
    with ZipFile(sc_zip_io, "w") as sc_zip:
        for i in ipa.filelist:
            r = re.search(r"^Payload/{}\.app/SC_Info/(.+?)$".format(app_name), i.filename)
            if r:
                with ipa.open(i.filename, "r") as f:
                    new_name = r.group(1).replace(binary_name, "binary")
                    with sc_zip.open(new_name, "w") as nf:
                        nf.write(f.read())
    sc_zip_io.seek(0)

# push to server
DECRYPT_SERVER = os.environ["DECRYPT_SERVER"]
DECRYPT_SERVER_TOKEN = os.environ["DECRYPT_SERVER_TOKEN"]
print("Uploading to server...")
r = requests.post("https://{}/submit".format(DECRYPT_SERVER), files={
    "token": DECRYPT_SERVER_TOKEN,
    "binary": binary,
    "sc_info": sc_zip_io.read(),
    "hash": sha256(binary).hexdigest()
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
with open(binary_name, "wb") as f:
    f.write(result.content)
print("All success.")
