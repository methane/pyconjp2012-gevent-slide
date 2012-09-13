Gevent

---

#お前誰よ

稲田 直哉 (@methane)

KLab株式会社

* msgpack-python
* エキスパート Python プログラミング
* これから Python 3 のコアな本を書く予定

---

#Summary

- <big>Gevent の目的</big>
- <big>Gevent の仕組み</big>
- <big>Gevent の特徴</big>
- <big>Gevent を使おう</big>

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

複数のIO処理を並行に扱うこと.

## blocking IO
IOをすぐに実行できない場合は、そのスレッドを止めて待たせる.

スレッドを複数使うことで並行処理が可能.

## nonblocking IO
IOをすぐに実行できない場合は、エラーを返す.

複数のIO待ちをまとめて待つ.

実行可能になったIOを処理する **イベントドリブン** プログラム.

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

#nonblocking + select で多重化 (1)

    !python
    import socket, select, errno

    read_handlers = {}  # IO待ちとコールバック関数の管理.
    write_handlers = {}

    def call_handlers(handlers, fds): # コールバックの呼び出し.
        for fd in fds:
            try:
                handlers[fd]()
            except IOError as e:
                if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                    continue
            except KeyError:
                pass
                
    def loop():  # イベントループ
        while True:
            reads, writes, _ = select.select(
                    read_handlers.keys(),
                    write_handlers.keys(),
                    [])
            call_handlers(read_handlers, reads)
            call_handlers(write_handlers, writes)
            
---

#nonblocking + select で多重化 (2)

サーバーの起動と新規接続の受けつけ

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

#nonblocking + select で多重化 (3)

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
                self._update()
                
        def _update(self):
            if self.buf:
                write_handlers[self.sock.fileno()] = self.on_writable
            else:
                write_handlers.pop(self.sock.fileno(), None)
        #...
                
---

#nonblocking + select で多重化 (4)

    !python
        #...
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
                self._update()

        def close(self):
            fd = self.sock.fileno()
            read_handlers.pop(fd, None)
            write_handlers.pop(fd, None)
            self.sock.close()
            self.buf = []

---

#めんどくさい?

ほとんどが汎用的な処理で、フレームワーク化が可能

イベントループ＋コールバックという構成は基本的に変わらない

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
明示的に切り替えが必要な軽量スレッド(コルーチン)

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

#Greenlet vs Thread

- スレッドごとに大きなスタックエリアを取らない
- スイッチのオーバーヘッドが軽い
- 高負荷時のスループット低下が無い
- 勝手にスイッチしない(スレッドセーフに書きやすい)

- **ブロックするシステムコールを実行すると、ほかのスレッドに切り替えることができない**
- マルチコアを活かせない

---

#gevent.core
libev ラッパー

イベントループを抽象化する.

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
    
    # hub = gevent.get_hub() の簡易版
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
- イベントループ (core)
- コールバックから greenlet への橋渡し (hub)
- 標準ライブラリと互換性の高いモジュール群
- 標準ライブラリを置き換えるモンキーパッチ
- tcpserver, wsgiserver, 名前解決などのネットワークライブラリ
- その他 pool, Event, AsyncResult などのライブラリ

---

#特徴

---

#スレッド vs gevent

---

#ベンチマーク
echo サーバーに、1000接続から1000回ずつ、計100万回のメッセージを送受信します.

厳密に計測したわけではないので傾向をみるだけにしてください。

---

#メモリ使用量(RSS)

<br />

threading:
34MB

gevent:
26MB

tornado:
12MB

select:
6.1MB

<br />
アプリケーションを乗せるともっと差が開く可能性があるが、クリティカルな差ではない。

---

#メモリ使用量(VSS)

<br />

threading: **3.9GB**

gevent: 41MB

tornado: 27MB

select: 21MB

<br />
32bit 環境では2GBしかメモリ空間がないので致命的(C10K問題).
64bit 環境では無視できる。

---

#時間

<br />
threading:
43sec

gevent:
53sec

tornado:
43sec

select:
25sec

<br />
OSのスケジューラが十分良いので、むしろオーバーヘッドの分だけ遅くなっている。

ただし、条件によっては GIL やその他の同期機構のオーバーヘッドが大きくなって逆転する可能性がある。

---

#ネイティブスレッド vs Gevent

たいていのケースではスレッドで十分うまくいく。

GIL がよく dis られるが、問題になるケースは限られる。

スレッドで何か問題があってからでも Gevent に移行できる。

(スレッドで十分でも、ワクワクするから Gevent を使うというのはアリ:-)

---

#Tornado vs Gevent

---

#複数の処理を繋げる

イベントドリブンだと処理が細切れになりがち.

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

<small>ジェネレータを使ったコルーチン.</small>

    !python
    from tornado import gen
    @gen.engine
    def spamegg(a):
        b = yeild spam()
        return egg(a, b)

---

#エラー処理

callback が呼ばれるのは try-catch ブロックの外.<br />
イベントドリブンでは try-catch に代わる仕組みが必要。

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

#ライブラリの対応

##Gevent
PyMySQL のように、 Python のソケットを使っているライブラリはモンキーパッチで動く可能性が高い。
追加で Gevent に対応するのも容易.

##Tornado
最初から Tornado 用に設計されてないと対応が難しい.

##例: PyMongo
gevent は monkey patch だけで動く

Tornado に対応させるために、 Motor がある。(内部では gevent.hub みたいな機能を実装している)

---

#Gevent vs Tornado

Tornado, Twisted, node.js はそれぞれイベントドリブンプログラミングのためのフレームワークとしてとてもおもしろい。

パフォーマンスについても、 Tornado や Twisted の方が若干軽く、しかも PyPy に対応できる。

Gevent は今までと同じプログラムの書き方ができ、既存のライブラリを対応させるのも容易なのが特徴。

---

#Gevent を使おう

---

#Gevent を使うチャンス

* WebSocket対応
* Coment (long polling) 対応
* Streaming API 対応
* その他、アプリの機能の一部として大量接続が必要になるケース.

---

#Gevent を使いたくなったら

* チュートリアル

    http://sdiehl.github.com/gevent-tutorial
    
    (日本語訳) http://methane.github.com/gevent-tutorial-ja
    
* 公式サイト
 
    http://gevent.org/
  
* プロジェクト

    http://code.google.com/p/gevent/

---

#Gevent が使えない環境

## Python 3
* 必要性は認識されているが、現在は 1.0 の完成に注力されている.

## PyPy
* greenlet は CPython 専用。 PyPy に stackless が導入されたのでそれを元に再実装が必要.
* Cython + PyPy の環境は整備されてきているが、性能が出るのはまだまだ先.

---

#もっと先へ

CPUコア数だけネイティブスレッドを動かし、その上でさらに軽量スレッドを動かすことで、
マルチコアの性能を活かせる. (N-Mモデル).

* Haskell
* Erlang
* Go (Google)
* Rust (Mozilla)
