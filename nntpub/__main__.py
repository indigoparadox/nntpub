
import argparse
import logging
import asyncio
from configparser import ConfigParser
from importlib import import_module

from .nntprotocol import NNTPServer
from .sources.random import RandomSource

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument( '-c', '--config', default='nntpub.ini' )

    parser.add_argument( '-v', '--verbose', action='store_true' )

    args = parser.parse_args()

    # Setup logging.
    level = logging.INFO
    if args.verbose:
        level = logging.DEBUG
    logging.basicConfig( level=level )
    logger = logging.getLogger( 'main' )

    # Setup config.
    config = ConfigParser()
    config.read( args.config )

    listen_addr = '0.0.0.0'
    try:
        listen_addr = config['nntp']['listen']
    except:
        logger.warning( 'no listen address specified; using %s', listen_addr )

    listen_port = 119
    try:
        listen_port = config['nntp']['port']
    except:
        logger.warning( 'no listen port specified; using %d', listen_port )

    source_mod = import_module( 'nntpub.sources.' + config['source']['module'] )
    src_config = dict( config['source'] )
    source = source_mod.SOURCE_CLASS( **src_config )

    # Setup server.
    nntp_config = dict( config['nntp'] )
    server = NNTPServer( listen_addr, listen_port, source, **nntp_config )
    asyncio.run( server.listen() )

if '__main__' == __name__:
    main()
