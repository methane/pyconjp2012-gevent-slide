#!/usr/bin/env python
from tornado import ioloop, iostream
from tornado.netutil import TCPServer

class EchoServer(TCPServer):
    def handle_stream(self, stream, addr):
        stream.read_until_close(lambda _: stream.close(),
                                stream.write)

def serve(addr):
    server = EchoServer()
    server.listen(addr[1], addr[0])
    ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    serve(('', 4000))
