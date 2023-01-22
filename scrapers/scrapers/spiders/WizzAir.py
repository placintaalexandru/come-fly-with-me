import logging
from typing import List

from scrapy import Spider, Request
from datetime import date, timedelta
from copy import deepcopy

from scrapy.utils.project import get_project_settings
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
from scrapy.http import JsonRequest, TextResponse

from .. utils import load_pairs_to_scrape


class WizzairSpider(Spider):
    name = 'WizzAir'
    allowed_domains = ['wizzair.com']
    start_url = 'https://wizzair.com'

    # 42 is supported by Wizz Air -> 30 just to be safe
    WINDOW_SIZE = timedelta(days=30)

    PRICE_TYPES = [{'priceType': 'regular'}]

    def __init__(self, *_args, **kwargs):
        super().__init__(self.name, **kwargs)
        settings = get_project_settings()
        logging.basicConfig(format=settings['LOG_FORMAT'], level=settings['LOG_LEVEL'])

        self.pairs = load_pairs_to_scrape(self.logger)
        self.PERIOD_MONTHS = settings['PERIOD_MONTHS']

        self.logger.info(f'Spider {self.name} will scrape ahead {self.PERIOD_MONTHS} starting from {date.today()}.')
        self.logger.info(f'Spider {self.name} will scrape {self.pairs}.')

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

    def _prepare_request(self, source: str, destination: str, left_date: date, right_date: date) -> List[Request]:
        def apply_extras(base_template: dict, extras: dict) -> dict:
            base_template.update(extras)
            return base_template

        base_request = {
            "flightList": [
                {
                    "departureStation": source,
                    "arrivalStation": destination,
                    "from": left_date.strftime("%Y-%m-%d"),
                    "to": right_date.strftime("%Y-%m-%d")
                }
            ],
            "priceType": "",
            "adultCount": 1,
            "childCount": 0,
            "infantCount": 0
        }

        return list(
            map(lambda extra: JsonRequest(
                    url='https://be.wizzair.com/14.6.0/Api/search/timetable',
                    method='POST',
                    callback=self.parse,
                    errback=self.error_callback,
                    data=apply_extras(deepcopy(base_request), extra),
                ),
                WizzairSpider.PRICE_TYPES)
        )

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

    def parse(self, response: TextResponse, **kwargs):
        flights = response.json()
        scrape_date = date.today().isoformat()

        self.logger.info(f'Received {len(flights)} flights from {response.url}')

        try:
            for flight in flights['outboundFlights']:
                yield {
                    'flight_date': flight['departureDates'][0],
                    'source': flight['departureStation'],
                    'destination': flight['arrivalStation'],
                    'price': flight['price']['amount'],
                    'currency': flight['price']['currencyCode'],
                    'company': self.name,
                    'scrape_date': scrape_date
                }
        except KeyError as e:
            self.logger.error(repr(e))
