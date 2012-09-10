from gevent.pywsgi import WSGIServer
import render

def app(env, start_response):
    content = render.render()
    content = content.encode('utf-8')
    L = len(content)

    start_response('200 OK',
            [
                ('Content-Length', str(L)),
                ('Content-Type', 'text/html; charset=utf-8'),
            ])
    return [content]

WSGIServer(('127.0.0.1', 8001), app).serve_forever()
