from gevent.pywsgi import WSGIServer
import render


def slide(env, start_response):
    content = render.render()
    content = content.encode('utf-8')
    L = len(content)

    start_response('200 OK',
            [
                ('Content-Length', str(L)),
                ('Content-Type', 'text/html; charset=utf-8'),
            ])
    return [content]

def app(env, start_response):
    path = env['PATH_INFO']

    if path == '/':
        return slide(env, start_response)

    with open(path[1:]) as f:
        data = f.read()

    if path.lower().endswith(('.jpg', '.jpeg')):
        content_type = 'image/jpeg'
    elif path.lower().endswith('.png'):
        content_type = 'image/png'
    else:
        content_type = 'text/plain'

    start_response('200 OK', [
                ('Content-Length', str(len(data))),
                ('Content-Type', content_type)
                ])
    return [data]

WSGIServer(('127.0.0.1', 8001), app).serve_forever()
