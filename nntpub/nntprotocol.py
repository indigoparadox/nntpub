
import socketserver

NNTP_STATE_INIT = 0

class NNTPSession( socketserver.StreamRequestHandler ):

    def handle( self ):

        self.nntp_state = NNTP_STATE_INIT

        self.wfile.write( '200 news.nntpub.example.com NNTPub news\r\n' )

        while line = self.rfile.readline( 10000 ).rstrip():
            print( line )

class NNTPServer( socketserver.TCPServer ):

    def __init__( self, server_address, bind_and_activate = True ):
        super().__init__( server_address, NNTPSession, bind_and_activate )
