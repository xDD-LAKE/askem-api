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
from xdd.SetHelper import SetHelper
logging.basicConfig(format='%(levelname)s :: %(asctime)s :: %(message)s', level=logging.DEBUG)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.url_map.strict_slashes = False
bp = Blueprint('xDD-gromet-api', __name__)

products = {}
product_files = glob.glob("products/*.json")
for f in product_files:
    data = json.load(open(f))
    products[data['name'].lower()] = data


# TODO: get ride of this obvious placeholder
KNOWN_MODELS=[]

@bp.route('/', defaults={'model_id': None})
@bp.route('/<model_id>')
@bp.route('/<model_id>/')
def get_model(model_id):
    if model_id is None:
        results_obj = {
                "description" : "Sets are a (still in development) construct within xDD creating a way for users to define, search, and interact with a set of documents within the xDD corpus. These sets may be defined by topic, keywords, journals, or simply a list of DOIs. Browse to any of the sets listed below (e.g. /sets/xdd-covid-19) for the set definitions along with available products created from each.",
                "available_sets" : list(sets.keys())
                }
        return jsonify(results_obj)
    else :
        if model_id not in KNOWN_MODELS:
            return {"error" : "Set undefined!"}
        return jsonify(sets[model_id])

if 'PREFIX' in os.environ:
    logging.info(f"Stripping {os.environ['PREFIX']}")
    app.register_blueprint(bp, url_prefix=os.environ['PREFIX'])
else:
    logging.info("No prefix stripped.")
    app.register_blueprint(bp)
CORS(app)

#if __name__ == '__main__':
#    app.run(debug=True,host='0.0.0.0', port=80)
