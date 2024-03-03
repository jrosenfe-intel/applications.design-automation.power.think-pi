# To invoke this script
# C:\thinkpi\Scripts\python.exe C:\thinkpi\app\process_manager.py

import sys
sys.path.append(r"C:\thinkpi\core_latest")
import subprocess
from concurrent.futures import ThreadPoolExecutor

import requests


from thinkpi.backend_api import lib

class Manager:

    def __init__(self):

        self.num_restarts = 1
        self.server_list = self.get_server_list()

  
    def get_server_list(self):

        lib_mgr = lib.LibManager()
        servers_list = lib_mgr.get_server_list()
        hostname_by_ip = {ip:host_name.lower() for ip, host_name in zip(servers_list['ip_address'],
                                                              servers_list['host_name'])}
        return hostname_by_ip
        
    def ping(self, ip_address):
    
        try:
            r = requests.get(f'http://{ip_address}:8080/ping', timeout=10)
        except (requests.ConnectionError, requests.exceptions.ReadTimeout):
            return 'Connection error'
        
        return 'pong'

    def update(self, ip_address):

        print(f'Updating server {self.server_list[ip_address]} ({ip_address})...')
        try:
            r = requests.get(f'http://{ip_address}:8080/update', timeout=300)
        except (requests.ConnectionError, requests.exceptions.ReadTimeout):
            print(f'{self.server_list[ip_address]} ({ip_address}) connection error. Aborting update.')
            return 'Connection error'

        print(f'Update on server {self.server_list[ip_address]} ({ip_address}) is done')
        return 'success'
    
    def update_all(self):

        with ThreadPoolExecutor(len(self.server_list)) as tpe:
            responses = [response for response in tpe.map(self.update,
                                                          (self.server_list.keys()))]

    def shutdown(self, ip_address):

        pong = self.ping(ip_address)
        if pong == 'pong':
            print(f'Restarting server {self.server_list[ip_address]} ({ip_address})...')
            try:
                r = requests.get(f'http://{ip_address}:8080/stop-server', timeout=10)
            except requests.ConnectionError: # Not a real connection error since the server got shutdown
                pass
        else:
            print(f'Connection error server {self.server_list[ip_address]} ({ip_address})')
            return pong

    def check_server(self, ip_address):

        pong = self.ping(ip_address)
        if pong == 'pong':
            message = 'has restarted successfuly'
        else:
            message = 'failed to restart'
        print(f'Server {self.server_list[ip_address]} ({ip_address}) {message}')

    def scan_servers(self, operation):

        for ip in self.server_list.keys():
            operation(ip)


if __name__ == '__main__':
    mgr = Manager()
    if len(sys.argv) > 1 and sys.argv[1] == 'restart':
        mgr.scan_servers(mgr.shutdown)
        mgr.scan_servers(mgr.check_server)
    elif len(sys.argv) > 1 and sys.argv[1] == 'update':
        mgr.update_all()
        mgr.scan_servers(mgr.shutdown)
        mgr.scan_servers(mgr.check_server)
    else:
        while True:
            if mgr.num_restarts > 20:
                print("Shutting down server after 20 restarts")
                break
            subprocess.run(r'C:\thinkpi\Scripts\python.exe C:\thinkpi\app\backend\main.py'.split(), stdout=subprocess.PIPE, text=True)
            print(f'Restarting server {mgr.num_restarts} time(s) out of 20')
            mgr.num_restarts += 1
            
    

