"""
Helper tools for unit tests
"""
from builtins import object

class patch(object):
    """
    Decorator for replacing a function or class by a mock version for the
    duration of a test, then replacing the original afterwards.
    """
    
    def __init__(self, module, obj_name, mock_obj):
        self.module = module
        self.obj_name = obj_name
        self.mock_obj = mock_obj
        self.orig_obj = getattr(module, obj_name)
        
    def __call__(self, f):
        def wrapped_f(*args, **kwargs):
            setattr(self.module, self.obj_name, self.mock_obj)
            f(*args, **kwargs)
            setattr(self.module, self.obj_name, self.orig_obj)
        wrapped_f.__name__ = f.__name__
        return wrapped_f
