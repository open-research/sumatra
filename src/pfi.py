#!/usr/bin/env python
"""
Obtain platform information from every node of a cluster.

This script should be placed somewhere on the user's path.
"""

from mpi4py import MPI
import platform
import socket
import time
from datetime import datetime

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
                       clock=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
}

comm.send(platform_information, dest=MPI_ROOT, tag=rank)

comm.Disconnect()
