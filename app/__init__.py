# # app/__init__.py
# from flask import Flask
# from app.routes import bp

# def create_app():
#     app = Flask(__name__)
#     app.register_blueprint(bp, url_prefix="/api")
#     return app

# app/__init__.py
import os
import logging

# Suppress noisy loggers globally
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from flask import Flask
from app.routes import bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp, url_prefix="/api")
    return app