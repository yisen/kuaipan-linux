#!/usr/bin/python2.7
# -*- coding: utf-8 -*-
import hmac
import hashlib
import binascii
import time
import random
import urllib
import json
import threading
import Queue
import os
import pycurl
#import MultipartPostHandler, urllib2, cookielib
#import sys
from operator import itemgetter


oauth_dict = {
    'oauth_version' : '1.0',
    'oauth_http_method' : 'GET',
    'oauth_signature_method' : 'HMAC-SHA1' ,
    'oauth_consumer_key' : 'xclrhUdwXVa3PcQ2',
    'oauth_consumer_secret' : '2Q0T16Unv9Uf45Hv',
}

url_dict = {
    'root': 'kuaipan',
    'requestToken': 'https://openapi.kuaipan.cn/open/requestToken',
    'authorize': 'https://www.kuaipan.cn/api.php',
    'accessToken': 'https://openapi.kuaipan.cn/open/accessToken',
    'account_info': 'http://openapi.kuaipan.cn/1/account_info',
    'metadata': 'http://openapi.kuaipan.cn/1/metadata/kuaipan/',
    'create_folder': 'http://openapi.kuaipan.cn/1/fileops/create_folder',
    'delete': 'http://openapi.kuaipan.cn/1/fileops/delete', 
    'download_file': 'http://api-content.dfs.kuaipan.cn/1/fileops/download_file',
    'upload_locate': 'http://api-content.dfs.kuaipan.cn/1/fileops/upload_locate',
    'upload_file': '1/fileops/upload_file',
    'move': 'http://openapi.kuaipan.cn/1/fileops/move',
}


def generate_timestamp():
    return int(time.time())

def generate_nonce():
    return ''.join([str(random.randint(0, 9)) for i in range(8)])

def escape(s):
        """Escape a URL including any /."""
        return urllib.quote(s, safe='~')
    
     
class HttpRequest():
    """HttpRqeuest base class"""
    def set_parameters(self, base_url, parameters):  
        """set http request parameters
        
        @param base_url: type IN str, not include '?'
        @param parameters: type IN RequestParameters
        
        """
        self._signature = ""
        self._base_url = base_url
        self._parameters = parameters  
        
    def _generate_basestring(self, parameters):
        """generate base string"""
        url = self._parameters.protocol + "&" + escape(self._base_url) + "&"
        base_string =  url + escape(parameters)
        return base_string
        
    def _generate_signature(self, base_string):
        """generate signature"""
        key = str(oauth_dict['oauth_consumer_secret'] + "&" + self._parameters.oauth_token_secret)
        hashed = hmac.new(key, base_string, hashlib.sha1)
        return binascii.b2a_base64(hashed.digest())[:-1]
    
    def build_httprequest(self, signature=False):
        parameters = self._parameters.build_parameters()
        request_str = self._base_url + "?" + parameters
        if signature:
            _signature = self._generate_signature(self._generate_basestring(parameters))
            request_str += "&" + urllib.urlencode({'oauth_signature': _signature})
        return request_str
    
    def send_request(self, request):
        return urllib.urlopen(request)
    
    def get_response(self, request):
        response = self.send_request(request)
        return json.loads(response.readline())
    

class RequestParameters():
    """RequestParameters base class
    """
    def __init__(self):
        self.parameters = ""
        self.oauth_token_secret = ''
        self._parameters_dict = {}
        self.protocol = 'GET'
    
    def generate_parameters(self):
        raise NotImplementedError
        
    def set_parameter(self, key, value):
        self._parameters_dict[key] = value
    
    def build_parameters(self):
#        self._parameters_dict = {}
        self.set_parameter('oauth_timestamp', generate_timestamp())
        self.set_parameter('oauth_nonce', generate_nonce())
        self.generate_parameters()
        # sort parameters dict
        self._parameters_dict = sorted(self._parameters_dict.iteritems(), key=itemgetter(0), reverse=False)
        self.parameters = urllib.urlencode(self._parameters_dict)
        return self.parameters
        

class RequestTokenParameters(RequestParameters):
    def __init__(self):
        RequestParameters.__init__(self)
        
    def generate_parameters(self):
        self.set_parameter('oauth_consumer_key', oauth_dict['oauth_consumer_key'])
        self.set_parameter('oauth_signature_method', oauth_dict['oauth_signature_method'])
        self.set_parameter('oauth_version', oauth_dict['oauth_version'])
        

class AuthorizeParameters(RequestParameters):
    def __init__(self, value):
        RequestParameters.__init__(self)
        self.oauth_token = value['oauth_token']
        self.oauth_token_secret = value['oauth_token_secret']
        
    def generate_parameters(self):
        self.set_parameter('ac', 'open')
        self.set_parameter('op', 'authorise')
        self.set_parameter('oauth_token', self.oauth_token)
        
        
