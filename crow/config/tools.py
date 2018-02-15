import crow.tools
import os.path
import os
import re
import datetime
from collections import Sequence, Mapping
from crow.config.exceptions import *
from crow.tools import typecheck
import crow.sysenv

class Environment(dict):
    def __getattr__(self,key):
        if key in self: return self[key]
        raise AttributeError(key)

ENV=Environment(os.environ)

def strftime(d,fmt): return d.strftime(fmt)
def strptime(d,fmt): return datetime.datetime.strptime(d,fmt)
def to_YMDH(d): return d.strftime('%Y%m%d%H')
def to_YMD(d): return d.strftime('%Y%m%d')
def from_YMDH(d): return datetime.datetime.strptime(d,'%Y%m%d%H')
def from_YMD(d): return datetime.datetime.strptime(d,'%Y%m%d')
def join(L,J): return J.join([str(i) for i in L])
def seq(start,end,step):
    return [ r for r in range(start,end+1,step) ]

def fort(value,scope='scope'):
    """!Convenience function to convert a python object to a syntax valid
    in fortran namelists.    """
    if isinstance(value,str):
        return repr(value)
    elif isinstance(value,Sequence):
        # For sequences, convert to a namelist list.
        result=[]
        for item in value:
            assert(item is not value)
            fortitem=fort(item,scope)
            result.append(fortitem)
        return ", ".join(result)
    elif isinstance(value,Mapping):
        # For mappings, assume a derived type.
        subscope_keys=[ (f'{scope}%{key}',value) for key in value ]
        return ', '.join([f'{k}={fort(v,k)}' for (k,v) in subscope_keys])
    elif value is True or value is False:
        # Booleans get a "." around them:
        return '.'+str(bool(value))+'.'
    elif isinstance(value,float):
        return '%.12g'%value
    else:
        # Anything else is converted to a string.
        return str(value)

def seconds(dt):
    if not isinstance(dt,datetime.timedelta):
        raise TypeError(f'dt must be a timedelta not a {type(dt).__name__}')
    return dt.total_seconds()

def crow_install_dir(rel=None):
    path=os.path.dirname(__file__)
    path=os.path.join(path,'../..')
    if rel:
        path=os.path.join(path,rel)
    return os.path.abspath(path)

MISSING=object()
def env(var,default=MISSING):
    if default is MISSING:
        return os.environ[var]
    return os.environ.get(var,default)

def have_env(var): return var in os.environ

def command_without_exe(parallelism,jobspec,exe):
    typecheck('jobspec',jobspec,crow.sysenv.JobResourceSpec)
    shell_command_obj=parallelism.make_ShellCommand(jobspec)
    cmd=list(shell_command_obj.command)
    return ' '.join( [ s for s in cmd if s!=exe ] )

def indent(prefix,text):
    """!Given a multiline string, return a new multiline string with the
    given prefix prepended to each line.    """
    return '\n'.join([prefix+L for L in text.splitlines()])

def expand(string,**kwargs):
    return eval(f"f'''{string}'''",{},kwargs)

## The CONFIG_TOOLS contains the tools available to configuration yaml
## "!calc" expressions in their "tools" variable.
CONFIG_TOOLS=crow.tools.ImmutableMapping({
    'fort':fort,
    'seq':seq,
    'expand':expand,
    'crow_install_dir':crow_install_dir,
    'to_upper':(lambda s: s.upper()),
    'to_lower':(lambda s: s.lower()),
    'panasas_gb':crow.tools.panasas_gb,
    'gpfs_gb':crow.tools.gpfs_gb,
    'basename':os.path.basename,
    'dirname':os.path.dirname,
    'abspath':os.path.abspath,
    'realpath':os.path.realpath,
    'isdir':os.path.isdir,
    'isfile':os.path.isfile,
    'env':env,
    'have_env':have_env,
    'islink':os.path.islink,
    'exists':os.path.exists,
    'strftime':strftime,
    'strptime':strptime,
    'to_timedelta':crow.tools.to_timedelta,
    'as_seconds':seconds,
    'to_YMDH':to_YMDH, 'from_YMDH':from_YMDH,
    'to_YMD':to_YMD, 'from_YMD':from_YMD,
    'grep':re.search,
    'join':join,
    'get_parallelism':crow.sysenv.get_parallelism, 
    'get_scheduler':crow.sysenv.get_scheduler,
    'node_tool_for':crow.sysenv.node_tool_for,
    'command_without_exe':command_without_exe,
    'indent':indent,
})
