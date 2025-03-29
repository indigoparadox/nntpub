
import logging
import asyncio
from datetime import datetime

class NNTPNotFoundException( Exception ):
    pass

class NNTPServer( object ):

    def __init__( self, server_address, server_port, **kwargs ):
        self.server_address = server_address
        self.logger = logging.getLogger( 'nntproto' )
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

    def send_banner( self, wfile ):
        # TODO: Indicate if posting allowed with 200.
        NNTPServer._write_line( wfile, f'201 %s NNTPub' % self.domain )

    def send_list( self, wfile ):

        NNTPServer._write_line( wfile, '215 Descriptions in form "group description"' )
        for group in self.groups:
            NNTPServer._write_line( wfile, f'%s %s' % (group, self.groups[group]['desc']) )
        NNTPServer._write_line( wfile, '.' )

    def send_group_meta( self, wfile, group_name : str ):
        if not group_name in self.groups:
            self.logger.warning( 'invalid group requested: %s', group_name )
            NNTPServer._write_line( wfile, '411 No such group' )
            raise NNTPNotFoundException
        
        group_len = len( self.groups[group_name]['msg'] )
        if 0 >= group_len:
            NNTPServer._write_line( wfile, f'211 0 0 0 %s' % (group_name,) )
            return
        
        NNTPServer._write_line( wfile, f'211 %d %d %d %s' % \
            (group_len, 
            self.groups[group_name]['msg'][0]['id'], 
            self.groups[group_name]['msg'][-1]['id'], 
            group_name) )
        
    def send_group_list( self, wfile, group_name: str, start : int, end : int = -1 ):
        if not group_name:
            self.logger.warning( 'no group selected' )
            NNTPServer._write_line( wfile, '412 No newsgroup currently selected' )
            raise NNTPNotFoundException
        
        NNTPServer._write_line( wfile, '224 Overview information follows' )
        
        in_range = False
        for msg in self.groups[group_name]['msg']:
            if start == msg['id'] or (-1 == start and end == msg['id']):
                in_range = True
            if in_range:
                # TODO: Lines field should count lines?
                NNTPServer._write_line( wfile, '\t'.join(
                    [NNTPServer._clean_field( x ) for x in \
                        [str( msg['id'] ), msg['subject'], msg['from'], str( datetime.now() ),
                        f'<%d@%s>' % (msg['id'], self.domain), '',
                            str( len( NNTPServer._clean_field( msg['body'] ) ) ), '1']] ) )
            if end == msg['id']:
                in_range = False
                
        NNTPServer._write_line( wfile, '.' )

    def send_article( self, wfile, group_name : str, msg_id : int ):
        if not group_name:
            self.logger.warning( 'no group selected' )
            NNTPServer._write_line( wfile, '412 No newsgroup currently selected' )
            raise NNTPNotFoundException
        
        # TODO: More efficient ID retrieval.
        for msg in self.groups[group_name]['msg']:
            if msg['id'] != msg_id:
                continue

            self._write_line( wfile, f'220 %d <%d@%s>' % (msg['id'], msg['id'], self.domain) )
            self._write_line( wfile, f'From: %s' % (msg['from'],) )
            self._write_line( wfile, f'Subject: %s' % (msg['subject'],) )
            self._write_line( wfile, f'Date: %s' % (str( datetime.now()),) )
            self._write_line( wfile, f'Message-ID: <%d@%s>' % (msg['id'],self.domain) )
            self._write_line( wfile, '' )
            for line in msg['body'].split( '\r\n' ):
                self._write_line( wfile, line )
            self._write_line( wfile, '.' )

            # Message displayed; go home!
            return
        
        # Could not find message.
        self.logger.warning( 'invalid message number: %d', msg_id )
        NNTPServer._write_line( wfile, '423 No message with that number' )
        raise NNTPNotFoundException

    @staticmethod
    def _clean_field( field : str ):
        return field.replace( '\r\n', '' ).replace( '\t', ' ' )

    @staticmethod
    def _write_line( wfile, line : str ):
        logger = logging.getLogger( 'nntproto.line' )
        logger.debug( line )
        wfile.write( line.encode( 'utf8' ) + b'\r\n' )

    async def _handle_client( self, rfile, wfile ):
    
        line = None
        running = True
        nntp_group = None

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
                self.logger.warning( 'unsupported list: %s', line )
                NNTPServer._write_line( wfile, '503 Data item not stored' )

            elif line.startswith( 'GROUP' ):
                line_arr = line.split( ' ' )
                self.logger.debug( 'group info requested: %s', line )
                try:
                    self.send_group_meta( wfile, line_arr[1] )
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
                        self.send_group_list( wfile, nntp_group, int( line_arr[1] ) )
                    except NNTPNotFoundException:
                        pass
                elif '-' in line_arr[1]:
                    # Send a specific range.
                    line_range = line_arr[1].split( '-' )
                    try:
                        self.send_group_list( wfile, nntp_group, int( line_range[0] ), end=int( line_range[1] ) )
                    except NNTPNotFoundException:
                        pass
                else:
                    # Send a single message.
                    try:
                        self.send_group_list( wfile, nntp_group, -1, end=int( line_arr[1] ) )
                    except NNTPNotFoundException:
                        pass

            elif line.startswith( 'ARTICLE' ):
                self.logger.debug( 'group list requested: %s', line )
                line_arr = line.split( ' ' )
                try:
                    self.send_article( wfile, nntp_group, int( line_arr[1] ) )
                except NNTPNotFoundException:
                    pass

            elif '' != line:
                logging.warning( 'unknown command: "%s"', line )
