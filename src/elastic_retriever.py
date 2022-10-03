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
        name='askem-object'



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
        s = Search(index='askem-object')
        s = s.query(query)
        response = s.execute()
        return response

    def search_metadata(self,
            askem_class: str = "",
            domain_tag: str = "",
            metadata_type: str = "",
            source_title: str = "",
            provenance_method: str = "",
            **kwargs) -> dict:
        q = Q()

        # top-level searching
        if askem_class:
            q = q & Q('match', ASKEM_CLASS=askem_class)
        if domain_tag:
            q = q & Q('match', DOMAIN_TAGS=domain_tag)
        for key, value in kwargs.items():
            logger.info(f"Adding {key}:{value} to the query")
            q = q & Q('match_phrase', **{f"properties__{key}": value})

        # below are from pre-schema days
        if metadata_type:
            q = q & Q('match', metadata__metadata_type=metadata_type)
        if source_title:
            q = q & Q('match_phrase', metadata__documents__bibjson__title=source_title)
        if provenance_method:
            q = q & Q('match_phrase', metadata__provenance__method=provenance_method)
        # ---
        logger.info(q.to_dict())
        s = Search(index='askem-object')
        s = s.query(q)
        response = s.execute()
        final_results = [r.meta.id for r in response]
        final_results = [self.get_object(i) for i in final_results]
        return final_results


    def get_object(self, id: str):
        try:
            if id=="all":
                s = Search(index='askem-object')
                return [e.to_dict() for e in s.scan()]
            obj = ASKEMObject.get(id=id).to_dict()
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
        for prop in schema.BASE_OBJECT_PROPERTIES:
            properties[prop] = {"type" : "object"}
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
        # Mildly annoying that the mapping parlance and our chosen parlance are the same here..
        properties['properties'] = {"properties" : subproperties}
        return properties

    def create_index(self):
        logger.info('Building elastic index')
        es= connections.get_connection()
        if not es.indices.exists("askem-object"):
            mapping = {
                "mappings": {
                    "_source" : { "enabled" : True },
                    "properties" : self.get_mappings()
                }
                }
            es.indices.create("askem-object", body=mapping) # TODO: put in settings.
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
