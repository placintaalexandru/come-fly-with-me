import abc
import json
import scrapy
import datetime
import logging

from scrapy import http
from .. import settings, airline_route

from typing import List, Optional
from twisted.python import failure
from scrapy.spidermiddlewares import httperror
from twisted.internet import error

class BaseSpider(scrapy.Spider):
    name: Optional[str] = None
    days_to_scrape: int = 0
    routes: List[airline_route.Route] = []
    allowed_domains: List[str] = []
    window_size: int = 1

    def __init__(self, name, window_size, **kwargs):
        super().__init__(name, **kwargs)
        logging.basicConfig(format=settings.LOG_FORMAT, level=settings.LOG_LEVEL)

        self.routes = self.routes_to_scrape()
        self.days_to_scrape = settings.DAYS_TO_SCRAPE
        self.window_size = window_size
        self.logger.info(f'Spider {self.name} will scrape ahead {self.days_to_scrape} days starting from {datetime.date.today()}.')
        self.logger.info(f'Spider {self.name} will scrape {self.routes}.')

    def start_requests(self):
        start = datetime.date.today()
        end = start + self.days_to_scrape

        while start < end:
            period_start, period_end = start, start + self.window_size - datetime.timedelta(days=1)

            for route in self.routes:
                yield from (
                    self.prepare_request(route, period_start, period_end) +
                    self.prepare_request(route.return_route(), period_start, period_end)
                )

            start = start + self.WINDOW_SIZE

    def routes_to_scrape(self) -> List[airline_route.Route]:
        routes: List[airline_route.Route] = []

        try:
            with open(settings.ROUTES_FILE, 'r') as f:
                json_routes = json.load(f).get(self.name, [])

                for json_route in json_routes:
                    try:
                        route: airline_route.Route = airline_route.Route.from_dict(json_route)

                        if route.source == route.destination:
                            self.logger.warning(f'Identical pair in {route} found.')
                            continue

                        routes.append(route)
                    except KeyError as ke:
                        self.logger.error(f'{json_route} is not a valid {type(airline_route.Route)} object')
                        self.logger.error(ke)
        except FileNotFoundError:
            self.logger.error(f'File {settings.ROUTES_FILE} was not found')

        return routes

    @abc.abstractmethod
    def prepare_request(
        self, route: airline_route.Route,
        arrival_date: datetime.date,
        departure_date: datetime.date
    ) -> List[scrapy.Request]:
        ...

    @abc.abstractclassmethod
    def parse(self, response: http.TextResponse, **_kwargs):
        ...

    def error_callback(self, failure: failure.Failure):
        # log all failures
        self.logger.error(repr(failure.value))

        # in case you want to do something special for some errors,
        # you may need the failure's type:

        if failure.check(httperror.HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
        elif failure.check(error.DNSLookupError):
            # this is the original request
            request = failure.request
            self.logger.error('DNSLookupError on %s', request.url)
        elif failure.check(error.TimeoutError, error.TCPTimedOutError):
            request = failure.request
            self.logger.error('TimeoutError on %s %s', request.url)
