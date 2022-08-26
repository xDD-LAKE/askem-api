from flask import Flask, request, abort, Blueprint
from flask import jsonify
from flask_cors import CORS
import logging
import glob
import os
import sys
import uuid
import random
import datetime
import subprocess
from threading import Thread
import json
import base64
from collections import OrderedDict
logging.basicConfig(format='%(levelname)s :: %(asctime)s :: %(message)s', level=logging.DEBUG)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.url_map.strict_slashes = False
bp = Blueprint('xDD-gromet-api', __name__)

# TODO: get ride of this obvious placeholder
KNOWN_MODELS=[]

@bp.route('/', defaults={'model_id': None})
@bp.route('/<model_id>')
@bp.route('/<model_id>/')
def get_model(model_id):
    if model_id is None:
        results_obj = {
                "description" : "..."
                }
        return jsonify(results_obj)
    else :
        if model_id not in KNOWN_MODELS:
            return {"error" : "Set undefined!"}
        return jsonify({})

if 'PREFIX' in os.environ:
    logging.info(f"Stripping {os.environ['PREFIX']}")
    app.register_blueprint(bp, url_prefix=os.environ['PREFIX'])
else:
    logging.info("No prefix stripped.")
    app.register_blueprint(bp)
CORS(app)

#if __name__ == '__main__':
#    app.run(debug=True,host='0.0.0.0', port=80)
