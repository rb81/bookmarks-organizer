from abc import ABC, abstractmethod
from typing import List, Dict

class LLMInterface(ABC):
    """
    Abstract base class defining the interface for Language Model implementations.
    
    This interface ensures that all concrete LLM classes implement the required
    methods for bookmark categorization.
    """

    @abstractmethod
    def categorize_bookmarks(self, bookmarks: List[Dict], existing_categories: List[str], max_categories: int) -> List[str]:
        """
        Categorize a list of bookmarks using the LLM.

        :param bookmarks: List of bookmark dictionaries
        :param existing_categories: List of existing category names
        :param max_categories: Maximum number of categories allowed
        :return: List of category names for the input bookmarks
        """
        pass