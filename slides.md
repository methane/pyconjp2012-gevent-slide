Gevent

---

#お前誰よ

<img src='./icon.jpg' style="right: 30px; top: 30px; position: absolute; width:240px; height:240px;
 border-radius:30px; ">

稲田 直哉

* @methane
* msgpack-python
* エキスパート Python プログラミング
* これから Python 3 の本を書く

<br />
KLab株式会社

* スポンサーしてます
* **We're hiring!**

---

#発表資料

* ソース

    <small>http://github.com/methane/pyconjp2012-gevent-slide</small>

* スライド

    <small>http://methane.github.com/pyconjp2012-gevent-slide</small>

---

#Summary

- <big>Gevent の目的</big>
- <big>Gevent の特徴</big>
- <big>Gevent の仕組み</big>
- <big>Gevent を使おう</big>

---

#Gevent の目的

<br />

<big>簡単かつ効率のいい **IO多重化** </big>

---

#IO多重化とは

複数のIO処理を並行に扱うこと.

* Webアプリ
* チャット
* 複数のファイルの tail
* たくさんの<s>エロ</s>画像のダウンロード

---

#IO多重化の手段

## blocking IO
スレッドを止めてIOを待つ

スレッドを複数使うことで多重化

## nonblocking IO
IOを待たないでエラーを返す.

複数のIOをまとめて待つ(selectなど)ことで多重化

実行可能になったIOに対応する処理を実行する **イベントドリブン** プログラム.

---

#echoサーバーを作ろう

---

#blocking (多重化なし)

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
            echo(conn) # 終わるまで帰ってこない
    
    serve(('0.0.0.0', 4000))

---

#blocking with threading

**並行処理したい関数をスレッドで包むだけ**

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
            threading.Thread(target=echo, args=(conn,)).start()

    serve(('0.0.0.0', 4000))

---

#nonblocking with select

**かなり面倒**

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

基本はコールバック使ったイベントドリブンのまま。

    !python
    from tornado import ioloop, iostream
    from tornado.netutil import TCPServer

    class EchoServer(TCPServer):
        def handle_stream(self, stream, addr):
            stream.read_until_close(
                    lambda _: stream.close(), # 切断時コールバック
                    stream.write, # データ受信コールバック
                    )

    def serve(addr):
        server = EchoServer()
        server.listen(addr[1], addr[0])
        ioloop.IOLoop.instance().start()

    serve(('', 4000))

---

#Gevent の特徴

---

#Gevent の特徴

* echoサーバー

* Gevent vs Threading

    * パフォーマンス対決

* Gevent vs Tornado

    * 使いやすさ対決

---

#Gevent で echo サーバー

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

#**どう見てもblockingなのに、<br />スレッド1つで多重化できる**

---

#gevent.monkey.patch_all()

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
            threading.Thread(target=echo, args=(conn,)).start()
            
    serve(('0.0.0.0', 4000))

---

#**スレッド版のコードが<br />魔法の1行でGevent版に**

---

#Gevent vs Threading<br/><small>パフォーマンス対決</small>

---

#ベンチマーク

echo サーバーに 1000接続から1000回ずつ、

計100万回のメッセージを送受信.

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

---

#仮想メモリ使用量(VSS)

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

---

#**Gevent意味あんの？**

---

#ベンチマーク2

2000接続から50回ずつ、計10万回リクエスト

send の手前で負荷をかけてみる

    !python
    
    def stress(): # 18.6 ms
        def rec(n):
            if n:
                return rec(n-1)
        for i in xrange(100):
            rec(100)

---

#結果

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

スレッドのオーバーヘッド:

* 深い関数呼び出し => メモリ使用量が増える

* CPUを使う処理がたくさん並行する

    => 実行時間が増える

---


#Gevent vs Threading まとめ

* たいていスレッドで十分

    ワクワクするから Gevent を使うというのはアリ :-)

* マルチコア・マルチスレッド・高負荷のとき

    スレッドのオーバーヘッドが大きい(GIL)場合は、
    Gevent の方が安定した性能が出る.

* メモリを節約したい場面でも有効

---

#Gevent vs Tornado<br/><small>使いやすさ対決</small>

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
多くのライブラリがモンキーパッチで動く.

後から Gevent に対応するのも容易.

##Tornado
最初から Tornado 用に設計されてないと対応が難しい.

##例: PyMongo
gevent は monkey patch だけで動く

Tornado に対応させるために Motor が作られた。
(Gevent のような仕組みをTornadoで実現)

---

#Gevent vs Tornado

Tornado, Twisted, node.js はそれぞれイベントドリブンプログラミングのためのフレームワークとしてとてもおもしろい。

<br/>
パフォーマンスについても、 Tornado や Twisted の方が若干軽く、しかも PyPy に対応できる。

<br/>
Gevent は **今までと同じプログラムの書き方ができ、<br />既存のライブラリを対応させるのも容易**

---

#Gevent の仕組み

---

#Gevent の仕組み

* Greenlet
* gevent.core
* gevent.hub

---

#Greenlet
明示的に切り替えが必要な軽量スレッド(コルーチン)

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

実行結果

    f1 1
    f2 2
    f1 3
    f2 4
    f1 5

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
- etc...

---

# gevent とは何か
- イベントループ (core)
- コールバックから greenlet への橋渡し (hub)
- 標準ライブラリと互換性の高いモジュール群
- 標準ライブラリを置き換えるモンキーパッチ
- tcpserver, wsgiserver, 名前解決などのネットワークライブラリ
- その他 pool, Event, AsyncResult などのライブラリ

---

#Gevent を使おう

---

#Gevent を使うチャンス

* WebSocket対応
* Comet (long polling) 対応
* Streaming API 対応
* その他、アプリの機能の一部として大量接続が必要になるケース.
* その他、メモリを節約したかったりGILに悩んでいるケース.

---

#Gevent が使えない環境

## Python 3
* 必要性は認識されているが、現在は 1.0 の完成に注力されている.

## PyPy
* greenlet は CPython 専用。 PyPy に stackless が導入されたのでそれを元に再実装が必要.
* Cython + PyPy の環境は整備されてきているが、性能が出るのはまだまだ先.

---

#参考

* [チュートリアル](http://sdiehl.github.com/gevent-tutorial)

    http://sdiehl.github.com/gevent-tutorial
    
* [日本語訳](http://methane.github.com/gevent-tutorial-ja)

    http://methane.github.com/gevent-tutorial-ja
    
* 公式サイト
 
    http://gevent.org/
  
* プロジェクト

    http://code.google.com/p/gevent/

---

#Thanks.

---

#...

---
