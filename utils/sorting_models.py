from typing import List, Callable
from core.entities.note import Note
from core.entities.value_objects.timestamp import Timestamp
from datetime import datetime

class NoteSorter:
    """Utility class for sorting notes with various strategies"""
    
    @staticmethod
    def sort_by_created_date(notes: List[Note], reverse: bool = False) -> List[Note]:
        return sorted(
            notes,
            key=lambda note: note.created_date.value,
            reverse=reverse
        )
    
    @staticmethod
    def sort_by_modified_date(notes: List[Note], reverse: bool = True) -> List[Note]:
        return sorted(
            notes,
            key=lambda note: note.modified_date.value,
            reverse=reverse
        )
    
    @staticmethod
    def sort_by_title(notes: List[Note], reverse: bool = False) -> List[Note]:
        return sorted(
            notes,
            key=lambda note: note.title.lower(),
            reverse=reverse
        )
    
    @staticmethod
    def sort_by_pinned(notes: List[Note], reverse: bool = True) -> List[Note]:
        return sorted(
            notes,
            key=lambda note: note.is_pinned,
            reverse=reverse
        )
    
    @staticmethod
    def get_sorter(sort_by: str) -> Callable[[List[Note]], List[Note]]:
        """Factory method to get appropriate sorting strategy"""
        sorters = {
            'created_date': NoteSorter.sort_by_created_date,
            'modified_date': NoteSorter.sort_by_modified_date,
            'title': NoteSorter.sort_by_title,
            'pinned': NoteSorter.sort_by_pinned
        }
        
        if sort_by not in sorters:
            raise ValueError(f"Invalid sort_by option: {sort_by}")
            
        return sorters[sort_by]