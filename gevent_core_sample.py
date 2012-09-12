import gevent.core
import time

loop = gevent.core.loop()

def callback():
    print time.time()

timer = loop.timer(1.0, 1.0)
timer.start(callback)
loop.run()