class AccessTokenParameters(RequestParameters):
    def __init__(self, value):
        RequestParameters.__init__(self)
        self.oauth_token = value['oauth_token']
        self.oauth_token_secret = value['oauth_token_secret']
        
    def generate_parameters(self):
        self.set_parameter('oauth_consumer_key', oauth_dict['oauth_consumer_key'])
        self.set_parameter('oauth_signature_method', oauth_dict['oauth_signature_method'])
        self.set_parameter('oauth_version', oauth_dict['oauth_version'])
        self.set_parameter('oauth_token', self.oauth_token)
        
        
class FileopsRequestParameters(RequestParameters):
    def __init__(self, value):
        RequestParameters.__init__(self)
        self.oauth_token_secret = value['oauth_token_secret']
        self.set_parameter('oauth_token', value['oauth_token'])
        self.set_parameter('oauth_version', oauth_dict['oauth_version'])    
        self.set_parameter('oauth_consumer_key', oauth_dict['oauth_consumer_key'])
        self.set_parameter('oauth_signature_method', oauth_dict['oauth_signature_method'])
        self.set_parameter('oauth_version', oauth_dict['oauth_version'])    
        

class AccountInfoParameters(FileopsRequestParameters):
    def __init__(self, value):
        FileopsRequestParameters.__init__(self, value)
        
    def generate_parameters(self):
        pass
    

class MetadataParameters(FileopsRequestParameters):
    def __init__(self, value):
        FileopsRequestParameters.__init__(self, value)
        
    def generate_parameters(self):
        pass
    
    
class UploadLocateParameters(FileopsRequestParameters):
    def __init__(self, value):
        FileopsRequestParameters.__init__(self, value)
        
    def generate_parameters(self):
        pass
    

class UploadFileParameters(FileopsRequestParameters):
    def __init__(self, value, path):
        FileopsRequestParameters.__init__(self, value)
        self.file_path = path
        self.protocol = 'POST'
        
    def generate_parameters(self):
        self.set_parameter('overwrite', 'True')
        self.set_parameter('root', url_dict['root'])
        self.set_parameter('path', self.file_path)
        

class CreateFolderParameters(FileopsRequestParameters):
    def __init__(self, token, path):
        FileopsRequestParameters.__init__(self, token)
        self.path = path
        
    def generate_parameters(self):
        self.set_parameter('root', url_dict['root'])
        self.set_parameter('path', self.path)
        
        
class DeleteParameters(FileopsRequestParameters):
    def __init__(self, token, path):
        FileopsRequestParameters.__init__(self, token)
        self.path = path
        
    def generate_parameters(self):
        self.set_parameter('root', url_dict['root'])
        self.set_parameter('path', self.path)    
        

class DownloadFileParameters(FileopsRequestParameters):
    def __init__(self, token, path):
        FileopsRequestParameters.__init__(self, token)
        self.path = path
        
    def generate_parameters(self):
        self.set_parameter('root', url_dict['root'])
        self.set_parameter('path', self.path) 
        
        
class MoveParameters(FileopsRequestParameters):
    def __init__(self, token, path):
        FileopsRequestParameters.__init__(self, token)
        self.path = path
        
    def generate_parameters(self):
        self.set_parameter('root', url_dict['root'])
        self.set_parameter('from_path', self.path[0])
        self.set_parameter('to_path', self.path[1])
        

