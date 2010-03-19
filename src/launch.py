"""
The launch module handles launching of simulations as sub-processes, and
obtaining information about the platform(s) on which the simulations are run.

Classes
-------

PlatformInformation   - a container for platform information
SerialLaunchMode      - handles launching local, serial simulations
DistributedLaunchMode - handles launching distributed simulations using MPI
"""

import platform
import socket
import subprocess
import os
from sumatra.programs import Executable


class PlatformInformation(object):
    
    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
    #platform.mac_ver()
    #platform.win32_ver()
    #platform.dist()
    #platform.libc_ver()


def check_files_exist(executable, main_file, parameter_file):
    paths = [executable.path, main_file]
    if parameter_file:
        paths.append(parameter_file)
    for path in paths:
        if not os.path.exists(path):
            raise IOError("%s does not exist." % path)
    return paths


class LaunchMode(object):
    """
    Launch serially or in parallel with MPI.
    If MPI store configuration (which nodes, etc)
    """
    
    def get_state(self):
        """
        Since each subclass has different attributes, we provide this method
        as a standard way of obtaining these attributes, for database storage,
        etc. Returns a dict.
        """
        return {}
    
    def pre_run(self, executable):
        #Run tasks before the simulation proper, e.g. nrnivmodl
        #should get the tasks to run from the Executable 
        pass

    def generate_command(self, paths):
        raise NotImplementedError("must be impemented by sub-classes")

    def run(self, executable, main_file, parameter_file=None):
        paths = check_files_exist(executable, main_file, parameter_file)
        cmd = self.generate_command(paths)
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


class SerialLaunchMode(LaunchMode):
    
    def __init__(self):
        LaunchMode.__init__(self)
        
    def __str__(self):
        return "serial"
    
    def generate_command(self, paths):
        cmd = "%s "*len(paths) % tuple(paths)
        return cmd
    
    def get_platform_information(self):
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


class DistributedLaunchMode(LaunchMode):
    
    def __init__(self, n, mpirun="mpiexec", hosts=[]):
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
    
    def __str__(self):
        return "distributed (n=%d, mpiexec=%s, hosts=%s)" % (self.n, self.mpirun, self.hosts)
    
    def generate_command(self, paths):
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
        return []

    def get_state(self):
        return {'mpirun': self.mpirun, 'n': self.n, 'hosts': self.hosts}
    