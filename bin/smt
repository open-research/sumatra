#!/usr/bin/env python
"""
Command-line interface to the Sumatra computational experiment management tool.
"""

import sys
from sumatra import commands, __version__
from sumatra.versioncontrol.base import VersionControlError
from sumatra.recordstore.base import RecordStoreAccessError

usage = """Usage: smt <subcommand> [options] [args]

Simulation/analysis management tool version %s

Available subcommands:
  """ % __version__
usage += "\n  ".join(commands.modes)

if len(sys.argv) < 2:
    print(usage)
    sys.exit(1)

cmd = sys.argv[1]
try:
    main = getattr(commands, cmd)
except AttributeError:
    print(usage)
    sys.exit(1)

try:
    main(sys.argv[2:])
except (VersionControlError, RecordStoreAccessError) as err:
    print("Error: {}".format(err))
    sys.exit(1)
