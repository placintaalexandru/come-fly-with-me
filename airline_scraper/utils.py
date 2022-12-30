import json
import os
from json import JSONDecodeError
from logging import Logger
from typing import Union, List, Tuple

from scrapy.utils.project import get_project_settings


def load_pairs_to_scrape(logger: Logger) -> List[Tuple]:
    settings = get_project_settings()

    try:
        pairs = json.loads(os.environ[settings['ENVIRONMENT_SOURCE_PAIRS']])

        if not isinstance(pairs, list):
            raise TypeError('Items to scrape must be list of form (station1,station2)')
    except (KeyError, JSONDecodeError, TypeError) as e:
        logger.error(repr(e))
        pairs = []

    if not pairs:
        logger.error('No pair of stations could be parsed')

    return pairs
