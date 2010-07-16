"""
The launch module handles launching of simulations/analyses as sub-processes, and
obtaining information about the platform(s) on which the simulations are run.

Classes
-------

PlatformInformation   - a container for platform information
SerialLaunchMode      - handles launching local, serial computations
DistributedLaunchMode - handles launching distributed computations using MPI
"""

import platform
import socket
import subprocess
import os
from sumatra.programs import Executable
import warnings

class PlatformInformation(object):
    """
    A simple container for information about the machine and environment the
    computations are being performed on/in.
    """
    
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
    #platform.mac_ver()
    #platform.win32_ver()
    #platform.dist()
    #platform.libc_ver()
    # Python compile options? distutils.sys_config?
    # some numpy information?
    # numpy.distutils.system_info import get_info
    # get_info('blas_opt')


def check_files_exist(executable_path, main_file, parameter_file):
    """
    Check that the given paths exist and return the list of paths.
    
    parameter_file may be None, in which case it is not included in the list of
    paths.
    """
    paths = [executable_path, main_file]
    if parameter_file:
        paths.append(parameter_file)
    for path in paths:
        if not os.path.exists(path):
            raise IOError("%s does not exist." % path)
    return paths


class LaunchMode(object):
    """
    Base class for launch modes (serial, distributed, batch, ...)
    """
    
    def get_state(self):
        """
        Since each subclass has different attributes, we provide this method
        as a standard way of obtaining these attributes, for database storage,
        etc. Returns a dict.
        """
        return {}
    
    def pre_run(self, executable):
        """Run tasks before the simulation/analysis proper.""" # e.g. nrnivmodl
        #should get the tasks to run from the Executable 
        pass

    def generate_command(self, paths):
        """Return a string containing the command to be launched."""
        raise NotImplementedError("must be impemented by sub-classes")

    def run(self, executable, main_file, parameter_file=None, append_label=None):
        """
        Run a computation in a shell, with the given executable, script and
        parameter file. If `append_label` is provided, it is appended to the
        command line. Return True if the computation finishes successfully,
        False otherwise.
        """
        cmd = self.generate_command(executable, main_file, parameter_file)
        if append_label:
            cmd += append_label
        print "Sumatra is running the following command:", cmd
        #p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        p = subprocess.Popen(cmd, shell=True, stdout=None, stderr=None, close_fds=True)
        result = p.wait()
        #self.errors = p.stderr.read()
        #self.output = p.stdout.read()
        #sys.stdout.write(self.output)
        #sys.stderr.write(self.errors)
        if result == 0:
            return True
        else:
            return False

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.get_state() == other.get_state()

    def __ne__(self, other):
        return not self.__eq__(other)

    def get_platform_information(self):
        """
        Return a list of `PlatformInformation` objects, containing information
        about the machine(s) and environment(s) the computations are being
        performed on/in. 
        """
        network_name = platform.node()
        bits, linkage = platform.architecture()
        return [PlatformInformation(architecture_bits=bits,
                                    architecture_linkage=linkage,
                                    machine=platform.machine(),
                                    network_name=network_name,
                                    ip_addr=socket.gethostbyname(network_name),
                                    processor=platform.processor(),
                                    release=platform.release(),
                                    system_name=platform.system(),
                                    version=platform.version())]
        # maybe add system time?


class SerialLaunchMode(LaunchMode):
    """
    Enable running serial computations.
    """
        
    def __str__(self):
        return "serial"
    
    def generate_command(self, executable, main_file, parameter_file):
        __doc__ = LaunchMode.__doc__
        paths = check_files_exist(executable.path, main_file, parameter_file)
        cmd = "%s "*len(paths) % tuple(paths)
        return cmd
    

class DistributedLaunchMode(LaunchMode):
    """
    Enable running distributed computations using MPI.
    
    The current implementation is specific to MPICH2, but this will be
    generalised in future releases.
    """
    
    def __init__(self, n, mpirun="mpiexec", hosts=[], pfi_path="/usr/local/bin/pfi.py"):
        """
        `n` - the number of hosts to run on.
        `mpirun` - the path to the mpirun or mpiexec executable. If a full path
                 is not given, the user's PATH will be searched.
        `hosts` - a list of host names to run on. **Currently not used.**
        `pfi_path` - the path to the pfi.py script provided with Sumatra, which
                     should be installed on every node and is used to obtain
                    platform information.
        """
        LaunchMode.__init__(self)
        class MPI(Executable):
            name = mpirun
            default_executable_name = mpirun
        if os.path.exists(mpirun): # mpirun is a full path
            mpi_cmd = MPI(path=mpirun)
        else:
            mpi_cmd = MPI(path=None)
        self.mpirun = mpi_cmd.path #"/usr/local/bin/mpiexec"
        self.hosts = hosts
        self.n = n
        self.mpi_info = {}
        self.pfi_path = pfi_path
    
    def __str__(self):
        return "distributed (n=%d, mpiexec=%s, hosts=%s)" % (self.n, self.mpirun, self.hosts)
    
    def generate_command(self, executable, main_file, parameter_file):
        __doc__ = LaunchMode.__doc__
        paths = check_files_exist(executable.path, main_file, parameter_file)
        if hasattr(executable, "mpi_flags"):
            paths.insert(1, executable.mpi_flags)
        #cmd = "%s -np %d -host %s %s %s %s" % (self.mpirun,
        #                                       self.n,
        #                                       ",".join(hosts),
        #                                       executable.path,
        #                                       main_file,
        #                                       parameter_file)
        cmd = "%s -n %d" % ( # MPICH2-specific - need to generalize
            self.mpirun,
            self.n
        )
        cmd += " %s"*len(paths) % tuple(paths)
        return cmd
    
    def get_platform_information(self):
        __doc__ = LaunchMode.__doc__ + """
        Requires the script pfi.py to be placed on the user's path on
        each node of the machine.
        
        This is currently not useful, as I don't think there is any guarantee
        that we get the same n nodes that the command is run on. Need to look
        more into this.
        """
        try:
            import mpi4py.MPI
            MPI = mpi4py.MPI
        except ImportError:
            MPI = None
            warnings.warn("mpi4py is not available, so Sumatra is not able to obtain platform information for remote nodes.")
            platform_information = LaunchMode.get_platform_information()
        if MPI:
            import sys
            comm = MPI.COMM_SELF.Spawn(sys.executable,
                                       args=[self.pfi_path],
                                       maxprocs=self.n)
            platform_information = []
            for rank in range(self.n):
                platform_information.append(PlatformInformation(**comm.recv(source=rank, tag=rank).values()[0]))
            comm.Disconnect()
        return platform_information

    def get_state(self):
        """Return a dict containing the values needed to recreate this instance."""
        return {'mpirun': self.mpirun, 'n': self.n, 'hosts': self.hosts}
    
