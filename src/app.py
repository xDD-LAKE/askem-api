from flask import Flask, request, abort, Blueprint
from flask import jsonify
from flask_cors import CORS
import logging
import glob
import os
import sys
import uuid
import random
from datetime import datetime
import subprocess
from threading import Thread
import json
import psycopg2
from uuid import uuid4, UUID
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
VERSION = 1

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

if not table_exists(ccur, "object"):
    ccur.execute("""
        CREATE TABLE object (
            id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
            registrant_id integer REFERENCES registrant(id),
            data jsonb DEFAULT NULL
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

@bp.route('/object', defaults={'model_id': None})
@bp.route('/object/<model_id>')
@bp.route('/object/<model_id>/')
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


@bp.route('/create', methods=["POST", "GET"])
def create():
    helptext = {
            "v" : VERSION,
            "description": "Create and register a new ASKE-ID.",
            "options" : {
                "parameters" : {
                    "api_key" : "(required) API key assigned to an ASKE-ID registrant. Can also be passed as a header in the 'x-api-key' field."
                    },
                "body" : "POSTed request body must be a JSON object of the form [json1, json2].",
                "methods" : ["POST"],
                "output_formats" : ["json"],
                "fields" : {
                    "registered_ids" : "Array of successfully registered ASKE-IDs."
                    },
                "examples": []
                }
            }
    if request.method == "GET":
        return {"success" : helptext}

    headers = request.headers
    api_key = headers.get('x-api-key', default = None)
    if api_key is None:
        api_key = request.args.get('api_key', default=None)
        logging.info(f"got api_key from request.args")
    if api_key is None:
        return {"error" :
                {
                    "message" : "You must specify an API key!",
                    "v" : VERSION,
                    "about" : helptext
                }
                }
    try:
        objects = request.get_json()
    except:
        return {"error" :
                {
                    "message" : "Invalid body! Registration expects a JSON object of the form [<location>, <location>] or [[<location>, <description>], [<location>, <description>], ...].",
                    "v" : VERSION,
                    "about" : helptext
                }
                }

    conn = psycopg2.connect(host=host, user=user, password=os.environ["POSTGRES_PASSWORD"], database='aske_id')
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT id FROM registrant WHERE api_key=%(api_key)s", {"api_key" : api_key})
    reg_id = cur.fetchone()[0]
    if reg_id is None:
        cur.close()
        conn.close()
        return {"error" :
                {
                    "message" : "Invalid API key!",
                    "v" : VERSION,
                    "about" : helptext
                }
                }

    registered = []
    if isinstance(objects, dict):
        objects = [objects]
    for obj in objects:
        logging.info(f"{type(obj)}")
        obj = json.dumps(obj)
        logging.info(f"{type(obj)}")
        try:
            cur.execute("INSERT INTO object (data, registrant_id) VALUES (%(data)s, %(registrant_id)s) RETURNING id", {"data" : obj, "registrant_id" : reg_id})
            oid = cur.fetchone()[0]
            conn.commit()
            registered.append(oid)

            # also write it to ES
            obj = json.loads(obj)
            obj['_id'] = oid
            obj['askem_id'] = oid
            obj['_xdd_created'] = datetime.now()
            obj['_xdd_registrant'] = reg_id
            app.retriever.add_object(obj)

        except:
            logging.info(f"Couldn't register {obj}.")
            logging.info(sys.exc_info())
            conn.commit()
    cur.close()
    conn.close()
    return {"success" : {
            "registered_ids" : registered
        }
        }


@bp.route('/reserve', methods=["GET", "POST"])
def reserve():
    helptext = {
            "v" : VERSION,
            "description": "Reserve a block of ASKE-IDs for later registration.",
            "options" : {
                "parameters" : {
                    "api_key" : "(required) API key assigned to an ASKE-ID registrant. Can also be passed as a header in the 'x-api-key' field.",
                    "n" : "(option, int, default 10) Number of ASKE-IDs to reserve."
                    },
                "methods" : ["POST"],
                "output_formats" : ["json"],
                "fields" : {
                    "reserved_ids" : "List of unique ASKE-IDs reserved for usage by the associated registrant API key."
                    },
                "examples": []
                }
            }

    if request.method == "GET":
        return {"success" : helptext}

    headers = request.headers
    api_key = headers.get('x-api-key', default = None)
    if api_key is None:
        api_key = request.args.get('api_key', default=None)
    try:
        check = UUID(api_key)
    except ValueError:
        check = False

    if api_key is None or check is False:
        return {"error" :
                {
                    "message" : "You must specify a valid API key!",
                    "v" : VERSION,
                    "about" : helptext
                }
                }

    n_requested = request.args.get('n', default=10)
    if not isinstance(n_requested, int):
        n_requested = int(n_requested)

    conn = psycopg2.connect(host=host, user=user, password=os.environ["POSTGRES_PASSWORD"], database='aske_id')
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT id FROM registrant WHERE api_key=%(api_key)s", {"api_key" : api_key})
    registrant_id = cur.fetchone()
    if registrant_id is None:
        cur.close()
        conn.close()
        return {"error" :
                {"message" : "Provided API key not allowed to reserve ASKE-IDs!",
                    "v": VERSION,
                    "about" : helptext
                    }
                }

    uuids = [str(uuid4()) for i in range(n_requested)]

    # TODO : catch foreign key exception
    execute_values(cur,
        "INSERT INTO object (id, registrant_id) VALUES %s",
        [(uuid, registrant_id) for uuid in uuids])
    conn.commit()
    cur.close()
    conn.close()
    return {"success" : True, "reserved_ids" : uuids}

if 'PREFIX' in os.environ:
    logging.info(f"Stripping {os.environ['PREFIX']}")
    app.register_blueprint(bp, url_prefix=os.environ['PREFIX'])
else:
    logging.info("No prefix stripped.")
    app.register_blueprint(bp)
CORS(app)

#if __name__ == '__main__':
#    app.run(debug=True,host='0.0.0.0', port=80)
