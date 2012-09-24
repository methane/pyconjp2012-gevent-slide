Gevent

---

#Who am I

<img src='./icon.jpg' style="right: 30px; top: 30px; position: absolute; width:240px; height:240px;
 border-radius:30px; ">

稲田 直哉 (INADA Naoki)

* KLab Inc.
* @methane
* msgpack-python

---

#This presentation

* source

    <small>http://github.com/methane/pyconjp2012-gevent-slide/</small>

* slide

    <small>http://methane.github.com/pyconjp2012-gevent-slide/en.html</small>

---

#Summary

- <big>Target of Gevent</big>
- <big>What makes Gevent unique</big>
- <big>How Gevent works</big>
- <big>Start using Gevent</big>

---

#Target of Gevent

<br />

<big>Easy and efficient **IO multiplexing**</big>

---

#IO multiplexing

Working on conccurrnt IO.

* Web Application
* Chatting system
* tailing multi files.
* downloading many <strike>porn</strike> images from web.

---

#How to multiplex IO

## blocking IO
blocks entire thread when can't process IO immediate.

Make threads to multiplex blocking IO.

## nonblocking IO

returns error without blocking when can't process IO immediate.

1. Wait multiple IOs with single blocking call. (*select*, *epoll*, *kqeuue*, ...)
1. Process returned IO with *event driven programming*.

---

#Make echo server

---

#blocking (no IO multiplexing)

**Only works with single client**

    !python
    import socket
    
    def echo(sock):
        try:
            while True:
                data = sock.recv(1024) # blocks until recieve data.
                if not data:
                    break
                sock.sendall(data) # block until send buffer is not full.
        finally:
            sock.close()

    def serve(addr):
        sock = socket.socket()
        sock.bind(addr); sock.listen(50)
        while True:
            conn, _ = sock.accept() # block untile client comes.
            echo(conn) # doesn't return until client disconnect.
    
    serve(('0.0.0.0', 4000))

---

#blocking with threading

**Wrap with thread. Very easy.**

    !python
    import socket, threading
    
    def echo(sock):
        try:
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                sock.sendall(data)
        finally:
            sock.close()

    def serve(addr):
        sock = socket.socket()
        sock.bind(addr); sock.listen(50)
        while True:
            conn, _ = sock.accept()
            threading.Thread(target=echo, args=(conn,)).start()

    serve(('0.0.0.0', 4000))

---

#nonblocking with select

**Using select manually is very hard**

[<small>echo_select.py</small>](./echo_select.py)

    !python
    
        #...
        def on_readable(self):
            while True:
                conn, _ = self.sock.accept()
                EchoHandler(conn)
        #...
        def on_readable(self):
            try:
                data = self.sock.recv(4096)
                if not data:
                    self.close()
                    return
                self.buf.append(data)
            finally:
                self._update()
        #...

---

#nonblocking with Tornado

It makes event driven programming easy

    !python
    from tornado import ioloop, iostream
    from tornado.netutil import TCPServer

    class EchoServer(TCPServer):
        def handle_stream(self, stream, addr):
            stream.read_until_close(
                    lambda _: stream.close(), # when closed connection.
                    stream.write, # when recieved data.
                    )

    def serve(addr):
        server = EchoServer()
        server.listen(addr[1], addr[0])
        ioloop.IOLoop.instance().start()

    serve(('', 4000))

---

#What makes Gevent unique

---

#What makes Gevent unique

* echo server with Gevent

* Gevent vs Threading

    * Performance

* Gevent vs Tornado

    * Programming.

---

#echo server with gevent

    !python
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

    def serve(addr):
        server = StreamServer(addr, handler, backlog=1024)
        server.serve_forever()

    serve(('', 4000))

---

#**It looks like bloking.<br>But it does IO multiplex in single thread.**

---

#gevent.monkey.patch_all()

    !python
    import gevent.monkey; gevent.monkey.patch_all()
    import socket, threading
    
    def echo(sock):
        try:
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                sock.sendall(data)
        finally:
            sock.close()

    def serve(addr):
        sock = socket.socket()
        sock.bind(addr); sock.listen(50)
        while True:
            conn, _ = sock.accept()
            threading.Thread(target=echo, args=(conn,)).start()
            
    serve(('0.0.0.0', 4000))

---

#**Magic 1line makes<br>threaded code to single thread.**

---

#Gevent vs Threading<br/><small>Performance</small>

---

#Benchmark

1000 clients sends 1000 messages to echo server.

(Total 1M messages)

---

#Memory (RSS)

<br />

threading:
34MB

gevent:
26MB

tornado:
12MB

select:
6.1MB

---

#Memory (VSS)

<br />

threading: **3.9GB**

gevent: 41MB

tornado: 27MB

select: 21MB

<br />
Threaded code doesn't run in 32bit environment.

---

#Time

<br />
threading:
43sec

gevent:
53sec

tornado:
43sec

select:
25sec

---

#**Hmm, Threading looks enough.<br>Why using Gevent?**

---

#Benchmark 2

2000 clients send 50 messages. (Total: 0.1M)

Add busy loop before send.

    !python
    
    def stress(): # 18.6 ms
        def rec(n):
            if n:
                return rec(n-1)
        for i in xrange(100):
            rec(100)

---

#Result

<table>
<tr>
<td></td>
<th>Gevent</th>
<th>Threading</th>
</tr>
<tr>
<td>RSS</td>
<td>46.1MB</td>
<td>210.5MB</td>
</tr>
<tr>
<td>VSS</td>
<td>46.5MB</td>
<td>7.9GB</td>
</tr>
<tr>
<td>time</td>
<td>3m20sec</td>
<td>10m55sec</td>
</tr>
</table>

