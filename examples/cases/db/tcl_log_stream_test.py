from threading import Thread
from threading import Event
from thinkpi.flows import tasks
import time

if __name__ == '__main__':
    t = tasks.TasksBase()
    event = Event()
    thread = Thread(target=t.stream_log, args=(event, r'D:\jrosenfe\ThinkPI\applications.design-automation.power.think-pi\tcl.tcl'))
    thread.start()
    #t.stream_log(r'D:\jrosenfe\ThinkPI\applications.design-automation.power.think-pi\tcl.tcl')
    time.sleep(60)
    event.set()
    thread.join()

    