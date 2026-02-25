# # # run.py
# # from app import create_app

# # app = create_app()

# # if __name__ == "__main__":
# #     print("Starting Banking Agent API...")
# #     app.run(host="0.0.0.0", port=5000, debug=False)

# # run.py
# import os
# import sys
# from app import create_app

# # Must be first — fix Windows console before any imports
# if sys.platform == "win32":
#     import io
#     # Reinitialize stdout/stderr with error handling
#     if hasattr(sys.stdout, 'buffer'):
#         sys.stdout = io.TextIOWrapper(
#             sys.stdout.buffer,
#             encoding='utf-8',
#             errors='replace',
#             line_buffering=True
#         )
#     if hasattr(sys.stderr, 'buffer'):
#         sys.stderr = io.TextIOWrapper(
#             sys.stderr.buffer,
#             encoding='utf-8',
#             errors='replace',
#             line_buffering=True
#         )

# # Clear log file on startup
# with open("agent.log", "w") as f:
#     f.write("=== Agent started ===\n")

# print("Starting Banking Agent API...")



# app = create_app()

# @app.errorhandler(Exception)
# def handle_exception(e):
#     import traceback
#     from flask import jsonify
#     error = traceback.format_exc()
#     with open("agent.log", "a") as f:
#         f.write(f"[FLASK ERROR] {error}\n")
#     return jsonify({"error": "Internal server error", "detail": str(e)}), 500

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

# run.py
import os
import sys
import io

# ── Fix Windows stdout BEFORE any imports ──────────────────
if sys.platform == "win32":
    # Reopen stdout/stderr with error replacement
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(
            sys.stderr.buffer,
            encoding='utf-8',
            errors='replace',
            line_buffering=True
        )

# ── Silence transformers/tokenizers warnings ───────────────
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["SENTENCE_TRANSFORMERS_HOME"] = "./models/minilm"

# Clear log
with open("agent.log", "w") as f:
    f.write("=== Agent started ===\n")

from app import create_app

app = create_app()

@app.errorhandler(Exception)
def handle_exception(e):
    import traceback
    from flask import jsonify
    error = traceback.format_exc()
    with open("agent.log", "a") as f:
        f.write(f"[FLASK ERROR] {error}\n")
    return jsonify({"error": "Internal server error", "detail": str(e), "trace": error}), 500

if __name__ == "__main__":
    with open("agent.log", "a") as f:
        f.write("Starting Banking Agent API...\n")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)