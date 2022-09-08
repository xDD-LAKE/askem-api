import os
import sys
import logging
from datetime import datetime
import json
from uuid import uuid4, UUID
from typing import Type
from functools import wraps
import psycopg2
from psycopg2.extras import execute_values
from flask import Flask, request, Blueprint
from flask import jsonify
from flask_cors import CORS
from elastic_retriever import ElasticRetriever
import routes
logging.basicConfig(format='%(levelname)s :: %(asctime)s :: %(message)s', level=logging.DEBUG)

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.url_map.strict_slashes = False
app.retriever=ElasticRetriever(hosts=os.environ.get('ES_HOST', "es01:9200"))
bp = Blueprint('xDD-askem-api', __name__)

# TODO: get ride of this obvious placeholder
KNOWN_MODELS=[]
VERSION = 1

def get_registrant_id(api_key):
    conn = psycopg2.connect(host=host, user=user, password=os.environ["POSTGRES_PASSWORD"], database=os.environ["POSTGRES_DB"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT id FROM registrant WHERE api_key=%(api_key)s", {"api_key" : api_key})
    registrant_id = cur.fetchone()
    if registrant_id is None:
        return None
    return registrant_id[0]

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
    return False

def save_object(oid: UUID, obj: dict, registrant_id:UUID, conn:Type[psycopg2.extensions.connection]) -> tuple:
    '''
    Assumes all registrant ID checks have been done.
    '''

    # write to postgres, getting an OID back if needed.
    cur = conn.cursor()
    if oid is None:
        cur.execute("INSERT INTO object (data, registrant_id) VALUES (%(data)s, %(registrant_id)s) RETURNING id", {"data" : obj, "registrant_id" : registrant_id})
        oid = cur.fetchone()[0]
        conn.commit()
    else:
        cur.execute("UPDATE object SET data=%(data)s WHERE id=%(oid)s", {"data" : obj, "oid": oid})
        conn.commit()

    # also write it to ES
    obj = json.loads(obj)
    obj['_id'] = oid
    obj['askem_id'] = oid
    obj['_xdd_created'] = datetime.now()
    obj['_xdd_registrant'] = registrant_id
    check = app.retriever.add_object(obj)
    if check != 0:
        return (-1,oid)
    return (0,oid)

def check_path_exists(original, update):
    pip 


tif "POSTGRES_HOST" in os.environ:
    host = os.environ["POSTGRES_HOST"]
else:
    host = 'aske-id-registration'

if "POSTGRES_USER" in os.environ:
    user = os.environ["POSTGRES_USER"]
else:
    user = 'zalando'

# Init postgres db if needed
cconn = psycopg2.connect(host=host, user=user, password=os.environ["POSTGRES_PASSWORD"], database=os.environ["POSTGRES_DB"])
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

if not table_exists(ccur, "update"):
    ccur.execute("""
        CREATE TABLE update (
            id SERIAL PRIMARY KEY,
            oid uuid REFERENCES object(id),
            user_id integer REFERENCES registrant(id),
            data jsonb DEFAULT NULL,
            timestamp timestamp DEFAULT now()
        );""")
    cconn.commit()
ccur.close()
cconn.close()
def response(fcn):
    def wrapper(*args, **kwargs):
        tresult = fcn(*args, **kwargs)
        if "error" in tresult:
            result = {"error": {'v' : VERSION, 'message': tresult["error"], "about": routes.helptext[fcn.__name__], 'license' : "https://creativecommons.org/licenses/by-nc/2.0/"}}
        elif fcn.__name__ == "index":
            ver = {'v': VERSION}
            lic = {'license' : "https://creativecommons.org/licenses/by-nc/2.0/"}
            result = {"success": {**ver, **tresult, **lic}}
        else:
            # TODO: this won't quite match the usual structure, since the "data" field implies successful request
            result = {"success": {'v' : VERSION, 'data': tresult, 'license' : "https://creativecommons.org/licenses/by-nc/2.0/"}}
        return jsonify(result)
    wrapper.__name__ = fcn.__name__ #wrapper name shenanigans: https://stackoverflow.com/questions/17256602/assertionerror-view-function-mapping-is-overwriting-an-existing-endpoint-functi
    return wrapper

def require_apikey(fcn):
    @wraps(fcn)
    def decorated_function(*args, **kwargs):
        headers = request.headers
        api_key = headers.get('x-api-key', default = None)
        if request.method == "GET" and len(request.args) == 0 and len(args) == 0 and len(kwargs) == 0: # if bare request, show the helptext even without an API key
            return fcn(*args, **kwargs)
        if api_key is None:
            api_key = request.args.get('api_key', default=None)
        if api_key is None:
            return {"error" :
                    {
                        "message" : "You must specify an API key!",
                        "about" : routes.helptext[fcn.__name__]
                    }
                    }
        registrant_id = get_registrant_id(api_key)
        if registrant_id is None:
            return {"error" :
                    {"message" : "Provided API key not allowed to reserve ASKEM-IDs!",
                        "about" : routes.helptext[fcn.__name__]
                        }
                    }
        return fcn(*args, **kwargs)
    return decorated_function



@bp.route('/', methods=["GET"])
@response
def index():
    return {
                "description" : "API for reserving or registering JSON objects for storage within the xDD system.",
                "routes": {
                    f"/reserve" : "Reserve a block of ASKEM-IDs for later registration.",
                    f"/register" : "Register a location for a reserved ASKEM-ID.",
                    f"/create" : "Create and register ASKEM-IDs for existing resources.",
                    f"/object" : "Retrieve or search for an object."
                    }
        }

@bp.route('/object', defaults={'object_id': None})
@bp.route('/object/<object_id>')
@bp.route('/object/<object_id>/')
@response
def get_object(object_id):
    if len(request.args) == 0 and object_id is None:
        return routes.helptext['object']
    metadata_type = request.args.get('metadata_type', type=str, default="")
    source_title = request.args.get('source_title', type=str, default="")
    provenance_method = request.args.get('provenance_method', type=str, default="")

    object_id = request.args.get('object_id', type=str, default=None) if object_id is None else object_id

    if "all" in request.args:
        object_id = "all"

    if object_id is None:
        if metadata_type is not None:
            logging.info("Searching by metadata type")
            res = app.retriever.search_metadata(metadata_type=metadata_type,
                    source_title=source_title,
                    provenance_method=provenance_method)
            return res
        return routes.helptext['object']
    res = app.retriever.get_object(object_id)
    if not isinstance(res, list):
        res = [res]
    return res

@bp.route('/create', methods=["POST", "GET"])
@response
@require_apikey
def create():
    if request.method == "GET":
        return routes.helptext["create"]
    try:
        objects = request.get_json()
    except:
        return {"error" : "Invalid body! Please pass in valid JSON."}

    api_key = request.headers.get('x-api-key', default = None)
    if api_key is None:
        api_key = request.args.get('api_key', default=None)
    reg_id = get_registrant_id(api_key)

    conn = psycopg2.connect(host=host, user=user, password=os.environ["POSTGRES_PASSWORD"], database=os.environ["POSTGRES_DB"])
    conn.autocommit = True
    cur = conn.cursor()
    registered = []
    if isinstance(objects, dict):
        objects = [objects]
    for obj in objects:
        obj = json.dumps(obj)
        try:
            success, oid = save_object(None, obj, reg_id, conn)
            if success == -1:
                return {"error" : f"Could not create object with ID {oid} in xDD indexer!"}
            registered.append(oid)
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
@response
@require_apikey
def reserve():
    if request.method == "GET":
        return routes.helptext['reserve']

    headers = request.headers
    api_key = headers.get('x-api-key', default = None)
    if api_key is None:
        api_key = request.args.get('api_key', default=None)

    n_requested = request.args.get('n', default=10)
    if not isinstance(n_requested, int):
        n_requested = int(n_requested)

    conn = psycopg2.connect(host=host, user=user, password=os.environ["POSTGRES_PASSWORD"], database=os.environ["POSTGRES_DB"])
    conn.autocommit = True
    cur = conn.cursor()

    registrant_id = get_registrant_id(api_key)

    uuids = [str(uuid4()) for i in range(n_requested)]

    # TODO : catch foreign key exception
    execute_values(cur,
        "INSERT INTO object (id, registrant_id) VALUES %s",
        [(uuid, registrant_id) for uuid in uuids])
    conn.commit()
    cur.close()
    conn.close()
    return {"success" : {"reserved_ids" : uuids}}

@bp.route('/register', methods=["POST", "GET"])
@response
@require_apikey
def register():
    if request.method == "GET":
        logging.info("???" + str(routes.helptext['register']))
        return routes.helptext['register']

    headers = request.headers
    api_key = headers.get('x-api-key', default = None)
    if api_key is None:
        api_key = request.args.get('api_key', default=None)
    try:
        objects = request.get_json()
    except:
        return {"error" : "Invalid body! Registration expects a JSON object of the form [[<ASKEM-ID>, <location>], [<ASKEM-ID>, <location>]]."}

    registered = []
    conn = psycopg2.connect(host=host, user=user, password=os.environ["POSTGRES_PASSWORD"], database=os.environ["POSTGRES_DB"])
    conn.autocommit = True
    cur = conn.cursor()
    for oid, obj  in objects:
        logging.info(f"Registering {oid}")
        # TODO: maybe get all oids this key can register and do the check in-memory instead of against the DB?
        try:
            cur.execute("SELECT r.id FROM registrant r, object o WHERE o.registrant_id=r.id AND r.api_key=%(api_key)s AND o.id=%(oid)s", {"api_key" : api_key, "oid" : oid})
            registrant_id = cur.fetchone()[0] # we can get this otherwise, but we need to check the object_id/registrant_id validity
            if registrant_id is None:
                return {"error" : f"Provided API key not allowed to register {oid}!"}
            obj = json.dumps(obj)
            success, oid = save_object(oid, obj, registrant_id, conn)
            if success == -1:
                return {"error" : f"Could not register object with ID {oid} in xDD indexer!"}
            registered.append(oid)
        except:
            logging.info(f"Couldn't register {oid}.")
            logging.info(sys.exc_info())
            conn.commit()
    cur.close()
    conn.close()
    return {"success" : {
            "registered_ids" : registered
            }
            }

@bp.route('/update', methods=["POST", "GET"])
@response
@require_apikey
def update():
    allowed_ops = ["ADD", "CHANGE", "DELETE", "APPEND"]
    if request.method == "GET":
        logging.info("???" + str(routes.helptext['update']))
        return routes.helptext['update']

    headers = request.headers
    api_key = headers.get('x-api-key', default = None)
    if api_key is None:
        api_key = request.args.get('api_key', default=None)
    try:
        body = request.get_json()
        assert "operation" in body and body['operation'] in allowed_ops
        assert "id" in body
        assert "data" in body
    except:
        logging.info(sys.exc_info())
        logging.info(body)
        return {"error" : f"Invalid body! Updating expects a JSON object of the form {{'id' : '<ASKEM-ID>', 'operation' : {str(allowed_ops)}, 'data': {{'field': 'value''}}}}'"}

    conn = psycopg2.connect(host=host, user=user, password=os.environ["POSTGRES_PASSWORD"], database=os.environ["POSTGRES_DB"])
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT data FROM object WHERE id=%(oid)s", {"oid": body['id']})
    logging.info(f"{body['operation']}-ing {body['id']} with {body['data']}")
    old = cur.fetchone()[0]
    if body["operation"] in ["ADD", "CHANGE"]: # functionally the same, but change should also check for the field existence to be sure that the user is aware that they're changing a thing..
        check_path_exists(old, body['data'])
        old.update(body["data"])

    logging.info(old)



#    old.update(data) will update the old dictionary.


    # ADD - implies adding data to an array *OR* creating a new field

    # TODO: Check for object existence.
    # TODO: parse field nesting and check validity
    # TODO: update JSON within postgres
    # TODO: update JSON in elasticsearch
    # TODO: write to updates table

    try:
        raise NotImplementedError
#        cur.execute("SELECT r.id FROM registrant r, object o WHERE o.registrant_id=r.id AND r.api_key=%(api_key)s AND o.id=%(oid)s", {"api_key" : api_key, "oid" : oid})
#        registrant_id = cur.fetchone()[0] # we can get this otherwise, but we need to check the object_id/registrant_id validity
#        if registrant_id is None:
#            return {"error" : f"Provided API key not allowed to register {oid}!"}
#        obj = json.dumps(obj)
#        success, oid = save_object(oid, obj, registrant_id, conn)
#        if success == -1:
#            return {"error" : f"Could not register object with ID {oid} in xDD indexer!"}
#            registered.append(oid)
        reg_id = get_registrant_id(api_key)
        cur.execute("INSERT INTO update (user_id, oid, data) VALUES (%(regid)s, %(oid), %(data)s);", {"data" : body['data'], "oid": body['id'], "reg_id": reg_id})
    except:
        logging.info(f"Couldn't update {body['id']}.")
        logging.info(sys.exc_info())
        conn.commit()
    cur.close()
    conn.close()
    return {"success" : body
            }




if 'PREFIX' in os.environ:
    logging.info(f"Stripping {os.environ['PREFIX']}")
    app.register_blueprint(bp, url_prefix=os.environ['PREFIX'])
else:
    logging.info("No prefix stripped.")
    app.register_blueprint(bp)
CORS(app)

#if __name__ == '__main__':
#    app.run(debug=True,host='0.0.0.0', port=80)
