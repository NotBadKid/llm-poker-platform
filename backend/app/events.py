from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# 1. A dictionary to track which clients have an active loop
#    We will store {sid: True}
active_loops = {}


def background_loop_task(sid):
    """
    A background task that runs a loop for a specific client (sid).
    It will stop when the client's sid is no longer in 'active_loops'.
    """
    print(f"Starting background loop for {sid}")
    count = 0
    try:
        # Loop *only* as long as this client is in our tracking dict
        while sid in active_loops:
            # IMPORTANT: Use socketio.sleep()!
            # time.sleep() is blocking and will still freeze your server
            # if you are using async workers (like gevent or eventlet).
            # socketio.sleep() yields control correctly.
            socketio.sleep(1)
            count += 1

            print(f"Emitting loop message {count} to {sid}")

            # Emit *only* to the client who started this task
            # by using room=sid.
            socketio.emit('server_loop_message',
                          {'data': f'This is message number {count}'},
                          room=sid)
    except Exception as e:
        print(f"Error in background task for {sid}: {e}")
    finally:
        # Clean up when the loop ends
        print(f"Stopping background loop for {sid}")
        active_loops.pop(sid, None)


# --- Event Handlers ---

@socketio.on('start_loop')
def handle_start_loop(json_data):
    sid = request.sid
    print(f"Received 'start_loop' from {sid}: {json_data}")

    if sid not in active_loops:
        active_loops[sid] = True

        socketio.start_background_task(background_loop_task, sid)
    else:
        print(f"Loop already running for {sid}")


@socketio.on('stop_loop')
def handle_stop_loop(json_data):
    sid = request.sid
    if sid in active_loops:
        print(f"Received 'stop_loop' from {sid}. Stopping loop.")
        active_loops.pop(sid, None)


@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in active_loops:
        print(f"Client {sid} disconnected. Stopping their loop.")
        active_loops.pop(sid, None)

