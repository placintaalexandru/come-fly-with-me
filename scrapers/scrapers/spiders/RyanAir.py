import logging
from urllib.parse import urlparse
from pathlib import PurePosixPath

from datetime import timedelta, date
from typing import List, Tuple

import scrapy
from scrapy import Request
from scrapy.http import TextResponse
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.project import get_project_settings
from twisted.internet.error import DNSLookupError, TCPTimedOutError

from ..utils import load_pairs_to_scrape


class RyanairSpider(scrapy.Spider):
    name = 'RyanAir'
    allowed_domains = ['ryanair.com']
    start_url = 'http://ryanair.com/'

    WINDOW_SIZE = timedelta(days=30)

    def __init__(self, *_args, **kwargs):
        super().__init__(self.name, **kwargs)
        settings = get_project_settings()
        logging.basicConfig(format=settings['LOG_FORMAT'], level=settings['LOG_LEVEL'])

        self.pairs = load_pairs_to_scrape(self.logger)
        self.PERIOD_MONTHS = settings['PERIOD_MONTHS']

        self.logger.info(f'Spider {self.name} will scrape ahead {self.PERIOD_MONTHS} starting from {date.today()}.')
        self.logger.info(f'Spider {self.name} will scrape {self.pairs}.')

    def _prepare_request(self, source: str, destination: str, left_date: date, right_date: date) -> List[Request]:
        return [scrapy.FormRequest(
            url=f'https://www.ryanair.com/api/farfnd/3/oneWayFares/{source}/{destination}/cheapestPerDay',
            method='GET',
            callback=self.parse,
            errback=self.error_callback,
            formdata={
                'outboundDateFrom': f'{left_date}',
                'outboundDateTo': f'{right_date}'
            },
        )]

    def start_requests(self):
        start = date.today()
        end = start + self.PERIOD_MONTHS

        while start < end:
            period_start, period_end = start, start + self.WINDOW_SIZE - timedelta(days=1)

            for station1, station2 in self.pairs:
                if not isinstance(station1, str):
                    logging.error(f'Station {station1} is not string')
                    continue

                if not isinstance(station2, str):
                    logging.error(f'Station {station2} is not string')
                    continue

                if station1 == station2:
                    self.logger.warning(f'Identical pair ({station1},{station2}) found.')
                    continue

                requests = self._prepare_request(station1, station2, period_start, period_end) + \
                           self._prepare_request(station2, station1, period_start, period_end)

                for request in requests:
                    yield request

            start = start + self.WINDOW_SIZE

    @staticmethod
    def _source_destination(url: str) -> Tuple[str, str]:
        url_components = urlparse(url)
        path_components = PurePosixPath(url_components.path)
        return path_components.parts[5], path_components.parts[6]

    def parse(self, response: TextResponse, **kwargs):
        flights = response.json()
        source, destination = RyanairSpider._source_destination(response.request.url)
        scrape_date = date.today().isoformat()

        try:
            # RyanAir gets the whole month and every day might or might not have data
            available_flights = list(
                filter(lambda day_flight: day_flight['unavailable'] is False, flights['outbound']['fares'])
            )
            self.logger.info(f'Received {len(available_flights)} flights from {response.url}')

            for available_flight in available_flights:
                yield {
                    'flight_date': available_flight['departureDate'],
                    'source': source,
                    'destination': destination,
                    'price': available_flight['price']['value'],
                    'currency': available_flight['price']['currencyCode'],
                    'company': self.name,
                    'scrape_date': scrape_date
                }
        except KeyError as e:
            self.logger.error(repr(e))

    def error_callback(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        # in case you want to do something special for some errors,
        # you may need the failure's type:

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
        elif failure.check(DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)
        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s', request.url)
