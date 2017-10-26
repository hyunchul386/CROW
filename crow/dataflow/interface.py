import sqlite3, logging, time, abc, os
from datetime import datetime, timedelta
from sqlite3 import Cursor, Connection
from typing import Generator, Callable, List, Tuple, Any, Union, Dict, IO
from crow.tools import deliver_file
from crow.dataflow.sql import *

__all__=[ 'Dataflow', 'Slot', 'Message', 'InputSlot', 'InputMessage',
          'OutputSlot', 'OutputMessage' ]

_logger=logging.getLogger('crow.dataflow')
_ZERO_DT=timedelta(seconds=0)

class Slot(object):
    def __init__(self,con: Connection,pid: int,actor: str,slot: str,
                 flow: str,defloc: str) -> None:
        self._con, self._pid, self._flow = con, pid, flow
        self.actor, self.slot, self.defloc = actor, slot, defloc
        self.__meta=None # type: dict
    @property
    def flow(self): return self._flow
    def get_meta(self) -> dict:
        if self.__meta is None:
            self.__meta=get_meta(self._con,self._pid)
        return self.__meta
    def __str__(self):
        dir='output' if self._flow=='O' else 'input'
        return(f'{dir} actor={self.actor} slot={self.slot} '
               f'meta={self.get_meta()}')

class Message(Slot):
    def __init__(self,con: Connection,pid: int,actor: str,slot: str,
                 flow: str,cycle: datetime) -> None:
        super().__init__(con,pid,actor,slot,flow,None)
        self.cycle=cycle
        self.__location=None # type: str
    def _get_location(self) -> str:
        if self.__location is None:
            avail, self.__location=get_location(
                self._con,self._pid,self._flow,self.cycle)
        return self.__location
    _location=property(_get_location,None,None,
                       'Internal variable: data location on disk.')
    def set_data(self,location: str,avail: int) -> None:
        set_data(self._con,self._pid,self.cycle,location,1)
        self.__location=location
    def obtain(self,location: str) -> None:
        deliver_file(self._location,location)
    @abc.abstractmethod
    def open(self,mode: str,buffering: int=-1,encoding: str=None) -> IO:
        pass
    def __str__(self):
        return super().__str__()+f' @ {self.cycle:%Y%m%d%H%M}'
    
class InputMessage(Message):
    def open(self,mode: str,buffering: int=-1,encoding: str=None) -> IO:
        if mode[0] != 'r':
            raise TypeError(f'{mode}: cannot open an input slot for writing.')
        _logger.debug(f'{self._location}: open mode {mode}')
        return open(self._location,mode,buffering,encoding)

class OutputMessage(Message):
    def open(self,mode: str,buffering: int=-1,encoding: str=None) -> IO:
        parent=os.path.dirname(self._location)
        if parent and not os.path.exists(parent):
            _logger.debug(f'{parent}: makedirs')
            os.makedirs(parent)
        _logger.debug(f'{self._location}: open mode {mode}')
        return open(self._location,mode,buffering,encoding)
    def deliver(self,from_location: str,to_location: str=None) -> None:
        if to_location is None:
            to_location=self._location
        deliver_file(from_location,to_location)   # copy file to destination
        self.set_data(to_location,int(time.time())) # mark file as available

class OutputSlot(Slot):
    def at(self,cycle: datetime) -> OutputMessage:
        return OutputMessage(self._con,self._pid,self.actor,self.slot,
                             self._flow,cycle)

class InputSlot(Slot):
    def at(self,cycle: datetime) -> InputMessage:
        return InputMessage(self._con,self._pid,self.actor,self.slot,
                            self._flow,cycle)
    def connect_to(self,oslot: Slot,rel_time: timedelta=_ZERO_DT) -> None:
        if oslot._flow != 'O':
            raise TypeError(
                'Input slots can only be connected to output slots.')
        add_message(self._con,oslot._pid,self._pid,rel_time)

class Dataflow(object):
    def __init__(self,filename: str) -> None:
        self._con=sqlite3.connect(filename)
        self._con.isolation_level=None;
        create_tables(self._con)

    def add_output_slot(self,actor: str,slot: str,defloc: str,
                        meta: Dict[str,Any]=None) -> None:
        add_slot(self._con,actor,slot,'O',defloc,meta)

    def add_input_slot(self,actor: str,slot: str,meta: Dict[str,Any]=None) -> None:
        add_slot(self._con,actor,slot,'I',None,meta)

    def find_input_slot(self,actor: str=None,slot: str=None,
                        meta: Dict[str,Any]=None) -> Generator[InputSlot,None,None]:
        for pid,actor,slot,flow,defloc in itercur(select_slot(
                self._con,actor,slot,'I',meta)):
            yield InputSlot(self._con,pid,actor,slot,flow,defloc)

    def find_output_slot(self,actor: str=None,slot: str=None,
                         meta: Dict[str,Any]=None) -> Generator[OutputSlot,None,None]:
        for pid,actor,slot,flow,defloc in itercur(select_slot(
                self._con,actor,slot,'O',meta)):
            yield OutputSlot(self._con,pid,actor,slot,flow,defloc)

    def add_cycle(self,cycle: datetime) -> None:
        with transaction(self._con):
            add_cycle(self._con,cycle)

    def del_cycle(self,cycle: datetime) -> None:
        _logger.debug(f'{cycle:%Y-%m-%dt%H:%M:%S}: delete Data table '
                      'entries for cycle')
        del_cycle(self._con,cycle)

    def _dump(self,fd):
        for row in self._con.iterdump():
            fd.write(row+'\n')
