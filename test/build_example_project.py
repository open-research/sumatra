from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
import sys, os
from .smt_test import run_test

if __name__ == "__main__":
    vcs = sys.argv[1]
    path = sys.argv[2]
    print(vcs, path)
    if os.path.exists(path):
        print("%s already exists. Please delete it before running this command again." % path)
    else:
        run_test("_"+vcs, {}, path, path)