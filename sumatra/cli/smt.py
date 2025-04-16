"""
Command-line interfaces to the Sumatra computational experiment management tool.
"""

import sys
from sumatra import commands, __version__
from sumatra.versioncontrol.base import VersionControlError
from sumatra.recordstore.base import RecordStoreAccessError

usage = f"""Usage: smt <subcommand> [options] [args]

Simulation/analysis management tool version {__version__}

Available subcommands:
  """ + "\n  ".join(commands.modes)


def smt():

    if len(sys.argv) < 2:
        print(usage)
        return 1

    cmd = sys.argv[1]
    try:
        main = getattr(commands, cmd)
    except AttributeError:
        print(usage)
        return 1

    try:
        main(sys.argv[2:])
    except (VersionControlError, RecordStoreAccessError) as err:
        print("Error: {}".format(err))
        return 1
    else:
        return 0
