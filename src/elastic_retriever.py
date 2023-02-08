from retriever import Retriever
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from elasticsearch import RequestsHttpConnection
from elasticsearch_dsl import Document, Text, connections, Integer, Date, Float, Keyword, Join, Long, Object, Mapping, Nested
from elasticsearch.helpers import bulk
from datetime import datetime
import schema
import sys
import os
import glob
import dateutil.parser
from mergedeep import merge
import json
import hashlib
import logging

logging.basicConfig(format='%(levelname)s :: %(asctime)s :: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
es_logger = logging.getLogger('elasticsearch')
es_logger.setLevel(logging.WARNING)

if "ES_INDEX" in os.environ:
    INDEX = os.environ["ES_INDEX"]
else:
    INDEX = "askem-object-07"

def json_extract(obj):
    """Recursively fetch values from nested JSON."""
    arr = []
    sarr = ""
    ignore_keys = ['_id', 'ASKEM_ID', '_xdd_created', '_xdd_registrant', "ASKEM_CLASS"]

    def extract(obj, arr, sarr):
        """Recursively search for values of key in JSON tree."""

        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    arr, sarr = extract(v, arr, sarr)
                else:
                    if k not in ignore_keys:
                        arr.append(v)
                        sarr += f" {v}"
                    else:
                        continue
        elif isinstance(obj, list):
            for item in obj:
                arr, sarr = extract(item, arr, sarr)
        return arr, sarr

    values, svalues = extract(obj, arr, sarr)
    return values, svalues

def upsert(doc: Document) -> dict:
    d = doc.to_dict(True)
    d['_op_type'] = 'update'
    d['doc'] = d['_source']
    d['_index'] = doc.Index().name
    d['doc_as_upsert'] = True
    d['_id'] = d["_source"].pop("id")
    del d['_source']
    return d

class ASKEMObject(Document):
    """
    ASKEM_ID:uuid
    ASKEM_CLASS:ASKEM_Ontology_type
    PROPERTIES:[key:value]
    DOMAIN_TAGS:[kg_version:domain_id]
    RAW_DATA:JSON
    EXTERNAL_URL:URL
    """
    class Index:
        name=INDEX



class ASKEMThing(ASKEMObject):
    """
    primaryName:Text
    description:Text
    rawData:JSON
    """

class ASKEMTerm(Document):
    """
    primaryName:Text
    description:Text
    sourceID:Text
    source:Text
    synymoms[Text]
    """

class ASKEMFigure(Document):
    """
    caption:Text
    documentID:ASKEM_ID
    documentTitle:Text
    contentText:Text
    image:JPG
    sectionTitle:Text
    sectionID:ASKEM_ID
    relevantSentences:[Text]
    """

class ASKEMTable(Document):
    """
    caption:Text
    documentID:ASKEM_ID
    documentTitle:Text
    contentText:Text
    contentJSON:JSON
    image:JPG
    sectionTitle:Text
    sectionID:ASKEM_ID
    relevantSentences:[Text]
    """

class ASKEMSection(Document):
    """
    title:Text
    documentID:ASKEM_ID
    documentTitle:Text
    contentText:Text
    indexInDocument:Integer
    """

class ASKEMDocument(Document):
    """
    title:Text
    DOI:Text
    treustScore:Numeric
    abstract:Text
    _XDDID:Text
    """
    class index:
        name='askem-document'

class ASKEMFunctionNetwork(Document):
    """
    primaryName:Text
    description:Text
    gromet:JSON
    """
    class Index:
        name='askem-functionnetwork'

class ASKEMParameter(Document):
    """
    primaryName:Text
    description:Text
    value:Numerical
    unit:Text
    rawLocation:Text
    populationMetadata:Text
    """
    class Index:
        name='askem-parameter'

class ASKEMScenario(Document):
    """
    description:Text
    consideredModel:ASKEM_ID
    consideredModelName:Text
    rawTime:Text
    rawLocation:Text
    populationMetadata:Text
    """
    class index:
        name='askem-scenario'

class ASKEMModel(Document):
    """
    primaryName:Text
    description:Text
    hasParameter:ASKEM_ID
    allParameters:[Text]
    functionNetwork:ASKEM_ID
    """
    class index:
        name='askem-model'



class ElasticRetriever(Retriever):
    def __init__(self, hosts=['localhost']):
        if os.path.exists("/mnt/es_certs"):
            connections.create_connection(hosts=hosts, timeout=100, alias="default", use_ssl=True, verify_certs=True, ca_certs="/mnt/es_certs/ca.crt",  http_auth=(os.getenv("ES_USER"), os.getenv("ES_PASSWORD")))
        else:
            connections.create_connection(hosts=hosts, timeout=100)

    def search(self, query: dict) -> dict:
        doc_filter = False
        s = Search(index=INDEX)
        s.source(exclude=["_all"])
        s = s.query(query)
        response = s.execute()
        return response

    def search_metadata(self,
            askem_class: str = "",
            domain_tag: str = "",
            count: bool = False,
            ndocs: int = 30,
            page: int = 0,
            qmatch: bool = False,
            include_highlights: bool = False,
            **kwargs) -> dict:
        q = Q()

        hfields = []
        no_highlight_fields = ["ASKEM_CLASS", "DOMAIN_TAGS"]

        # deprecated parameters, originally added by hand
        if askem_class:
            q = q & Q('match', ASKEM_CLASS=askem_class)
        if domain_tag:
            q = q & Q('match', DOMAIN_TAGS=domain_tag)

        # schema-derived searching
        for key, value in kwargs.items():
            if key in schema.BASE_PROPERTIES:
                ql = []
                for v in value.split(","):
                    ql.append(Q('match', **{f"{key}": v}))
                    if key not in no_highlight_fields: hfields.append(key)
                q = q & Q('bool', should=ql)
            elif key=="query_all":
                q = q & Q('match', **{"_all": value})
                hfields.append("_all")
            else:
                if qmatch:
                    ql = []
                    for v in value.split(","):
                        ql.append(Q('match', **{f"properties__{key}": v}))
                        hfields.append(f"properties.{key}")
                    q = q & Q('bool', should=ql)

                else:
                    ql = []
                    for v in value.split(","):
                        ql.append(Q('match_phrase', **{f"properties__{key}": v}))
                        hfields.append(f"properties.{key}")
                    q = q & Q('bool', should=ql)

        s = Search(index=INDEX)
        s.source(exclude=["_all"])
        start = page * ndocs
        end = start + ndocs
        logger.info(f"Getting results {start}-{end}")
        if count:
            return s.query(q).count()
        s = s.query(q)[start:end]
        if include_highlights:
            s = s.highlight(*hfields,  pre_tags='<em class="hl">', post_tags = '</em>')
        response = s.execute()
        final_results = []
        for r in response:
            obj = self.get_object(r.meta.id)
            if include_highlights:
                highlights = []
                if "highlight" not in r.meta: continue
                for k, v in r.meta.highlight.to_dict().items():
                    highlights+=v
                obj["_highlight"] = highlights
            final_results.append(obj)
        return final_results


    def get_object(self, id: str):
        try:
            if id=="all":
                s = Search(index=INDEX)
                s.source(exclude=["_all"])
                return [e.to_dict() for e in s.scan()]
            obj = ASKEMObject.get(id=id, _source_excludes=["_all"]).to_dict()
        except:

            logger.warning(sys.exc_info())
            logger.warning(f"Couldn't get ASKEMObject with id {id}!")
            obj = None
        return obj

    def get_mappings(self):
        properties = {}
        subproperties = {}
        for prop in schema.BASE_KEYWORD_PROPERTIES:
            properties[prop] = {"type" : "keyword"}
        for prop in schema.BASE_INTEGER_PROPERTIES:
            properties[prop] = {"type" : "integer"}
        for prop in schema.BASE_OBJECT_PROPERTIES:
            properties[prop] = {"type" : "object"}
        for prop in schema.BASE_TEXT_PROPERTIES:
            properties[prop] = {"type" : "text"}
        for prop in schema.KEYWORD_PROPERTIES:
            subproperties[prop] = {"type" : "keyword"}
        for prop in schema.TEXT_PROPERTIES:
            subproperties[prop] = {"type" : "text"}
        for prop in schema.OBJECT_PROPERTIES:
            subproperties[prop] = {"type" : "object"}
        for prop in schema.NUMERICAL_PROPERTIES:
            subproperties[prop] = {"type" : "double"}
        for prop in schema.INTEGER_PROPERTIES:
            subproperties[prop] = {"type" : "long"}
        for prop in schema.BINARY_PROPERTIES:
            subproperties[prop] = {"type" : "binary"}
        properties["_all"] = {"type" : "text"}
        # Mildly annoying that the mapping parlance and our chosen parlance are the same here..
        properties['properties'] = {"properties" : subproperties}
        return properties

    def create_index(self):
        logger.info('Building elastic index')
        es= connections.get_connection()
        if not es.indices.exists(INDEX):
            mapping = {
                "mappings": {
                    "_source" : { "enabled" : True },
                    "properties" : self.get_mappings(),
                    'dynamic': False,
                    "dynamic_templates": [
                        {
                            "only_index_metadata": {
                                "path_match": "metadata*",
                                "mapping": {
                                    "dynamic": "true"
                                    }
                                }
                            }
                        ]
                    }
                }
            es.indices.create(INDEX, body=mapping) # TODO: put in settings.
            logger.info("Index initialized.")

#        docs = glob.glob(f"{input_dir}/*.json")
#        logger.info(f"Ingesting {len(docs)} documents.")
#        to_ingest = []
#        for f in docs:
#            logger.info(f'Ingesting {f}')
#            data = json.load(open(f))
#
#            # I'm loading these manually, so set registrant appropriately
#            data["_xdd_registrant"] = 1
#            data["_xdd_created"] = datetime.now()
#            data["_xdd_modified"] = []
#
#            # TODO: get askem-ids
#            data["askem_id"] = "1"
#            data["_id"] = data["askem_id"]
#
#            test = ASKEMObject(**data)
#            to_ingest.append(test) # for now, just expand the whole thing with no changes
#        bulk(connections.get_connection(), [upsert(d) for d in to_ingest])

    def add_object(self, data: dict) -> int:
        # TODO (eventually) : check data consistency
        test, stest = json_extract(data)
        data["_all"] = stest

        test = ASKEMObject(**data)
        try:
            test.save()
        except:
            logging.error(sys.exc_info())
            return 1
        return 0

    def modify_object(self, oid, data:dict) -> int:
        '''
        Assume that we're just appending to existing metadata?
        Can users delete metadata?
        '''

        data["id"] = oid
        # make sure that dates are being stored as datetimes - if source of truth is postgres,
        # they're strings due to issues serializing of datetime

        for i, mdate in enumerate(data["_xdd_modified"]):
            if isinstance(mdate, datetime):
                data["_xdd_modified"][i] = mdate
            else:
                data["_xdd_modified"][i] = dateutil.parser.parse(mdate)

        test = ASKEMObject(**data)
        logging.info(test.to_dict().keys())
        bulk(connections.get_connection(), [upsert(test)])

        return 0


    def count(self, index:str):
        s = Search(index=index)
        return s.count()

    def delete(self):
        raise NotImplementedError('TODO')

    def rerank(self):
        raise NotImplementedError('ElasticRetriever does not rerank results')
