gevent

---

#お前誰よ

稲田 直哉 (@methane)

KLab株式会社

msgpack-python

---

#Summary

- <big>目的</big>
- <big>仕組み</big>
- <big>特徴</big>

---

#目的

---

#gevent = libev x greenlet

##libev
クロスプラットフォームな
イベントドリブンプログラミング
効率のいい **IO多重化** を実現

##greenlet
軽量スレッド

##gevent
2つを組み合わせて **簡単かつ効率のいいIO多重化** を実現

---

#IO多重化

複数のIO処理を並行に行う.

## blocking + thread
並行処理のためにスレッドを使う.

IO待ちのためにスレッドを止める(ブロック)

## nonblocking + event driven
複数のIO待ちをまとめて監視 (select, epoll, kqueue)

実行可能になったIOを処理する.

---

#echoサーバーを作ろう

---

#IO多重化なし
**1クライアントとしか通信できない**

    !python
    import socket
    
    def echo(sock):
        try:
            while True:
                data = sock.recv(1024) # 受信できるまでブロック
                if not data:
                    break
                sock.sendall(data) # 送信できるまでブロック
        finally:
            sock.close()

    def serve(addr):
        sock = socket.socket()
        sock.bind(addr); sock.listen(50)
        while True:
            conn, _ = sock.accept() # 接続されるまでブロック
            echo(conn) # 接続が終わるまでブロック
    
    if __name__ == '__main__':
        serve(('0.0.0.0', 4000))

---

#スレッドでIO多重化

    !python
    import socket, threading
    
    def echo(sock):
        try:
            while True:
                data = sock.recv(1024) # 受信できるまでブロック
                if not data:
                    break
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

---

#nonblocking + select (1)

    !python
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
            reads, writes, _ = select.select(
                    read_handlers.keys(),
                    write_handlers.keys(),
                    [])
            call_handlers(read_handlers, reads)
            call_handlers(write_handlers, writes)
            
---

#nonblocking + select (2)

    !python
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
        sock.bind(addr)
        sock.listen(50)
        ServerHandler(sock)
        loop()
    
    #...

    if __name__ == '__main__':
        serve(('0.0.0.0', 4000))
        
---

#nonblocking + select (3)

    !python
    
    class EchoHandler(object):
        def __init__(self, sock):
            sock.setblocking(0)
            self.sock = sock
            self.buf = []
            read_handlers[sock.fileno()] = self.on_readable

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
---

#nonblocking + select(4)

    !python
    
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

        def close(self):
            fd = self.sock.fileno()
            read_handlers.pop(fd, None)
            write_handlers.pop(fd, None)
            self.sock.close()
            self.buf = []

---

#めんどくさい?

ほとんどが汎用的な処理<br />フレームワーク化可能

##Tornado

    !python
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

---

#geventで多重化
**シングルスレッドなのにブロッキングしてる**

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

    def main(addr):
        server = StreamServer(addr, handler, backlog=1024)
        server.serve_forever()

    if __name__ == '__main__':
        main(('', 4000))

---

#仕組み

---

#greenlet

並行プログラミングのための軽量スレッド

##高効率
- スレッドごとに大きなスタックエリアを取らない
- スイッチのオーバーヘッドが軽い
- 高負荷時のスループット低下が無い

##協調型(cooperative)
- 勝手にスイッチしない(スレッドセーフに書きやすい)

##ユーザーランド
- ブロックするシステムコールを発行すると全スレッドが止まる

---

#greenlet
greenlet.switch() で明示的にスレッドを切り替える

$$$$

    !python
    import greenlet
    def f1():
        print 'f1', 1
        g2.switch()
        print 'f1', 2
        g2.switch()
        print 'f1', 3

    def f2():
        print 'f2', 1
        g1.switch()
        print 'f2', 2
        g1.switch()

    g1 = greenlet.greenlet(f1)
    g2 = greenlet.greenlet(f2)
    g1.switch()

$$$$

実行結果:

    f1 1
    f2 1
    f1 2
    f2 2
    f1 3

---

#gevent.core
libev ラッパー

$$$$

    !python
    import gevent.core
    import time

    loop = gevent.core.loop()

    def callback():
        print time.time()
        
    # 繰り返しタイマーイベント
    timer = loop.timer(1.0, 1.0)
    timer.start(callback)
    loop.run()

