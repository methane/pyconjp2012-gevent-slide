import socket, select, errno

read_handlers = {}
write_handlers = {}

def call_handlers(handlers, fds):
    for fd in fds:
        try:
            handlers[fd]()
        except IOError as e:
            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                continue
        except KeyError:
            pass
def loop():
    while True:
        reads, writes, x = select.select(read_handlers.keys(), write_handlers.keys(), [])
        call_handlers(read_handlers, reads)
        call_handlers(write_handlers, writes)

class ServerHandler(object):
    def __init__(self, sock):
        sock.setblocking(0)
        self.sock = sock
        read_handlers[sock.fileno()] = self.on_readable

    def on_readable(self):
        while True:
            conn, _ = self.sock.accept()
            EchoHandler(conn)

def serve(addr):
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(addr)
    sock.listen(50)
    ServerHandler(sock)
    loop()

class EchoHandler(object):
    def __init__(self, sock):
        sock.setblocking(0)
        self.sock = sock
        self.buf = []
        read_handlers[sock.fileno()] = self.on_readable

    def close(self):
        fd = self.sock.fileno()
        read_handlers.pop(fd, None)
        write_handlers.pop(fd, None)
        self.sock.close()
        self.buf = []

    def on_readable(self):
        try:
            while True:
                data = self.sock.recv(4096)
                if not data:
                    self.close()
                    return
                self.buf.append(data)
        finally:
            if self.buf:
                write_handlers[self.sock.fileno()] = self.on_writable

    def on_writable(self):
        try:
            while self.buf:
                data = self.buf[0]
                sent = self.sock.send(data)
                data = data[sent:]
                if not data:
                    self.buf.pop(0)
                else:
                    self.buf[0] = data
        finally:
            if self.buf:
                write_handlers[self.sock.fileno()] = self.on_writable
                
if __name__ == '__main__':
    serve(('0.0.0.0', 4000))

