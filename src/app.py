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
import psycopg2
import base64
from collections import OrderedDict
from functools import wraps
from src.elastic_retriever import ElasticRetriever
logging.basicConfig(format='%(levelname)s :: %(asctime)s :: %(message)s', level=logging.DEBUG)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.url_map.strict_slashes = False
app.retriever=ElasticRetriever(hosts=os.environ.get('ELASTIC_ADDRESS', "es01:9200"))
bp = Blueprint('xDD-gromet-api', __name__)

# TODO: get ride of this obvious placeholder
KNOWN_MODELS=[]

def table_exists(cur, table_name):
    """
    Check if a table exists in the current database
    :cur: psql cursort
    :table_name: Name of table to search for.
    :returns: True if it exists, False if not
    """
    cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' """)
    for table in cur.fetchall():
        logging.info(table[0])
        if table_name == table[0]:
            return True
        else:
            continue
    return False

if "POSTGRES_HOST" in os.environ:
    host = os.environ["POSTGRES_HOST"]
else:
    host = 'aske-id-registration'

if "POSTGRES_USER" in os.environ:
    user = os.environ["POSTGRES_USER"]
else:
    user = 'zalando'

# Init postgres db if needed
cconn = psycopg2.connect(host=host, user=user, password=os.environ["POSTGRES_PASSWORD"], database='aske_id')
cconn.autocommit = True
ccur = cconn.cursor()

if not table_exists(ccur, "registrant"):
    ccur.execute("""
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """)
    cconn.commit()
    ccur.execute("""
        CREATE TABLE registrant (
            id SERIAL PRIMARY KEY,
            registrant text,
            api_key uuid DEFAULT uuid_generate_v4()
        );""")
    cconn.commit()
ccur.close()
cconn.close()

def response(fcn):
    def wrapper(*args, **kwargs):
        tresult = fcn(*args, **kwargs)
        # TODO: catch non-successes.
        result = {"success": {'v' : 1, 'data': tresult, 'license' : "https://creativecommons.org/licenses/by-nc/2.0/"}}
        return jsonify(result)
    return wrapper

@bp.route('/', defaults={'model_id': None})
@bp.route('/<model_id>')
@bp.route('/<model_id>/')
@response
def get_model(model_id):
    metadata_type = request.args.get('metadata_type', type=str)

    if model_id is None:
        if metadata_type is not None:
            logging.info("Searching by metadata type")
            res = app.retriever.search_metadata(metadata_type=metadata_type)
            return res
        else:
            results_obj = {
                    "description" : "..."
                    }
            return results_obj
    else :
        res = app.retriever.get_object(model_id)
        logging.info(f"res type {type(res)}")
        return [res]

if 'PREFIX' in os.environ:
    logging.info(f"Stripping {os.environ['PREFIX']}")
    app.register_blueprint(bp, url_prefix=os.environ['PREFIX'])
else:
    logging.info("No prefix stripped.")
    app.register_blueprint(bp)
CORS(app)

#if __name__ == '__main__':
#    app.run(debug=True,host='0.0.0.0', port=80)
