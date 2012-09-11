import socket
import time

def main():
    socks = []
    for _ in xrange(1000):
        s = socket.socket()
        s.connect(('127.0.0.1', 4000))
        socks.append(s)

    for s in socks:
        s.sendall('hello\n')

    for _ in xrange(999):
        for s in socks:
            s.recv(1024)
            s.sendall('hello\n')

    for s in socks:
        s.recv()

main()
