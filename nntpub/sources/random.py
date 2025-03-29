
import random
import time
from typing import Generator

from . import NewsSource, NewsGroup

RAND_SUBJECTS = ['I', 'We', 'They', 'None of them', 'All of them']
RAND_VERBS = ['like', 'see', 'understand', 'run on', 'drop', 'drive', 'dislike']
RAND_OBJECTS = ['cows', 'birds', 'manga', 'space', 'words', 'honks']
RAND_TERMS = ['.', '...', '!', '?']
RAND_VOWELS = ['a', 'i', 'u', 'e', 'o']
RAND_CONSONANTS = ['k', 's', 'm', 'n', 'r', 'h', 'z']

class RandomGroup( NewsGroup ):

    def __init__( self, name, desc, **kwargs ):
        super().__init__( name, desc, **kwargs )

        start_id = int( time.mktime( time.gmtime() ) )
        self._msgs = []
        for i in range( start_id, start_id + 10 ):
            rand_from = []
            for j in range( 0, random.randint( 2, 6 ) ):
                rand_from.append(
                    RAND_CONSONANTS[random.randint( 0, len( RAND_CONSONANTS ) - 1)] + \
                    RAND_VOWELS[random.randint( 0, len( RAND_VOWELS ) - 1)] )

            self._msgs.append( {'id': i,
                'subject': RandomGroup.generate_sentence(),
                'body': ('\r\n'.join( [RandomGroup.generate_sentence() for x in range( 0, 3 )] )),
                'from': ''.join( rand_from ),
                'date': time.strftime( r'%d %b %Y %H:%M:%S %z', time.localtime() ) } )

    @staticmethod
    def generate_sentence():
        return f'%s %s %s%s' % ( \
            RAND_SUBJECTS[random.randint( 0, len( RAND_SUBJECTS ) - 1 )],
            RAND_VERBS[random.randint( 0, len( RAND_VERBS ) - 1 )],
            RAND_OBJECTS[random.randint( 0, len( RAND_OBJECTS ) - 1 )],
            RAND_TERMS[random.randint( 0, len( RAND_TERMS ) - 1 )])

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
            RandomGroup( 'test', 'Testing group' ),
            RandomGroup( 'random', 'Testing group' )
        ]
    
    def __getitem__( self, key ) -> RandomGroup:
        return {x.name: x for x in self._groups}[key]
    
    def __contains__( self, key ):
        return key in [x.name for x in self._groups]
    
    def __iter__( self ) -> Generator[RandomGroup, None, None]:
        for group in self._groups:
            yield group

SOURCE_CLASS = RandomSource