$$$$

実行結果:

    1347446334.99
    1347446335.99
    1347446336.99
    1347446337.99
    ...

---

#gevent.hub
イベントループと greenlet を繋げる greenlet

$$$$

    !python
    import gevent.core, greenlet, time
    
    # gevent.get_hub() の簡易版
    loop = gevent.core.loop()
    hub = greenlet.greenlet(loop.run)

    # gevent.sleep() の簡易版
    def sleep(seconds):
        timer = loop.timer(seconds)
        # コールバックで現在の greenlet に switch させる
        timer.start(greenlet.getcurrent().switch)
        # hub に switch してイベントループにもどる
        hub.switch()

    def sleeper():
        for _ in range(4):
            print time.time()
            # ブロックする関数として実行可能
            sleep(1)

    sleeper()
    hub.switch()

$$$$

実行結果:

    1347448193.7
    1347448194.7
    1347448195.71
    1347448196.71

---

#gevent.*

- gevent.thread -- thread の置き換え
- gevent.socket -- socket の置き換え
- gevent.select -- select の置き換え
- gevent.queue -- Queue の置き換え
- gevent.lock -- threading 内のロックの置き換え
- gevent.pywsgi -- wsgi サーバー
- gevent.monkey -- モンキーパッチ

---

#モンキーパッチ

    !python
    import gevent.monkey; gevent.monkey.patch_all()
    import socket, threading
    
    def echo(sock):
        try:
            while True:
                data = sock.recv(1024) # 受信できるまでブロック
                if not data:
                    break
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

---

# gevent とは何か
- libev の Python インターフェース (core)
- イベントコールバックを greenlet のブロックに置き換える (hub)
- 標準ライブラリと互換性の高いモジュール
- モンキーパッチで標準ライブラリを入れ替える
- tcpserver, wsgiserver, 名前解決などのネットワークライブラリ
- その他 pool, Event, AsyncResult などのライブラリ

---

#特徴

---

#...

---

html5-slides-markdown
=====================

Generates a slideshow using the slides that power
[the html5-slides presentation](http://apirocks.com/html5/html5.html).

A `python` with the `jinja2`, `markdown`, and `pygments` modules is required.

Markdown Formatting Instructions
--------------------------------

- Separate your slides with a horizontal rule (--- in markdown)
- Your first slide (title slide) should not have a heading, only `<p>`s
- Your other slides should have a heading that renders to an h1 element
- To highlight blocks of code, put !{{lang}} as the first indented line
- See the included slides.md for an example

Rendering Instructions
----------------------

- Put your markdown content in a file called `slides.md`
- Run `python render.py`
- Enjoy your newly generated `presentation.html`

---

Slide #2
========

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Aenean magna tellus,
fermentum nec venenatis nec, dapibus id metus. Phasellus nulla massa, consequat
nec tempor et, elementum viverra est. Duis sed nisl in eros adipiscing tempor.

Section #1
----------

Integer in dignissim ipsum. Integer pretium nulla at elit facilisis eu feugiat
velit consectetur.

Section #2
----------

Donec risus tortor, dictum sollicitudin ornare eu, egestas at purus. Cras
consequat lacus vitae lectus faucibus et molestie nisl gravida. Donec tempor,
tortor in varius vestibulum, mi odio laoreet magna, in hendrerit nibh neque eu
eros.

---

Middle slide
============

---

Slide #3
========

**Hello Gentlemen**

- Mega Man 2
- Mega Man 3
- Spelunky
- Dungeon Crawl Stone Soup
- Etrian Odyssey

*Are you prepared to see beyond the veil of reason?* - DeceasedCrab

- Black Cascade
- Two Hunters
- Diadem of 12 Stars

---

Slide #4
========

render.py
---------

    !python
    import jinja2
    import markdown

    with open('presentation.html', 'w') as outfile:
        slides_src = markdown.markdown(open('slides.md').read()).split('<hr />\n')

        slides = []

        for slide_src in slides_src:
            header, content = slide_src.split('\n', 1)
            slides.append({'header': header, 'content': content})

        template = jinja2.Template(open('base.html').read())

        outfile.write(template.render({'slides': slides}))

