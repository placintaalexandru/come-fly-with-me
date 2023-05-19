import scrapy
import datetime
from . import base_spider
from .. import airline_route

from scrapy import http
from urllib import parse
from pathlib import PurePosixPath

from typing import List, Tuple

class RyanairSpider(base_spider.BaseSpider):
    name = 'RyanAir'
    allowed_domains = ['ryanair.com']

    WINDOW_SIZE = datetime.timedelta(days=30)

    API_ENDPOINT_TEMPLATE = 'https://www.ryanair.com/api/farfnd/3/oneWayFares/{}/{}/cheapestPerDay'

    def __init__(self, *_args, **kwargs):
        super().__init__(self.name, self.__class__.WINDOW_SIZE, **kwargs)

    def prepare_request(
            self, 
            route: airline_route.Route, 
            left_date: datetime.date, 
            right_date: datetime.date
        ) -> List[scrapy.Request]:
        return [scrapy.FormRequest(
            url=self.__class__.API_ENDPOINT_TEMPLATE.format(route.source, route.destination),
            method='GET',
            callback=self.parse,
            errback=self.error_callback,
            formdata={
                'outboundDateFrom': f'{left_date}',
                'outboundDateTo': f'{right_date}'
            },
        )]

    def parse(self, response: http.TextResponse, **_kwargs):
        def source_destination(url: str) -> Tuple[str, str]:
            url_components = parse.urlparse(url)
            path_components = PurePosixPath(url_components.path)
            return path_components.parts[5], path_components.parts[6]

        flights = response.json()
        source, destination = source_destination(response.request.url)
        scrape_date = datetime.date.today().isoformat()

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
        except KeyError as ke:
            self.logger.error(repr(ke))
