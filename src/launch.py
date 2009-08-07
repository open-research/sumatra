


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
        

class SerialLaunchMode(LaunchMode):
    
    def __init__(self):
        LaunchMode.__init__(self)
        
    def __str__(self):
        return "serial"