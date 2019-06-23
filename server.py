import eventlet
import socketio

from shyr import shyr

sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={
    '/': {'content_type': 'text/html', 'filename': 'index.html'}
})

# async def index(request):
#   """Serve the client-side application."""
#   with open('index.html') as f:
#     return web.Response(text=f.read(), content_type='text/html')

@sio.event
def connect(sid, environ):
  print("connect ", sid)

@sio.event
def message(sid, data):
  print("message ", data)
  shyr.util.sid = sid
  shyr.util.sio = sio
  shyr.main()

@sio.event
def disconnect(sid):
  print('disconnect ', sid)

# app.router.add_static('/static', 'static')
# app.router.add_get('/', index)

if __name__ == '__main__':
  # web.run_app(app)
  eventlet.wsgi.server(eventlet.listen(('', 5000)), app)
