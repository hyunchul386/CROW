import itertools
from io import StringIO

from crow.sysenv.exceptions import *
from crow.sysenv.util import ranks_to_nodes_ppn
from crow.sysenv.spec import JobResourceSpec

#from crow.sysenv.parallelisms.base import Parallelism as BaseParallelism

from collections import Sequence

__all__=['Parallelism']

class Parallelism(object):  # (BaseParallelism):
    def __init__(self,settings):
        self.settings=dict(settings)
        self.cores_per_node=int(settings['physical_cores_per_node'])
        self.cpus_per_core=int(settings.get('logical_cpus_per_core',1))
        self.hyperthreading_allowed=bool(
            settings.get('hyperthreading_allowed',False))
        self.parallelism='HydraIMPI'
        self.indent_text=str(settings.get('indent_text','  '))

    def make_sh_command_to_launch(self,spec):
        pass
    
