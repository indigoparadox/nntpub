
import logging
import asyncio

NNTP_STATE_INIT = 0

class NNTPServer( object ):

    def __init__( self, server_address, server_port, **kwargs ):
        self.server_address = server_address
        self.logger = logging.getLogger( 'nntproto' )
        self.domain = 'nntp.example.com'
        self.server_port = server_port
        if 'domain' in kwargs:
            self.domain = kwargs['domain']
        self.groups = [
            {'name': 'control', 'desc': 'News server internal group'},
            {'name': 'junk', 'desc': 'News server internal group'}
        ]

    async def listen( self ):
        self.server = await asyncio.start_server( self._handle_client, self.server_address, self.server_port )
        async with self.server:
            await self.server.serve_forever()

    def send_banner( self, wfile ):
        # TODO: Indicate if posting allowed with 200.
        wfile.write( b'201 ' + self.domain.encode( 'utf8' ) + b' NNTPub\r\n' )

    def send_list( self, wfile ):

        wfile.write( b'215 Descriptions in form "group description"\r\n' )
        for group in self.groups:
            wfile.write( group['name'].encode( 'utf8' ) + b' ' + \
                group['desc'].encode( 'utf8' ) + b'\r\n' )
        wfile.write( b'.\r\n' )

    async def _handle_client( self, rfile, wfile ):
    
        line = None
        running = True
        nntp_state = NNTP_STATE_INIT

        self.send_banner( wfile )

        while running:
            line = (await rfile.readline())
            line = line.decode( 'utf8' ).strip()
            if 'MODE READER' == line:
                self.logger.debug( 'capabilities requested' )
                self.send_banner( wfile )

            elif 'LIST' == line:
                self.logger.debug( 'list requested' )
                self.send_list( wfile )

            elif line.startswith( 'LIST' ):
                self.logger.debug( 'unsupported list: %s', line )
                wfile.write( b'503 Data item not stored' )

            elif '' != line:
                logging.warning( 'unknown command: "%s"', line )
