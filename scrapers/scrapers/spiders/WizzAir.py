import json

import scrapy
import datetime


from typing import List, Dict
from scrapy import http
from copy import deepcopy
from . import base_spider
from .. import airline_route


class WizzairSpider(base_spider.BaseSpider):
    name = 'WizzAir'
    allowed_domains = ['wizzair.com']

    # 42 is supported by Wizz Air -> 30 just to be safe
    WINDOW_SIZE = datetime.timedelta(days=30)

    PRICE_TYPES = [{'priceType': 'regular'}]

    API_ENDPOINT = 'https://be.wizzair.com/17.4.0/Api/search/timetable'

    def __init__(self, *_args, **kwargs):
        super().__init__(self.name, self.__class__.WINDOW_SIZE, **kwargs)
        self.cookies = {}

    def _headers(self) -> Dict[str, str]:
        headers = {
            # From my experiments, this can also be empty
            'Referer': 'https://wizzair.com/en-gb/flights/timetable',
            'Content-Type': 'application/json',
        }

        if 'RequestVerificationToken' in self.cookies:
            headers['X-Requestverificationtoken'] = self.cookies['RequestVerificationToken']

        return headers

    def _update_cookies(self, response: http.TextResponse):
        for header_name, header_value in response.headers.items():
            # If WizzAir server doesn't want a cookie to be set, then don't set it
            if header_name.decode('utf-8') != 'Set-Cookie':
                continue

            for cookie_to_be_set in header_value:
                cookie_parts = cookie_to_be_set.decode('utf-8').split(';')

                for cookie_part in cookie_parts:
                    # Take only first `=` into account
                    name_and_value = cookie_part.strip().split('=', 1)

                    # Skip everything that does not have the form `key=value`
                    if len(name_and_value) != 2:
                        continue

                    name, value = name_and_value

                    # Minimal set of cookies so the thing works
                    # if name != 'ASP.NET_SessionId' and name != 'RequestVerificationToken':
                    #     continue

                    self.cookies[name] = value

    def prepare_request(
            self,
            route: airline_route.Route,
            left_date: datetime.date,
            right_date: datetime.date
    ) -> List[scrapy.Request]:
        def apply_extras(base_template: dict, extras: dict) -> dict:
            base_template.update(extras)
            return base_template

        base_request = {
            "flightList": [
                {
                    "departureStation": route.source,
                    "arrivalStation": route.destination,
                    "from": left_date.strftime("%Y-%m-%d"),
                    "to": right_date.strftime("%Y-%m-%d")
                }
            ],
            "priceType": "",
            "adultCount": 1,
            "childCount": 0,
            "infantCount": 0
        }

        result = []

        for price_type in WizzairSpider.PRICE_TYPES:
            result.append(
                scrapy.Request(
                    url=self.__class__.API_ENDPOINT,
                    method='POST',
                    callback=self.parse,
                    errback=self.error_callback,
                    headers=self._headers(),
                    cookies=self.cookies,
                    body=json.dumps(apply_extras(deepcopy(base_request), price_type))
                )
            )

        return result

    def parse(self, response: http.TextResponse, **_kwargs):
        flights = response.json()
        scrape_date = datetime.date.today().isoformat()

        self.logger.info(f'Received {len(flights)} flights from {response.url}')
        self._update_cookies(response)

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
        except KeyError as ke:
            self.logger.error(repr(ke))
