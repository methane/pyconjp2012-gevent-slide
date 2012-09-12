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