class KuaiPan():
    def __init__(self, configure):
        self._http_request = HttpRequest()
        self.remote_folder_queue = Queue.Queue()
        self.configure = configure
        self.upload_locate = ""
        self.oauth_token = {}
        self.all_folders = []
        self.remote_info_list = []
        self.locale_info_list = []
        self._worker_num = 5
        
    def _get_request_token(self):
        self._http_request.set_parameters(url_dict['requestToken'], RequestTokenParameters())
        request_str = self._http_request.build_httprequest(signature=True)
        self.oauth_token = self._http_request.get_response(request_str)
        
    def _user_authorize(self):
        self._http_request.set_parameters(url_dict['authorize'], AuthorizeParameters(self.oauth_token))
        print self._http_request.build_httprequest()
        
    def _trans_to_dict(self, info_list):
        # FIX: empty folder does not in dict
        _dict = {}
        for folder in info_list:
            if len(folder['files']) == 0:
                _dict[folder['path'] + '/'] = "folder"
            else:
                for file in folder['files']:
                    _dict[folder['path'][1:] + "/" + file['name']] = file['modify_time']
        return _dict
    
    def _cal_time(self, t1, t2):
        t_list1 = t1.split(' ')
        _t1 = t_list1[0].split('-')
        _t1.extend(t_list1[1].split(':'))
        
        t_list2 = t2.split(' ')
        _t2 = t_list2[0].split('-')
        _t2.extend(t_list2[1].split(':'))
        
        for i in range(len(_t1)):
            if int(_t1[i]) > int(_t2[i]):
                return True
            elif int(_t1[i]) < int(_t2[i]):
                return False
        
    def get_access_token(self):
        try:
            with open("oauthkuaipan.txt", "r") as fp:
                self.oauth_token = json.loads(fp.readline())
        except:
            self._get_request_token()
            self._user_authorize()
            raw_input()
            self._http_request.set_parameters(url_dict['accessToken'], AccessTokenParameters(self.oauth_token))
            request_str = self._http_request.build_httprequest(signature=True)
            self.oauth_token = self._http_request.get_response(request_str)
            
    def get_account_info(self):
        self._http_request.set_parameters(url_dict['account_info'], AccountInfoParameters(self.oauth_token))
        request = self._http_request.build_httprequest(signature=True)
        self.account_info = self._http_request.get_response(request)

    def get_metadata(self, path):
        url = url_dict['metadata'] + escape(str(path))
        self._http_request.set_parameters(url, MetadataParameters(self.oauth_token))
        request = self._http_request.build_httprequest(signature=True)
        return self._http_request.get_response(request)
    
    def build_remote_list(self, path):
        self.remote_info_list = []
        self.remote_folder_queue.empty()
        self.remote_folder_queue.put(path)
        
        handle_files_worker_list = []
        for i in range(self._worker_num):
            handle_files_worker = HandleFilesWorkerThread(self, self.remote_folder_queue)
            handle_files_worker_list.append(handle_files_worker)
            handle_files_worker_list[i].start()
            
        for i in range(self._worker_num):
            handle_files_worker_list[i].join()
            print "worker %d join!" % i
            
    def build_locale_list(self, path):
        self.locale_info_list = []
        for path, dirs, files in os.walk(path):
            _dict = {}
            _dict['path'] = path
            _dict['files'] = []
            
            for file_name in files:
                _file = {}
                _file['modify_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(
                                                    os.stat(_dict['path'] + "/" + file_name).st_mtime))    
                _file['name'] = file_name
                _dict['files'].append(_file)
                
            self.locale_info_list.append(_dict)
            
    def compare_diffs(self):
        self.remote_transed_dict = self._trans_to_dict(self.remote_info_list)
        self.locale_transed_dict = self._trans_to_dict(self.locale_info_list)
        # FIX: test modify time
        
        _diff_files = []
        _set = set(self.remote_transed_dict.items()) ^ set(self.locale_transed_dict.items())
        for file_path in _set:
            _diff_files.append(file_path[0])
        
        return list(set(_diff_files))
    
    def add_task(self, diff_list, task_queue):
        for diff_item in diff_list:
            if diff_item in self.locale_transed_dict.keys():
                if diff_item in self.remote_transed_dict.keys():
                    # diffenert
                    if self._cal_time(self.locale_transed_dict[diff_item], self.remote_transed_dict[diff_item]):
                        # True, locale is newer
                        task_queue.put((diff_item, 'UPLOAD')) 
                        print 'newer:', diff_item
                    else:
                        task_queue.put(diff_item, 'DOWNLOAD')
                else:
                    # in locale
                    if diff_item[-1] == '/':
                        task_queue.put((diff_item[:-1], 'CREATE'))
                    else:
                        task_queue.put((diff_item, 'UPLOAD'))
            else:
                # in remote
                task_queue.put((diff_item, 'DOWNLOAD'))
                
    def handle_task_mainloop(self, task_queue):
        """wait for task and handle it
        
        @param task_queue: type IN Queue, task queue
        
        """
        self.handle_task_worker = HandleTaskWorkerManager(self, task_queue)
        self.handle_task_worker.start()
        
    def create_folder(self, folder):
        self._http_request.set_parameters(url_dict['create_folder'], CreateFolderParameters(self.oauth_token, folder))
        request = self._http_request.build_httprequest(signature=True)
        
        while True:
            response = self._http_request.get_response(request)
            if response['msg'] == 'ok':
                break
            else:
                print response
        return
    
    def delete(self, path):
        self._http_request.set_parameters(url_dict['delete'], DeleteParameters(self.oauth_token, path))
        request = self._http_request.build_httprequest(signature=True)
        self._http_request.send_request(request)
        return
    
    def _get_upload_locate(self):
        self._http_request.set_parameters(url_dict['upload_locate'], UploadLocateParameters(self.oauth_token))
        request = self._http_request.build_httprequest(signature=True)
        self.upload_locate = self._http_request.get_response(request)['url']   
    
    def handle_ret_json(self, buff):
        pass
    
    def _upload_file(self, url, file):
        file = self.configure['root_path'] + '/' + file
        
        c = pycurl.Curl()
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.URL, str(url))
        c.setopt(pycurl.HTTPPOST, [('file', (pycurl.FORM_FILE,  file))])
        c.setopt(pycurl.WRITEFUNCTION, self.handle_ret_json)
        while True:
            try:
                c.perform()
                break
            except:
                continue
        c.close()
    
    def upload(self, path):
        if self.upload_locate == "":
            self._get_upload_locate()
        self._http_request.set_parameters(self.upload_locate + url_dict['upload_file'], UploadFileParameters(self.oauth_token, path))
        request = self._http_request.build_httprequest(signature=True)
        self._upload_file(request, path)

    
    def _curl_download(self, url, path):
        try:
            fd = open(path, "wb")
        except IOError:
            _path = path[::-1]
            _path = _path[_path.index('/'):]
            _path = _path[::-1]
            _path = self.configure['root_path'] + "/" + _path
            if not os.path.exists(_path):
                os.makedirs(_path)
            fd = open(self.configure['root_path'] + "/" + path, "wb")
        
        crl = pycurl.Curl()
        crl.setopt(pycurl.FOLLOWLOCATION, 1)
        crl.setopt(pycurl.URL, url)
        crl.setopt(pycurl.COOKIEFILE, "temp.cookie")
        crl.setopt(pycurl.WRITEDATA, fd)
        while True:
            try:
                crl.perform()
                break
            except:
                continue
        crl.close()
    
    def download(self, path):
        self._http_request.set_parameters(url_dict['download_file'], DownloadFileParameters(self.oauth_token, path))
        request_url = self._http_request.build_httprequest(signature=True)
        self._curl_download(request_url, path)
        
    def move(self, path):
        self._http_request.set_parameters(url_dict['move'], MoveParameters(self.oauth_token, path))
        request = self._http_request.build_httprequest(signature=True)
        self._http_request.send_request(request)
            
            
