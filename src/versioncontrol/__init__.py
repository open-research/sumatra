import sys
import os.path

vcs_list = []

for vcs in ['mercurial', 'subversion']:
    try:
        __import__('versioncontrol.%s' % vcs)
        vcs_list.append(sys.modules['versioncontrol.%s' % vcs])
    except ImportError:
        pass
    
            
def get_working_copy():
    for vcs in vcs_list:
        if vcs.may_have_working_copy():
            return vcs.get_working_copy()
    return None
            
def get_repository(url):
    if url:
        for vcs in vcs_list:
            try:
                repos =  vcs.get_repository(url)
                break
            except Exception:
                pass
        return repos
    else:
        working_copy = get_working_copy()
        if working_copy:
            return working_copy.repository
        else:
            return None