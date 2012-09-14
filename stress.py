def stress():
    def rec(n):
        if n:
            return rec(n-1)
    for i in xrange(100):
        rec(100)
