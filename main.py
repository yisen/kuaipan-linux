#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import threading
import hdnotify
import Queue


EVENT_QUEUE = Queue.Queue()


class HdNotify(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self._queue = queue
        
    def run(self):
        hdnotify.mainloop(self._queue)


class EventMonitor(threading.Thread):
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self._queue = queue
        
    def run(self):
        while True:
            event = self._queue.get()
#            self.eventHandler(event)
            print event
            self._queue.task_done()
            
    def eventHandler(self, raw_event):
        file, event = raw_event
        print "FILE: " + file + ", EVENT: " + event


def main():
    hd_notify = HdNotify(EVENT_QUEUE)
    event_monitor = EventMonitor(EVENT_QUEUE)
    
    hd_notify.start()
    event_monitor.start()
    
    hd_notify.join()
    event_monitor.join()
    EVENT_QUEUE.join()


if __name__ == '__main__':
    main()

