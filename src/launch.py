


class LaunchMode(object):
    """
    Launch serially or in parallel with MPI.
    If MPI store configuration (which nodes, etc)
    """
    pass


class SerialLaunchMode(object):
    
    def __init__(self):
        LaunchMode.__init__(self)
        
    def __str__(self):
        return "serial"