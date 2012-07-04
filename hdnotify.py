#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import pyinotify
import os
import sys
import Queue
import threading


EVENT_TYPE = {
    'IN_ACCESS'        : 0x00000001,  # File was accessed
    'IN_MODIFY'        : 0x00000002,  # File was modified
    'IN_ATTRIB'        : 0x00000004,  # Metadata changed
    'IN_CLOSE_WRITE'   : 0x00000008,  # Writable file was closed
    'IN_CLOSE_NOWRITE' : 0x00000010,  # Unwritable file closed
    'IN_OPEN'          : 0x00000020,  # File was opened
    'IN_MOVED_FROM'    : 0x00000040,  # File was moved from X
    'IN_MOVED_TO'      : 0x00000080,  # File was moved to Y
    'IN_CREATE'        : 0x00000100,  # Subfile was created
    'IN_DELETE'        : 0x00000200,  # Subfile was deleted
    'IN_DELETE_SELF'   : 0x00000400,  # Self (watched item itself)
    'IN_MOVE_SELF'     : 0x00000800,  # Self (watched item itself) was moved
    'IN_ISDIR'         : 0x40000000,  # event occurred against dir
    'IN_CREATE_ISDIR'  : 0x40000000 | 0x00000100,
    'IN_DELETE_ISDIR'  : 0x40000000 | 0x00000200,
}


class GetEvents(pyinotify.ProcessEvent):
    """
    Dummy class used to print events strings representations. For instance this
    class is used from command line to print all received events to stdout.
    """
    def my_init(self, out=None, queue=None, file_filter=None, config=None):
        """
        @param out: Where events will be written.
        @type out: Object providing a valid file object interface.
        """
        monitor_event = ['IN_CREATE_ISDIR', 'IN_DELETE_ISDIR', 'IN_MODIFY', 'IN_DELETE', 'IN_MOVED_FROM', 'IN_MOVED_TO']
        self.monitor_event = []
        for event in monitor_event:
            if event in EVENT_TYPE.keys():
                self.monitor_event.append(EVENT_TYPE[event])
        
        if out is None:
            out = open(os.devnull, 'w')
        self._out = out
        
        if file_filter:
            self._filter = file_filter
        
        if queue is None:
            print "No Event Queue!"
        self._event_queue = queue
        
        if config:
            self.config = config
        self.moved_list = []

    def handle_event_type(self, maskname):
        event_dict = {
            'IN_MODIFY': 'UPLOAD',
            'IN_DELETE': 'DELETE',
            'IN_CREATE|IN_ISDIR': 'CREATE',
            'IN_DELETE|IN_ISDIR': 'DELETE',
        }
        return event_dict[maskname]

    def process_default(self, event):
        """
        Writes event string representation to file object provided to
        my_init().

        @param event: Event to be processed. Can be of any type of events but
                      IN_Q_OVERFLOW events (see method process_IN_Q_OVERFLOW).
        @type event: Event instance
        """
        if self._filter.do_filter(event.pathname):
            root = self.config['root_path']
            pathname = event.pathname[len(root) + 1:]
            if event.mask in self.monitor_event:
                if event.maskname == 'IN_MOVED_FROM':
                    self.moved_list = []
                    self.moved_list.append(pathname)
                    return 
                if event.maskname == 'IN_MOVED_TO':
                    self.moved_list.append(pathname)
                    if len(self.moved_list) != 2:
                        raise Exception
                    self._event_queue.put((tuple(self.moved_list), 'MOVE'))
                    return
                    
                self._event_queue.put((pathname, self.handle_event_type(event.maskname)))
                self._out.write("FILE: " + pathname + ", EVENT: " + event.maskname)
        #        self._out.write(str(event))
                self._out.write('\n')
                self._out.flush()


class FileFilter():
    def __init__(self):
        self.filter_list = []
    
    def set_filter(self, filter_str):
        self.filter_list = filter_str.split('|')

    def do_filter(self, file_name):
        for filter_item in self.filter_list:
            filter_len = len(filter_item)
            if file_name[-filter_len:] == filter_item:
                return False
            else:
                continue
        return file_name


def mainloop(configure, queue):
    wm = pyinotify.WatchManager()
    file_filter = FileFilter()
    file_filter.set_filter(configure['filter_list'])
    
#    mask = pyinotify.ALL_EVENTS
    mask = 0
    monitor_event = ['IN_CREATE', 'IN_MODIFY', 'IN_DELETE', 'IN_ISDIR', 'IN_MOVED_FROM', 'IN_MOVED_TO']
    for event in monitor_event:
        if event in EVENT_TYPE.keys():
            mask |= EVENT_TYPE[event]

    notifier = pyinotify.Notifier(wm, default_proc_fun=GetEvents(config=configure, queue=queue, file_filter=file_filter))
    
    wm.add_watch(configure['root_path'], mask, rec=True, auto_add=True)
    notifier.loop()


class MonitorLocaleFolder(threading.Thread):
    def __init__(self, configure, queue):
        threading.Thread.__init__(self)
        self.configure = configure
        self.queue = queue
        
    def run(self):
        mainloop(self.configure, self.queue)
    

if __name__ == '__main__':
    task_queue = Queue.Queue()
    mainloop(task_queue)

