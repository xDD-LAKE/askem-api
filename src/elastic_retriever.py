from retriever import Retriever
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections
from elasticsearch import RequestsHttpConnection
from elasticsearch_dsl import Document, Text, connections, Integer, Float, Keyword, Join
from elasticsearch.helpers import bulk
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
    d['_id'] = str(doc['_id'])
    del d['_source']
    return d

class GrometFN(Document):
    cls = Text(fields={'raw': Keyword()})
    detect_score = Float()
    postprocess_score = Float()
    dataset_id = Text(fields={'raw': Keyword()})
    header_content = Text()
    content = Text()
    context_from_text = Text()
    full_content = Text()
    local_content = Text()
    area = Integer()
    pdf_name = Text(fields={'raw': Keyword()})
    img_pth = Text(fields={'raw': Keyword()})
    class meta:
        index='gromet-fn'


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

    def get_object(self, id: str):
        if self.awsauth is not None:
            connections.create_connection(hosts=self.hosts,
                                          http_auth=self.awsauth,
                                          use_ssl=True,
                                          verify_certs=True,
                                          connection_class=RequestsHttpConnection
                                          )
        else:
            connections.create_connection(hosts=self.hosts)
        try:
            obj = GrometFN.get(id=id)
        except:
            obj = None
        return obj

    def build_index(self):
        logger.info('Building elastic index')
        connections.create_connection(hosts=self.hosts)
        GrometFN.init(index="gromet-fn")
        # TODO: Read + index documents.

    def count(self, index:str):
        connections.create_connection(hosts=self.hosts)
        s = Search(index=index)
        return s.count()

    def delete(self):
        raise NotImplementedError('TODO')

    def rerank(self):
        raise NotImplementedError('ElasticRetriever does not rerank results')
