#!/usr/bin/env python
from gevent.server import StreamServer

def handler(sock, addr):
    try:
        while 1:
            buf = sock.recv(4096)
            if not buf:
                return
            sock.sendall(buf)
    finally:
        sock.close()

def main(addr):
    server = StreamServer(addr, handler, backlog=1024)
    server.serve_forever()

if __name__ == '__main__':
    main(('', 4000))
