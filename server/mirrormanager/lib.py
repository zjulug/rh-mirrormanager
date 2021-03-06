import os
import subprocess
import sys
import tempfile
import traceback
import types
from turbogears import config

def createErrorString(tg_errors):
    """
        Creates and returns an string representation of tg_errors
        tg_errors(list): List of turbogears generated errors
    """
    errors = []
    if type(tg_errors) == types.DictType:

        for param, inv in tg_errors.items():
            if type(inv) == types.StringType or type(inv) == types.UnicodeType:
                errors.append("%s: %s"%(param, inv))
            else:
                errors.append("%s(%s): %s"%(param, inv.value, inv.msg))
    else:
        errors.append(tg_errors)
    
    return "Error:" + ", ".join(errors)

def uniqueify(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

def remove_pidfile(pidfile):
    os.unlink(pidfile)

def create_pidfile_dir(pidfile):
    piddir = os.path.dirname(pidfile)
    try:
        os.makedirs(piddir, mode=0755)
    except OSError, err:
        if err.errno == 17: # File exists
            pass
        else:
            raise
    except:
        raise

def write_pidfile(pidfile, pid):
    create_pidfile_dir(pidfile)
    f = open(pidfile, 'w')
    f.write(str(pid)+'\n')
    f.close()
    return 0

def manage_pidfile(pidfile):
    """returns 1 if another process is running that is named in pidfile,
    otherwise creates/writes pidfile and returns 0."""
    pid = os.getpid()
    try:
        f = open(pidfile, 'r')
    except IOError, err:
        if err.errno == 2: # No such file or directory
            return write_pidfile(pidfile, pid)
        return 1

    oldpid=f.read()
    f.close()

    # is the oldpid process still running?
    try:
        os.kill(int(oldpid), 0)
    except ValueError: # malformed oldpid
        return write_pidfile(pidfile, pid)
    except OSError, err:
        if err.errno == 3: # No such process
            return write_pidfile(pidfile, pid)
    return 1

def append_value_to_cache(cache, key, value):
    if key not in cache:
        cache[key] = [value]
    else:
        cache[key].append(value)
    return cache

def run_rsync(rsyncpath, extra_rsync_args=None):
    tmpfile = tempfile.SpooledTemporaryFile()
    cmd = "rsync --temp-dir=/tmp -r --exclude=.snapshot --exclude='*.~tmp~'"
    if extra_rsync_args is not None:
        cmd += ' ' + extra_rsync_args
    cmd += ' ' + rsyncpath
    devnull = open('/dev/null', 'r+')
    p = subprocess.Popen(cmd, shell=True, stdin=devnull,
                         stdout=tmpfile, stderr=devnull, close_fds=True, bufsize=-1)
    p.wait()
    result = p.returncode
    tmpfile.flush()
    tmpfile.seek(0)
    return (result, tmpfile)


def project_template(formname):
    project = config.get("mirrormanager.project_template", "fedora")
    template = "mirrormanager.templates.%s.%s" % (project, formname)
    return template

def project_dict(formname, template_engine="kid", **kw):
    d = dict()
    template = project_template(formname)
    d['tg_template'] = "%s:%s" % (template_engine, template)
    d.update(**kw)
    return d

def parent_dir(path):
    sdir = path.split('/')[:-1]
    try:
        parent = os.path.join(*sdir)
    except TypeError: # 
        parent = u''
    return parent
