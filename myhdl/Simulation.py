""" Module with the Simulation class """
from __future__ import generators
import _simulator as sim
from _simulator import _siglist, _futureEvents
from Signal import Signal, _SignalWrap, _WaiterList
from delay import delay
from types import GeneratorType
import exceptions

schedule = _futureEvents.append
            
class Simulation:

    def __init__(self, *args):
        sim._time = 0
        self._waiters = _flatten(*args)
        del _futureEvents[:]
        del _siglist[:]

    def run(self, duration=None, quiet=0):
        waiters = self._waiters
        maxTime = None
        if duration:
            stop = _Waiter(None)
            stop.hasRun = 1
            maxTime = sim._time + duration
            schedule((maxTime, stop))
            
        t = sim._time
        while 1:
            try:
                for s in _siglist:
                    waiters.extend(s._update())
                del _siglist[:]
                
                while waiters:
                    waiter = waiters.pop(0)
                    if waiter.hasRun or not waiter.hasGreenLight():
                        continue
                    try:
                        clauses, clone = waiter.next()
                    except StopIteration:
                        if waiter.caller:
                            waiters.append(waiter.caller)
                        continue
                    for clause in clauses:
                        if type(clause) is _WaiterList:
                            clause.append(clone)
                        elif isinstance(clause, Signal):
                            clause._eventWaiters.append(clone)
                        elif type(clause) is delay:
                            schedule((t + clause._time, clone))
                        elif type(clause) is GeneratorType:
                            waiters.append(_Waiter(clause, clone))
                        elif type(clause) is join:
                            waiters.append(_Waiter(clause._generator(), clone))
                        else:
                            raise TypeError, "Incorrect yield clause type"

                if _siglist: continue
                if t == maxTime:
                    raise StopSimulation, "Simulated for duration %s" % duration

                if _futureEvents:
                    _futureEvents.sort()
                    t = sim._time = _futureEvents[0][0]
                    while _futureEvents:
                        newt, event = _futureEvents[0]
                        if newt == t:
                            if type(event) is _Waiter:
                                waiters.append(event)
                            else:
                                waiters.extend(event.apply())
                            del _futureEvents[0]
                        else:
                            break
                else:
                    raise StopSimulation, "No more events"
                
            except StopSimulation, e:
                if not quiet:
                    print "StopSimulation: %s" % e
                if _futureEvents:
                    return 1
                return 0
                
 
def _flatten(*args):
    res = []
    for arg in args:
        if type(arg) is GeneratorType:
            res.append(_Waiter(arg))
        else:
            for item in arg:
                res.extend(_flatten(item))
    return res


class _Waiter(object):
    
    def __init__(self, generator, caller=None, semaphore=None):
        self.generator = generator
        self.hasRun = 0
        self.caller = caller
        self.semaphore = None
        
    def next(self):
        self.hasRun = 1
        clone = _Waiter(self.generator, self.caller, self.semaphore)
        clause = self.generator.next()
        if type(clause) is tuple:
            return clause, clone
        elif type(clause) is join:
            n = len(clause._args)
            clone.semaphore = _Semaphore(n)
            return clause._args, clone
        else:
            return (clause,), clone
    
    def hasGreenLight(self):
        if self.semaphore:
            self.semaphore.val -= 1
            if self.semaphore.val != 0:
                return 0
        return 1
    
    def clone(self):
        return _Waiter(self.generator, self.caller, self.semaphore)
    
        
class _Semaphore(object):
    def __init__(self, val=1):
        self.val = val
        
class StopSimulation(exceptions.Exception):
    pass

class join(object):
    
    def __init__(self, *args):
        self._args = args
        
    def _generator(self):
        yield join(*self._args)
        