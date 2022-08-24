import click
from elastic_retriever import ElasticRetriever
import os

@click.command()
@click.option('--host', type=str, help='', default='localhost')
def run(host):
    ret = ElasticRetriever(hosts=[host])
    print('Connected to retriever, building indices')
    ret.build_index()
    print('Done building index')

if __name__ == '__main__':
    run()
