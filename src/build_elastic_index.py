import click
from elastic_retriever import ElasticRetriever
import os

@click.command()
@click.option('--input_dir', type=str, help='', default='/input/')
@click.option('--host', type=str, help='', default='localhost')
def run(host, input_dir):
    ret = ElasticRetriever(hosts=[host])
    print('Connected to retriever, building indices')
    ret.build_index(input_dir)
    print('Done building index')

if __name__ == '__main__':
    run()
