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

import requests
import time

HOST = os.environ["NEW_DECRYPT_SERVER"]

# push to server
ipa_abs_path = os.path.abspath(ipa_file)
r = requests.post(HOST + '/add_http_decrypt_task', json={
    'HTTPUrl': f"https://ghactions-tmp1.misty.moe/chfs/shared/{ipa_abs_path}",
    'HTTPMethod': 'GET',
    'StartOffset': 0,
    'FileSize': -1,
    'RemotePath': f'dropbox-misty:ios-decrypt/testdec-{int(time.time())}.tar',
})
taskret = r.json()
if taskret['status'] != 'ok':
    print("Failed to create task: ", taskret)

task_id = taskret['task_id']
task_queue = taskret['task_queue']
print("Got decrypt task: id %s queue %s" % (task_id, task_queue))

print("Waiting for task completion...")
while True:
    r = requests.post(HOST + '/get_task_data', json={
        'task_id': task_id,
        'task_queue': task_queue,
        'need_download': False,
    })
    ret = r.json()
    if ret['status'] == 'error':
        print("Failed to get task status: ", ret)
        break
    elif ret['status'] == 'pending':
        print("waiting for task finish...")
    elif ret['status'] == 'ok':
        print("success! ret: ", ret['decrypted_result'])
        savedPath = ret['decrypted_result']['SavedPath']
        savedSize = ret['decrypted_result']['SavedSize']
        r = requests.post(HOST + '/get_task_data', json={
            'task_id': task_id,
            'task_queue': task_queue,
            'need_download': True,
        })
        with open('dec.tar', 'wb') as f:
            f.write(r.content)
        assert len(r.content) == savedSize
        break

    time.sleep(10)