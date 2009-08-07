import sys
import os.path

vcs_list = []

for vcs in ['mercurial', 'subversion']:
    try:
        __import__('sumatra.versioncontrol._%s' % vcs)
        vcs_list.append(sys.modules['sumatra.versioncontrol._%s' % vcs])
    except ImportError:
        pass
    
            
def get_working_copy():
    for vcs in vcs_list:
        if vcs.may_have_working_copy():
            return vcs.get_working_copy()
    return None
            
def get_repository(url):
    if url:
        repos = None
        for vcs in vcs_list:
            print vcs, url
            try:
                repos =  vcs.get_repository(url)
                break
            except Exception, e:
                print e
        if repos is None:
            raise Exception("Can't find repository at URL '%s'" % url)
        else:
            return repos
    else:
        working_copy = get_working_copy()
        if working_copy:
            return working_copy.repository
        else:
            return None