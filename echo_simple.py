#coding: utf-8
import sys
if 'g' in sys.argv:
    import gevent.monkey; gevent.monkey.patch_all()
import os
print os.getpid()
import socket, threading

from stress import stress

def echo(sock):
    try:
        while True:
            data = sock.recv(1024) # 受信できるまでブロック
            if not data:
                break
            stress()
            sock.sendall(data) # 送信できるまでブロック
    finally:
        sock.close()

def serve(addr):
    sock = socket.socket()
    sock.bind(addr); sock.listen(50)
    while True:
        conn, _ = sock.accept()
        # クライアントごとにスレッドを立ち上げて並行処理
        threading.Thread(target=echo, args=(conn,)).start()

if __name__ == '__main__':
    serve(('0.0.0.0', 4000))

