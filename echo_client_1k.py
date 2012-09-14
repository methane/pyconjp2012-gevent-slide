import socket
import time

def main():
    socks = []
    for _ in xrange(2000):
        s = socket.socket()
        s.connect(('127.0.0.1', 4000))
        socks.append(s)

    for s in socks:
        s.sendall('hello\n')

    for i in xrange(50):
        print i
        for s in socks:
            s.recv(1024)
            s.sendall('hello\n')

    for s in socks:
        s.recv(1024)

main()
