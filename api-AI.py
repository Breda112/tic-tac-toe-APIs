from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import tictactoe as ttt

app = Flask(__name__)
CORS(app, origins="*")  # Allow frontend origin for CORS

socketio = SocketIO(app, cors_allowed_origins="*")  # Allow Socket.IO connections from frontend

# In-memory store for active rooms
active_rooms = {}

@app.route("/api/initial_state", methods=["GET"])
def initial_state():
    return jsonify(ttt.initial_state())

# Handle room creation
@socketio.on("create_room")
def handle_create_room(data):
    username = data.get("username")
    room_id = data.get("room_id")

    if not room_id or not username:
        emit("error", {"message": "Room ID and username are required."})
        return

    # Check if the user is already in a room
    for existing_room_id, room in list(active_rooms.items()):
        if username in room["players"]:
            # If the user is already in a room, delete that room
            print(f"User {username} is in room {existing_room_id}. Deleting the old room.")
            del active_rooms[existing_room_id]
            emit("room_deleted", {"message": f"Your previous room {existing_room_id} has been deleted."}, to=username)
            break

    # Check if room already exists
    if room_id in active_rooms:
        emit("error", {"message": "Room ID already exists."})
        return

    # Create the room and add the first player
    active_rooms[room_id] = {
        "players": [username],
        "board": None,  # Don't send the board yet
        "current_player": username,
        "game_started": False,  # Game hasn't started yet
    }
    join_room(room_id)
    emit("room_created", {"message": f"Room {room_id} created by {username}."}, to=room_id)
    print(f"Room {room_id} created by {username}. Current rooms: {list(active_rooms.keys())}")

# Handle room joining
@socketio.on("join_room")
def handle_join_room(data):
    room_id = data.get("room_id")
    username = data.get("username")
    
    if room_id not in active_rooms:
        emit("error", {"message": f"Room {room_id} does not exist."})
        return
    
    room = active_rooms[room_id]
    
    if len(room["players"]) >= 2:
        emit("error", {"message": "Room is full. Cannot join."})
        return
    
    room["players"].append(username)
    join_room(room_id)
    
    # Notify the room that the second player has joined
    emit("room_joined", {
        "message": f"{username} joined room {room_id}",
        "room_id": room_id
    }, to=room_id)

    # Send the board to the second player immediately upon joining
    if room["board"] is None:
        room["board"] = ttt.initial_state()  # Initialize the board when the second player joins

    # Always send the current board and player turn to the second player
    emit("update_game", {
        "board": room["board"],
        "current_player": room["current_player"],
        "terminal": ttt.terminal(room["board"]),
        "winner": ttt.winner(room["board"])
    }, to=room_id)

    # If both players have joined, start the game
    if len(room["players"]) == 2:
        room["game_started"] = True
        emit("game_started", {
            "message": "Game started! First player to move.",
            "current_player": room["current_player"]
        }, to=room_id)

@socketio.on("make_move")
def handle_make_move(data):
    room_id = data.get("room_id")
    username = data.get("username")
    action = data.get("action")

    if room_id not in active_rooms:
        emit("error", {"message": "Room does not exist."})
        return
    
    room = active_rooms[room_id]
    
    if room["current_player"] != username:
        emit("error", {"message": "Not your turn!"})
        return
    
    if not room["game_started"]:
        emit("error", {"message": "Game has not started yet."})
        return
    
    board = room["board"]
    try:
        new_board = ttt.result(board, tuple(action))
        room["board"] = new_board
        room["current_player"] = room["players"][0] if room["current_player"] == room["players"][1] else room["players"][1]
        emit("update_game", {
            "board": new_board,
            "current_player": room["current_player"],
            "terminal": ttt.terminal(new_board),
            "winner": ttt.winner(new_board)
        }, to=room_id)

        # Check if the game has ended and notify the players
        if ttt.terminal(new_board):
            emit("game_over", {
                "message": "The game is over!",
                "winner": ttt.winner(new_board)
            }, to=room_id)

    except Exception as e:
        emit("error", {"message": str(e)})

# Reset the game by clearing the board, setting the current player back to the first player, and starting the game
@socketio.on("reset_game")
def handle_reset_game(data):
    room_id = data.get("room_id")
    room = active_rooms.get(room_id)
    
    if room:
        room["board"] = ttt.initial_state()  # Reset the board
        room["current_player"] = room["players"][0]  # Set the current player back to the first player
        room["game_started"] = False  # Game is not started yet
        emit("reset_game", {
            "message": "The game has been reset! Ready to start a new game."
        }, to=room_id)

        # After reset, automatically start the game
        room["game_started"] = True  # Set game started flag
        emit("game_started", {
            "message": "Game started! First player to move.",
            "current_player": room["current_player"]
        }, to=room_id)

        print(f"Game in room {room_id} has been reset and started.")

# Handle disconnection
@socketio.on('disconnect')
def handle_disconnect():
    for room_id, room in list(active_rooms.items()):
        # Check if the user was part of the room using username, not socket id
        if request.sid in room['players']:
            username = room['players'].remove(request.sid)  # Remove user from players list
            leave_room(room_id)
            
            # If no players are left, delete the room
            if len(room['players']) == 0:
                del active_rooms[room_id]
                emit("room_deleted", {"message": f"Room {room_id} has been deleted because both players disconnected."})
                print(f"Room {room_id} deleted due to both players disconnecting.")
            break

if __name__ == "__main__":
    socketio.run(app, debug=True, port=5001)  # Now the server will run on port 5001
