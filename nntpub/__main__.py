
import asyncio

from .nntprotocol import NNTPServer

def main():
    server = NNTPServer( '0.0.0.0' )
    asyncio.run( server.listen() )

if '__main__' == __name__:
    main()
