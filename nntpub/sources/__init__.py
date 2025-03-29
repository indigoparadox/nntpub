
from typing import Generator

class NewsGroup( object ):
    def __init__( self, name, desc ):
        self.name = name
        self.desc = desc

    def __getitem__( self, key ) -> dict[str, any]:
        return None
    
    def __contains__( self, key ) -> bool:
        return False

    def __iter__( self ) -> Generator[dict[str, any], None, None]:
        return None
    
    def get_first_msg( self ) -> dict[str, any]:
        return None
    
    def get_last_msg( self ) -> dict[str, any]:
        return None
    
    def count_messages( self ) -> int:
        return 0

class  NewsSource( object ):
    def __init__( self, **kwargs ):
        pass

    def __getitem__( self, key ) -> NewsGroup:
        return None
    
    def __contains__( self, key ) -> bool:
        return False
    
    def __iter__( self ) -> Generator[NewsGroup, None, None]:
        return None
