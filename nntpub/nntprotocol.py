
import asyncio

NNTP_STATE_INIT = 0

class NNTPServer( object ):

    def __init__( self, server_address ):
        self.server_address = server_address

    async def listen( self ):
        self.server = await asyncio.start_server( self._handle_client, self.server_address, 60119 )
        async with self.server:
            await self.server.serve_forever()

    def send_banner( self, wfile ):
        wfile.write( b'200 news.nntpub.example.com NNTPub news\r\n' )

    def send_list( self, wfile ):

        wfile.write( b'215 Descriptions in form "group description"\r\n' )
        wfile.write( b'control News server internal group\r\n' )
        wfile.write( b'junk News server internal group\r\n' )
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
                self.send_banner( wfile )

            if 'LIST' == line:
                self.send_list( wfile )

            elif '' != line:
                print( line )
