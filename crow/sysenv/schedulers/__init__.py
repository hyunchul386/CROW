from crow.sysenv.exceptions import UnknownSchedulerError
from crow.sysenv.schedulers.MoabTorque import Scheduler as MoabTorqueScheduler

KNOWN_SCHEDULERS={
    'MoabTorque': MoabTorqueScheduler
    }

def get_scheduler(name,settings):
    if name not in KNOWN_SCHEDULERS:
        raise UnknownSchedulerError(name)
    cls=KNOWN_SCHEDULERS[name]
    return cls(settings)

def has_scheduler(name):
    return name in KNOWN_SCHEDULERS
