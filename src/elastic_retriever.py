from src.retriever import Retriever
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from elasticsearch import RequestsHttpConnection
from elasticsearch_dsl import Document, Text, connections, Integer, Date, Float, Keyword, Join, Long, Object, Mapping, Nested
from elasticsearch.helpers import bulk
import glob
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
    d['_id'] = str(doc.get_id())
    del d['_source']
    return d

class GrometFN(Document):
    class Index:
        name='gromet-fn'
    def get_id(self):
        return 1

class ElasticRetriever(Retriever):
    def __init__(self, hosts=['localhost']):
        self.hosts = hosts

    def search(self, query: dict) -> dict:
        connections.create_connection(hosts=self.hosts, timeout=20)
        doc_filter = False
        s = Search(index='gromet-fn')
        s = s.query(query)
        response = s.execute()
        return response

    def search_metadata(self, metadata_type: str = "") -> dict:
        q = Q('match', metadata__metadata_type=metadata_type)
        s = Search(index='gromet-fn')
        s = s.query(q)
        response = s.execute()
        final_results = [r.meta.id for r in response]
        final_results = [self.get_object(i) for i in final_results]
        return final_results


    def get_object(self, id: str):
        connections.create_connection(hosts=self.hosts)
        try:
            obj = GrometFN.get(id=id).to_dict()
        except:
            logger.warning(f"Couldn't get GrometFN with id {id}!")
            obj = None
        return obj

    def build_index(self, input_dir):
        logger.info('Building elastic index')
        connections.create_connection(hosts=self.hosts)

        es= connections.get_connection()
        if not es.indices.exists("gromet-fn"):
                mapping = {
                    "mappings": {
                        "_source" : { "enabled" : True },
                        "properties" : {
                            }
                        }
                    }
                # TODO: dump a real working mapping and use that
                es.indices.create("gromet-fn", body=mapping) # TODO: put in settings.
                logger.info("Index initialized.")

        docs = glob.glob(f"{input_dir}/*.json")
        logger.info(f"Ingesting {len(docs)} documents.")
        to_ingest = []
        for f in docs:
            logger.info(f'Ingesting {f}')
            data = json.load(open(f))
            test = GrometFN(**data)
            to_ingest.append(test) # for now, just expand the whole thing with no changes
        bulk(connections.get_connection(), [upsert(d) for d in to_ingest])

    def count(self, index:str):
        connections.create_connection(hosts=self.hosts)
        s = Search(index=index)
        return s.count()

    def delete(self):
        raise NotImplementedError('TODO')

    def rerank(self):
        raise NotImplementedError('ElasticRetriever does not rerank results')
