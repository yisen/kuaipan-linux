#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import oauthkuaipan
import thread
import time
import Queue
import hdnotify


# global configure
task_queue = Queue.Queue()

configure_dict = {
    'root_path': "/root/kuaipan",
    'filter_list': "~|.tmp|.swp|.swx|.swpx",
}


LOCAL_PATH = "/root/kuaipan"


def main():
    global configure_dict
    global task_queue
    kuaipan = oauthkuaipan.KuaiPan(configure_dict)
    
    # start monitor locale folder
    monitor_locale_folder = hdnotify.MonitorLocaleFolder(configure_dict, task_queue)
    monitor_locale_folder.start()
    
    # Login
    kuaipan.get_access_token()
#    kuaipan.get_account_info()

    # test
#    task_queue.put(('test/1', 'UPLOAD'))
    
    # start main task handle thread
    kuaipan.handle_task_mainloop(task_queue)
    
    # sync every 5min+
    while True:
        # FIX: change get locale and remote
        
        # get locale list
        kuaipan.build_locale_list(configure_dict['root_path'])

        # get remote list
        thread.start_new_thread(kuaipan.build_remote_list, ("wallpaper",))
        while True:
            time.sleep(10)
            if kuaipan.remote_folder_queue.qsize() == 0:
                break

        # get diffs
        kuaipan.add_task(kuaipan.compare_diffs(), task_queue)
        time.sleep(300)
        
    # stop threads
    kuaipan.handle_task_worker.join()
    monitor_locale_folder.join()
    kuaipan.remote_folder_queue.join()
    task_queue.join()
    
    

if __name__ == '__main__':
    main()