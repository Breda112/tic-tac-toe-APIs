from flask import Flask, jsonify, request , g
import tictactoe as ttt
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app, origin('*')) 

# Middleware to measure execution time
@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_execution_time(response):
    if hasattr(g, "start_time"):
        execution_time = time.time() - g.start_time
        print(f"Endpoint: {request.path}, Method: {request.method}, Execution Time: {execution_time:.4f} seconds")
    return response

@app.route("/api/initial_state", methods=["GET"])
def initial_state():
    return jsonify(ttt.initial_state())

@app.route("/api/player", methods=["POST"])
def player():
    board = request.json["board"]
    return jsonify({"next_player": ttt.player(board)})

@app.route("/api/actions", methods=["POST"])
def actions():
    board = request.json["board"]
    return jsonify({"actions": list(ttt.actions(board))})

@app.route("/api/result", methods=["POST"])
def result():
    board = request.json["board"]
    action = request.json["action"]
    try:
        new_board = ttt.result(board, tuple(action))
        return jsonify(new_board)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/winner", methods=["POST"])
def winner():
    board = request.json["board"]
    return jsonify({"winner": ttt.winner(board)})

@app.route("/api/terminal", methods=["POST"])
def terminal():
    board = request.json["board"]
    return jsonify({"terminal": ttt.terminal(board)})

@app.route("/api/minimax", methods=["POST"])
def minimax():
    board = request.json["board"]
    if ttt.terminal(board):
        return jsonify({"action": None})
    action = ttt.minimax(board)
    return jsonify({"action": action})

if __name__ == "__main__":
    app.run(debug=True)
