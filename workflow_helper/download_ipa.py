import os
import subprocess
import json

def main(args):
    verOutput = subprocess.check_output("python3 ipatool-py/main.py --json lookup -c '%s' -b '%s' download -e '%s' -p '%s'" % (*args, ), shell=True)
    verInfo = json.loads(verOutput)
    with open('curver.txt', 'w') as f:
        f.write("%s" % verInfo['downloadedVerId'])
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv[1:]))