
from locust import TaskSet,Locust,events,task
from locust.exception import LocustError
import socket
import requests
import json
import time
import struct
from random import randint
import Login_pb2,Common_pb2

def get_addr(account):
    url = 'http://192.168.11.249:8003/authentication'
    data = json.dumps({'account': account, 'ip': '192.168.10.143'})
    header = {"Content-Type": 'application/x-www-form-urlencoded', 'cache-control': 'no-cache'}
    a = requests.post(url, headers=header, data={'data': data})
    b = json.loads(a.content)
    print(b)
    gameAddr = b['gameAddr'].split(':')

    return gameAddr


class TcpClient(object):

    def __init__(self,host,port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    # def __getattr__(self, item):
    #     func = self.sock.__getattribute__(item)
    #
    #     def wrapper(*args,**kwargs):
    #         pass

    def http_request(self,account):
        url = 'http://192.168.11.249:8003/authentication'
        data = json.dumps({'account': account, 'ip': '192.168.10.143'})
        header = {"Content-Type":'application/x-www-form-urlencoded', 'cache-control': 'no-cache', 'connection':'close'}

        start_time = time.time()
        try:
            a = requests.post(url, headers=header, data={'data': data})
        except Exception as e:
            end_time = time.time()
            total_time = int((end_time - start_time) * 1000)
            events.request_failure.fire(request_type='http',
                                        name='http_request',
                                        response_time=total_time,
                                        exception=e)
        else:
            b = json.loads(a.content)
            connectKey = b['connectKey']
            gameAddr = tuple(b['gameAddr'].split(':'))
            end_time = time.time()
            total_time = int((end_time - start_time)*1000)
            events.request_success.fire(request_type='http',
                                        name='http_request',
                                        response_time=total_time,
                                        response_length=0)
            return gameAddr, connectKey

    def tcp_send(self,msg):
        self.sock.send(msg)

    def tcp_recv(self,length):
        blocks = []
        while length:
            block = self.sock.recv(length)
            if not block:
                raise EOFError('还有%d字节数据没有收到' % length)
            length -= len(block)
            blocks.append(block)
        return b''.join(blocks)

    def login(self,key):
        user = Login_pb2.C2SLogin()
        user.account = 'po002'
        user.connectKey = key
        user.platId = 1
        user.platToken = 'po'
        return user

    def tcp_request(self, connectKey):
        start_time = time.time()
        try:
            payload = self.login(connectKey).SerializeToString()
            client_data = struct.pack("!2IH%ds" % len(payload), (len(payload)+6), 1001, 10086, payload)
            self.tcp_send(client_data)
        except Exception as e:
            end_time = time.time()
            total_time = int((end_time - start_time) * 1000)
            events.request_failure.fire(request_type='tcp',
                                        name='tcp_request',
                                        response_time=total_time,
                                        exception=e)
        else:
            head_data = self.tcp_recv(4)
            package_len = int(struct.unpack('!I', head_data)[0])
            server_data = self.tcp_recv(package_len)
            end_time = time.time()
            total_time = int((end_time - start_time)*1000)
            events.request_success.fire(request_type='tcp',
                                        name='tcp_request',
                                        response_time=total_time,
                                        response_length=package_len)
            return package_len

class Task_set(TaskSet):

    @task(1)
    def login(self):
        account = 'po' + str(randint(1, 9999)) + str(randint(1, 9999))
        start_time = time.time()
        try:
            (_, connectkey) = self.client.http_request(account)
        except Exception as e:
            end_time = time.time()
            total_time = int((end_time - start_time) * 1000)
            events.request_failure.fire(request_type='tcp',
                                        name='login',
                                        response_time=total_time,
                                        exception=e)
        else:
            package_len = self.client.tcp_request(connectkey)
            end_time = time.time()
            total_time = int((end_time - start_time) * 1000)
            events.request_success.fire(request_type='tcp',
                                        name='login',
                                        response_time=total_time,
                                        response_length=package_len)




class User1(Locust):

    def __init__(self, *args, **kwargs):
        super(User1,self).__init__(*args, **kwargs)
        if self.host is None:
            raise LocustError("without host")
        self.client = TcpClient(self.host, self.port)

    task_set = Task_set
    # gameaddr = get_addr('po10000')
    host = '192.168.11.249'
    port = 8001
    min_wait = 1000
    max_wait = 1000



# if __name__ == "__main__":
#     gameaddr = get_addr('po11130')
#     host = gameaddr[0]
#     port = int(gameaddr[1])
#     sock = TcpClient(host, port)
#     print(sock)
#     (_,connectkey) = sock.http_request('poooo')
#     print('发送tcp:')
#     plen = sock.tcp_request(connectkey)
#     print(plen)