Threading have significant overhead.

---


#Gevent vs Threading

* Threading is enough on many circumstance

    It's ok to use Gevent for fun :-)

* multicore, multithread, heavy load

    When threading overhead is problem,
    Gevent helps us.

---

#Gevent vs Tornado<br/><small>Programming</small>

---

#Connecting multiple bloking functions.

$$$$

##Gevent

    !python
    def spamegg(a):
        b = spam()
        return egg(a, b)

##Tornado

    !python
    class SpameHamEgg(object):
    
        def bake(self, a, callback):
            self.a = a
            self.callback = callback
            spam(callback=self.on_spam)

        def on_spam(self, b):
            egg(self.a, b, callback=self.callback)

$$$$

##tornado.gen

<small>limited coroutine implemented by generator</small>

    !python
    from tornado import gen
    @gen.engine
    def spamegg(a):
        b = yeild spam()
        return egg(a, b)

---

#Error handling

Callback is called from outside of try-catche block.<br>
Event driven programming requires another error handling style.

$$$$

##Gevent

    !python
    def spamegg():
        try:
            a = spam()
            return egg(a)
        except Exception as e:
            log.error(e)
            return None

$$$$

##Tornado

    !python
    import contextlib

    @contextlib.contextmanager
    def log_error():
        try:
            yield
        except Exception as e:
            log.error(e)

    def spamegg():
        with StackContext(log_error):
            spam(callback=egg)

---

#libraries

##Gevent
Many libraries works on Gevent with monkey patching.

It's easy to support gevent.

##Tornado
Requires full scratch.

##Example: PyMongo
Works on Gevent with monkey patch.

It doesn't return to Tornado IO loops.
So Motor (gevent like system) is developed.

---

#Gevent vs Tornado

Torando, Twisted, node.js is good event driven programming framework.

<br/>
Gevent allows **standard programming style<br>and using existing libraries.**

---

#How Gevent works.

---

#How Gevent works.

1. Greenlet
1. gevent.core
1. gevent.hub

---

#Greenlet
lightweight thread requires explicit switch. (coroutine)

$$$$

    !python
    import greenlet
    def f1():
        print 'f1', 1
        g2.switch()
        print 'f1', 3
        g2.switch()
        print 'f1', 5

    def f2():
        print 'f2', 2
        g1.switch()
        print 'f2', 4
        g1.switch()

    g1 = greenlet.greenlet(f1)
    g2 = greenlet.greenlet(f2)
    g1.switch()

$$$$

Result

    f1 1
    f2 2
    f1 3
    f2 4
    f1 5

---

#Greenlet vs Thread

- low memory consuption.
- smaller overhead when switching. (especially, with Old GIL)
- cooperative (easy to write threadsafe code)

- **doesn't run blocking system call concurrently**

---

#gevent.core
Wrapping libev event loop

$$$$

    !python
    import gevent.core
    import time

    loop = gevent.core.loop()

    def callback():
        print time.time()
        
    # repeated timer event.
    timer = loop.timer(1.0, 1.0)
    timer.start(callback)
    loop.run()

$$$$

Result:

    1347446334.99
    1347446335.99
    1347446336.99
    1347446337.99
    ...

---

#gevent.hub
The Greenlet connects eventloop and greenlet.

$$$$

    !python
    import gevent.core, greenlet, time
    
    # simplified hub. (Use hub = gevent.get_hub() normally)
    loop = gevent.core.loop()
    hub = greenlet.greenlet(loop.run)

    # simplified gevent.sleep()
    def sleep(seconds):
        timer = loop.timer(seconds)
        # Switch to current greenlet on callback.
        timer.start(greenlet.getcurrent().switch)
        # Switch to hub and run event loop.
        hub.switch()

    # function looks like blocking code.
    def sleeper():
        for _ in range(4):
            print time.time()
            sleep(1)

    sleeper()

$$$$

Result:

    1347448193.7
    1347448194.7
    1347448195.71
    1347448196.71

---

#gevent.*

- gevent.thread -- gevent version of standard thread
- gevent.socket -- standard socket
- gevent.select -- standard select
- gevent.queue -- standard Queue
- gevent.lock -- locks in threading
- gevent.pywsgi -- wsgi server
- gevent.monkey -- monkey patch
- etc...

---

# What is gevent
- event loop (core)
- connector for event loop and greenlet (hub)
- modules highly compatible to standard library.
- monkey patch replacing standard libraries with gevent version.
- tcpserver, wsgiserver, name resolution, etc...
- pool, Event, AsyncResult, etc...

---

#Start using Gevent

---

#Chance to starting

* supporting WebSocket
* supporting Comet (long polling)
* supporting Streaming API
* anytime needs massive concurrent connection.
* When threading is not efficient.

---

#Where can't use Gevent now.

* Python 3
* PyPy

---

#Where to go now.

[tutorial](http://sdiehl.github.com/gevent-tutorial)

http://sdiehl.github.com/gevent-tutorial

[in japanese](http://methane.github.com/gevent-tutorial-ja)

http://methane.github.com/gevent-tutorial-ja

[Github](https://github.com/SiteSupport/gevent)

https://github.com/SiteSupport/gevent

[website](http://gevent.org/)

http://gevent.org/
  
---

#Thanks.

---

#...

---