class HandleTaskWorkerManager(threading.Thread):
    def __init__(self, kuaipan, task_queue):
        threading.Thread.__init__(self)
        self._kuaipan = kuaipan
        self._task_queue = task_queue
        self.killed = False
        
    def run(self):
        task_worker_list = []
        for i in range(self._kuaipan._worker_num):
            task_worker_list.append(HandleTaskWorkerThread(self._kuaipan, self._task_queue))
            task_worker_list[i].start()
            
        for i in range(self._kuaipan._worker_num):
            task_worker_list[i].join()
            print "task worker %d join!" % i        
        
        
class HandleTaskWorkerThread(threading.Thread):
    def __init__(self, kuaipan, task_queue):
        threading.Thread.__init__(self)
        self._kuaipan = kuaipan
        self._task_queue = task_queue
        self.killed = False
        
    def handle_task(self, task):
        task_type = {
            'UPLOAD': self._kuaipan.upload,
            'DOWNLOAD': self._kuaipan.download,
            'CREATE': self._kuaipan.create_folder,
            'DELETE': self._kuaipan.delete,
            'MOVE': self._kuaipan.move,
        }
        path, event_type = task
        print task
        task_type[event_type](path)
    
    def run(self):
        while True:
            if self.killed:
                break
            task = self._task_queue.get()
            self.handle_task(task)
            self._task_queue.task_done()
            

class HandleFilesWorkerThread(threading.Thread):
    def __init__(self, kuaipan, task_queue):
        threading.Thread.__init__(self)
        self._kuaipan = kuaipan
        self.killed = False
    
    def handle_files_info(self, info):
        folder_dict = {}
        folder_dict['path'] = info['path']
        folder_dict['files'] = []

        for files in info['files']:
            if files['type'] == "folder":
                path = folder_dict['path'] + ((folder_dict['path'] != "/") and "/" or "") + files['name']
                self._kuaipan.remote_folder_queue.put(path)
            else:
                _file = {}
                _file['name'] = files['name']
                _file['modify_time'] = files['modify_time']
                folder_dict['files'].append(_file)
        
        self._kuaipan.remote_info_list.append(folder_dict)
    
    def run(self):
        while True:
            # quit
            if self.killed:
                break
            
            task_path = self._kuaipan.remote_folder_queue.get()
            try:
                info = self._kuaipan.get_metadata(task_path)
            except:
                self._kuaipan.remote_folder_queue.task_done()
                self._kuaipan.remote_folder_queue.put(task_path)
                break
            self.handle_files_info(info)
            self._kuaipan.remote_folder_queue.task_done()
            
        return
            

def main():
    kuaipan = KuaiPan()
    kuaipan.get_access_token()
    
    print kuaipan.oauth_token
    

if __name__ == '__main__':
    main()
    