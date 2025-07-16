"""
Data Collection Module for Scout AI AFL Platform
"""

from .squiggle_scraper import SquiggleAPI
from .footywire_scraper import FootyWireScraper
from .data_processor import AFLDataProcessor

__all__ = ['SquiggleAPI', 'FootyWireScraper', 'AFLDataProcessor']