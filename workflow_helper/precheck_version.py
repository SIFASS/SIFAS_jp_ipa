import os
import subprocess
import json

def main(args):
    if os.path.exists('curver.txt'):
        with open('curver.txt') as f:
            ver = f.read()
        verOutput = subprocess.check_output("python3 ipatool-py/main.py --json lookup -c %s -b %s --get-verid" % (*args, ), shell=True)
        verInfo = json.loads(verOutput)
        appVer = verInfo['appVerId']
        if ver == appVer:
            return 1
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))