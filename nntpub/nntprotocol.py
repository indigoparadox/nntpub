
import logging
import asyncio
from datetime import datetime

class NNTPNotFoundException( Exception ):
    pass

class NNTPClientHandler( object ):

    def __init__( self,
        rfile : asyncio.streams.StreamReader,
        wfile : asyncio.streams.StreamWriter
    ):
        # TODO: Client ID.
        self.logger = logging.getLogger( 'nntproto.client' )
        self.rfile = rfile
        self.wfile = wfile
        self.running = True
        self.nntp_group = None
    
    def change_group( self, group_name : str ):
        self.logger.debug( 'using group: %s', group_name )
        self.nntp_group = group_name

    def write_line( self, line : str ):
        self.logger.debug( 'writing: %s', line )
        self.wfile.write( line.encode( 'utf8' ) + b'\r\n' )

class NNTPServer( object ):

    def __init__( self, server_address, server_port, **kwargs ):
        self.server_address = server_address
        self.logger = logging.getLogger( 'nntproto.server' )
        self.domain = 'nntp.example.com'
        self.server_port = server_port
        if 'domain' in kwargs:
            self.domain = kwargs['domain']
        self.groups = {
            'control': {'desc': 'News server internal group', 'msg': []},
            'junk': {'desc': 'News server internal group', 'msg': [
                {'id': 7, 'subject': 'foo', 'body': 'test msg 1\r\nyo!', 'from': 'fromguy'},
                {'id': 8, 'subject': 'fii', 'body': 'test msg 2\r\nhello!', 'from': 'fromotherguy'}
            ]}
        }

    async def listen( self ):
        self.server = await asyncio.start_server( self._handle_client, self.server_address, self.server_port )
        async with self.server:
            await self.server.serve_forever()

    def send_banner( self, client : NNTPClientHandler ):
        # TODO: Indicate if posting allowed with 200.
        client.write_line( f'201 %s NNTPub' % self.domain )

    def send_list( self, client : NNTPClientHandler ):

        client.write_line( '215 Descriptions in form "group description"' )
        for group in self.groups:
            client.write_line( f'%s %s' % (group, self.groups[group]['desc']) )
        client.write_line( '.' )

    def send_group_meta( self, client : NNTPClientHandler, group_name : str ):
        if not group_name in self.groups:
            self.logger.warning( 'invalid group requested: %s', group_name )
            client.write_line( '411 No such group' )
            raise NNTPNotFoundException
        
        group_len = len( self.groups[group_name]['msg'] )
        if 0 >= group_len:
            client.write_line( f'211 0 0 0 %s' % (group_name,) )
            return
        
        client.write_line( f'211 %d %d %d %s' % \
            (group_len, 
            self.groups[group_name]['msg'][0]['id'], 
            self.groups[group_name]['msg'][-1]['id'], 
            group_name) )
        
    def send_group_list( self, client : NNTPClientHandler, group_name: str, start : int, end : int = -1 ):
        if not group_name:
            self.logger.warning( 'no group selected' )
            client.write_line( '412 No newsgroup currently selected' )
            raise NNTPNotFoundException
        
        client.write_line( '224 Overview information follows' )
        
        in_range = False
        for msg in self.groups[group_name]['msg']:
            if start == msg['id'] or (-1 == start and end == msg['id']):
                in_range = True
            if in_range:
                # TODO: Lines field should count lines?
                client.write_line( '\t'.join(
                    [NNTPServer._clean_field( x ) for x in \
                        [str( msg['id'] ), msg['subject'], msg['from'], str( datetime.now() ),
                        f'<%d@%s>' % (msg['id'], self.domain), '',
                            str( len( NNTPServer._clean_field( msg['body'] ) ) ), '1']] ) )
            if end == msg['id']:
                in_range = False
                
        client.write_line( '.' )

    def send_article( self, client : NNTPClientHandler, group_name : str, msg_id : int ):
        if not group_name:
            self.logger.warning( 'no group selected' )
            client.write_line( '412 No newsgroup currently selected' )
            raise NNTPNotFoundException
        
        # TODO: More efficient ID retrieval.
        for msg in self.groups[group_name]['msg']:
            if msg['id'] != msg_id:
                continue

            client.write_line( f'220 %d <%d@%s>' % (msg['id'], msg['id'], self.domain) )
            client.write_line( f'From: %s' % (msg['from'],) )
            client.write_line( f'Subject: %s' % (msg['subject'],) )
            client.write_line( f'Date: %s' % (str( datetime.now()),) )
            client.write_line( f'Message-ID: <%d@%s>' % (msg['id'],self.domain) )
            client.write_line( '' )
            for line in msg['body'].split( '\r\n' ):
                client.write_line( line )
            client.write_line( '.' )

            # Message displayed; go home!
            return
        
        # Could not find message.
        self.logger.warning( 'invalid message number: %d', msg_id )
        client.write_line( '423 No message with that number' )
        raise NNTPNotFoundException

    @staticmethod
    def _clean_field( field : str ):
        return field.replace( '\r\n', '' ).replace( '\t', ' ' )

    async def _handle_client( self, rfile, wfile ):
    
        line = None
        client = NNTPClientHandler( rfile, wfile )

        self.send_banner( client )

        while client.running:
            line = (await rfile.readline())
            line = line.decode( 'utf8' ).strip()
            if 'MODE READER' == line:
                self.logger.debug( 'capabilities requested' )
                self.send_banner( client )

            elif 'LIST' == line:
                self.logger.debug( 'list requested' )
                self.send_list( client )

            elif line.startswith( 'LIST' ):
                self.logger.warning( 'unsupported list: %s', line )
                client.write_line( '503 Data item not stored' )

            elif line.startswith( 'GROUP' ):
                line_arr = line.split( ' ' )
                self.logger.debug( 'group info requested: %s', line )
                try:
                    self.send_group_meta( client, line_arr[1] )
                    nntp_group = line_arr[1]
                except NNTPNotFoundException:
                    pass
            
            elif line.startswith( 'XOVER' ):
                # TODO: Santize inputs.
                self.logger.debug( 'group list requested: %s', line )
                line_arr = line.split( ' ' )
                if line_arr[1].endswith( '-' ):
                    # Grab all messages remaining.
                    try:
                        self.send_group_list( client, nntp_group, int( line_arr[1] ) )
                    except NNTPNotFoundException:
                        pass
                elif '-' in line_arr[1]:
                    # Send a specific range.
                    line_range = line_arr[1].split( '-' )
                    try:
                        self.send_group_list( client, nntp_group, int( line_range[0] ), end=int( line_range[1] ) )
                    except NNTPNotFoundException:
                        pass
                else:
                    # Send a single message.
                    try:
                        self.send_group_list( client, nntp_group, -1, end=int( line_arr[1] ) )
                    except NNTPNotFoundException:
                        pass

            elif line.startswith( 'ARTICLE' ):
                self.logger.debug( 'group list requested: %s', line )
                line_arr = line.split( ' ' )
                try:
                    self.send_article( client, nntp_group, int( line_arr[1] ) )
                except NNTPNotFoundException:
                    pass

            elif '' != line:
                logging.warning( 'unknown command: "%s"', line )

            else:
                logging.info( 'hanging up' )
                return
