import eventlet
import socketio

from shyr import shyr

sio = socketio.Server()
app = socketio.WSGIApp(sio, static_files={'/': 'index.html'})

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

if __name__ == '__main__':
  eventlet.wsgi.server(eventlet.listen(('', 8000)), app)
