import gevent.core
import greenlet
import time

loop = gevent.core.loop()
hub = greenlet.greenlet(loop.run)

def sleep(seconds):
    timer = loop.timer(seconds)
    timer.start(greenlet.getcurrent().switch)
    hub.switch()

def sleeper():
    for _ in range(4):
        print time.time()
        sleep(1)

sleeper()
hub.switch()
