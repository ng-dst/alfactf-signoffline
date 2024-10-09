import gevent.monkey
gevent.monkey.patch_all()

import logging
from flask import Flask
from .routes import main

logging.basicConfig(level=logging.INFO, 
                    format='[%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
                    
def create_app():
    app = Flask(__name__)
    app.register_blueprint(main)
                    
    app.json.ensure_ascii = False
    app.config["JSONIFY_MIMETYPE"] = "application/json; charset=utf-8"
    
    return app

