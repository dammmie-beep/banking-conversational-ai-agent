# # app/routes.py
# from flask import Blueprint, request, jsonify
# from app.agent import run_agent
# from app.memory import session_store
# import uuid

# bp = Blueprint("api", __name__)


# @bp.route("/health", methods=["GET"])
# def health():
#     return jsonify({"status": "ok", "message": "Banking Agent is running."})


# @bp.route("/chat", methods=["POST"])
# def chat():
#     """
#     Request body:
#     {
#         "session_id": "optional-string",   // omit to start new session
#         "message": "I want to block my card"
#     }
#     """
#     body = request.get_json()
#     if not body or "message" not in body:
#         return jsonify({"error": "Missing 'message' field."}), 400

#     session_id = body.get("session_id") or str(uuid.uuid4())
#     user_message = body["message"].strip()

#     if not user_message:
#         return jsonify({"error": "Message cannot be empty."}), 400

#     response = run_agent(session_id, user_message)

#     return jsonify({
#         "session_id": session_id,
#         "response": response
#     })


# @bp.route("/session/<session_id>/clear", methods=["DELETE"])
# def clear_session(session_id: str):
#     """Clear conversation history for a session."""
#     if session_id in session_store:
#         session_store[session_id].clear()
#         return jsonify({"message": "Session cleared."})
#     return jsonify({"error": "Session not found."}), 404


# @bp.route("/session/<session_id>/history", methods=["GET"])
# def get_history(session_id: str):
#     """Retrieve conversation history for a session."""
#     if session_id in session_store:
#         history = session_store[session_id].get_history()
#         return jsonify({"session_id": session_id, "history": history})
#     return jsonify({"error": "Session not found."}), 404


# app/routes.py
from flask import Blueprint, request, jsonify
from app.agent import run_agent
from app.memory import session_store
import uuid
import sys
import traceback

bp = Blueprint("api", __name__)


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Banking Agent is running."})


@bp.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True, silent=True)

    if not body:
        return jsonify({"error": "Invalid or missing JSON body."}), 400

    if "message" not in body:
        return jsonify({"error": "Missing 'message' field."}), 400

    session_id = body.get("session_id") or str(uuid.uuid4())
    user_message = body["message"].strip()

    if not user_message:
        return jsonify({"error": "Message cannot be empty."}), 400

    try:
        response = run_agent(session_id, user_message)
        return jsonify({
            "session_id": session_id,
            "response": response
        })
    except Exception as e:
        error_detail = traceback.format_exc()
        sys.__stdout__.write(f"[ERROR] {error_detail}\n")
        sys.__stdout__.flush()
        return jsonify({
            "error": "Agent failed",
            "detail": str(e),
            "trace": error_detail
        }), 500


@bp.route("/session/<session_id>/clear", methods=["DELETE"])
def clear_session(session_id: str):
    if session_id in session_store:
        session_store[session_id].clear()
        return jsonify({"message": "Session cleared."})
    return jsonify({"error": "Session not found."}), 404


@bp.route("/session/<session_id>/history", methods=["GET"])
def get_history(session_id: str):
    if session_id in session_store:
        history = session_store[session_id].get_history()
        return jsonify({"session_id": session_id, "history": history})
    return jsonify({"error": "Session not found."}), 404