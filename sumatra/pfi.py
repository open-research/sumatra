#!/usr/bin/env python
"""
Obtain platform information from every node of a cluster.

This script should be placed somewhere on the user's path.

:copyright: Copyright 2006-2014 by the Sumatra team, see doc/authors.txt
:license: CeCILL, see LICENSE for details.
"""
from __future__ import unicode_literals

from mpi4py import MPI
import platform
import socket
from datetime import datetime

TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"

MPI_ROOT = 0
comm = MPI.Comm.Get_parent()
rank = comm.Get_rank()

network_name = platform.node()
bits, linkage = platform.architecture()
platform_information = {
    network_name: dict(architecture_bits=bits,
                       architecture_linkage=linkage,
                       machine=platform.machine(),
                       network_name=network_name,
                       ip_addr=socket.gethostbyname(network_name),
                       processor=platform.processor(),
                       release=platform.release(),
                       system_name=platform.system(),
                       version=platform.version(),
                       clock=datetime.now().strftime(TIMESTAMP_FORMAT))
}

comm.send(platform_information, dest=MPI_ROOT, tag=rank)

comm.Disconnect()
