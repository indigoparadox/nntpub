
from typing import Generator
from datetime import datetime

from . import NewsSource, NewsGroup

class RandomGroup( NewsGroup ):
    def __init__( self, name, desc ):
        super().__init__( name, desc )
        self._msgs = [
            {'id': 7, 'subject': 'foo', 'body': 'test msg 1\r\nyo!', 'from': 'fromguy', 'date': datetime.now()},
            {'id': 8, 'subject': 'fii', 'body': 'test msg 2\r\nhello!', 'from': 'fromotherguy', 'date': datetime.now()}
        ]

    def __getitem__( self, key ):
        return {x['id']: x for x in self._msgs}[key]
    
    def __contains__( self, key ):
        return key in [x['id'] for x in self._msgs]
    
    def __iter__( self ):
        for msg in self._msgs:
            yield msg

    def get_first_msg( self ):
        return self._msgs[0]
    
    def get_last_msg( self ):
        return self._msgs[-1]

    def count_messages( self ):
        return len( self._msgs )

class RandomSource( NewsSource ):

    def __init__( self, **kwargs ):
        super().__init__( **kwargs )
        self._groups = [
            RandomGroup( 'control', 'News server internal group' ),
            RandomGroup( 'junk', 'News server internal group' )
        ]
    
    def __getitem__( self, key ) -> RandomGroup:
        return {x.name: x for x in self._groups}[key]
    
    def __contains__( self, key ):
        return key in [x.name for x in self._groups]
    
    def __iter__( self ) -> Generator[RandomGroup, None, None]:
        for group in self._groups:
            yield group
