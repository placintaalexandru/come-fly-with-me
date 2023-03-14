import logging

from datetime import datetime, timedelta, date
from typing import List, Optional, Tuple

import scrapy
from scrapy import Request
from scrapy.http import TextResponse, JsonRequest
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.project import get_project_settings
from twisted.internet.error import DNSLookupError, TCPTimedOutError

from ..utils import load_pairs_to_scrape


class EasyJetSpider(scrapy.Spider):
    name = 'EasyJet'
    allowed_domains = ['easyjet.com/']
    start_url = 'http://easyjet.com/'

    WINDOW_SIZE = timedelta(days=30)

    # EasyJet structures the offers in these 3 categories
    OFFER_TYPES = [
        'RECOMMENDED',
        'QUICKEST',
        'CHEAPEST'
    ]

    API_ENDPOINT = 'https://gateway.prod.dohop.net/api/graphql'

    def __init__(self, *_args, **kwargs):
        super().__init__(self.name, **kwargs)
        settings = get_project_settings()
        logging.basicConfig(format=settings['LOG_FORMAT'], level=settings['LOG_LEVEL'])

        self.pairs = load_pairs_to_scrape(self.logger)
        self.PERIOD_MONTHS = settings['PERIOD_MONTHS']

        self.stations = set([station for pair in self.pairs for station in pair])

        self.logger.info(f'Spider {self.name} will scrape ahead {self.PERIOD_MONTHS} starting from {date.today()}.')
        self.logger.info(f'Spider {self.name} will scrape {self.pairs}.')

    def _prepare_request(self, source: str, destination: str, left_date: date, right_date: date) -> List[Request]:
        requests = []
        step = timedelta(days=1)

        while left_date < right_date:
            requests.append(
                JsonRequest(
                    url=self.__class__.API_ENDPOINT,
                    method='POST',
                    callback=self.parse,
                    errback=self.error_callback,
                    data={
                        "query": "query searchResult($partner: Partner!, $origin: String!, $destination: String!, "
                                 "$passengerAges: [PositiveInt!]!, $metadata: Metadata!, $departureDateString: "
                                 "String!, $returnDateString: String, $sort: Sort, $limit: PositiveInt, "
                                 "$filters: OfferFiltersInput) {  search(    partner: $partner    origin: $origin "
                                 "   destination: $destination    passengerAges: $passengerAges    metadata: "
                                 "$metadata    departureDateString: $departureDateString    returnDateString: "
                                 "$returnDateString    sort: $sort    limit: $limit    filters: $filters  ) {    "
                                 "numberOfPages    offersFilters {      overnightStay      overnightFlight      "
                                 "connectionTime {        min        max      }      landing {        outbound {  "
                                 "        min          max        }        homebound {          min          max  "
                                 "      }      }      takeoff {        outbound {          min          max       "
                                 " }        homebound {          min          max        }      }    }    "
                                 "bestOffers {      RECOMMENDED {        ...Offer      }      QUICKEST {        "
                                 "...Offer      }      CHEAPEST {        ...Offer      }    }    offers {      "
                                 "...Offer    }    currency    residency  }}        fragment Offer on Offer {  id "
                                 " price  pricePerPerson  currency  transferURL  duration  itinerary {    "
                                 "...Itinerary  }}        fragment Itinerary on Itinerary {  outbound {    "
                                 "...Route  }  homebound {    ...Route  }}        fragment Route on Route {  id  "
                                 "origin {    code    name    city    country  }  destination {    code    name   "
                                 " city    country  }  departure  arrival  duration  operatingCarrier {    name   "
                                 " code    flightNumber  }  marketingCarrier {    name    code    flightNumber  } "
                                 " legs {    ...Leg  }}        fragment Leg on Leg {  id  duration  origin {    "
                                 "code    name    city    country  }  destination {    code    name    city    "
                                 "country  }  departure  arrival  carrierType  operatingCarrier {    name    code "
                                 "   flightNumber  }  marketingCarrier {    name    code    flightNumber  }}",
                        "variables": {
                            "partner": "easyjet",
                            "metadata": {
                                "language": "en",
                                "currency": "EUR",
                            },
                            "origin": source,
                            "destination": destination,
                            "departureDateString": f"{left_date}",
                            "returnDateString": None,
                            "passengerAges": [
                                18
                            ],
                            "limit": 1
                        }
                    },
                )
            )

            left_date += step

        return requests

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

    # TODO: Look into why other stations are included
    def parse(self, response: TextResponse, **kwargs):
        def parse_offer(raw_offer: dict) -> Optional[Tuple[str, dict]]:
            outbound = raw_offer['itinerary']['outbound'][0]

            # Filter only direct flights
            if len(outbound['legs']) > 1:
                return None

            return outbound['id'], {
                'flight_date': datetime.fromisoformat(outbound['legs'][0]['departure'][:-1]).isoformat(),
                'source': outbound['legs'][0]['origin']['code'],
                'destination': outbound['legs'][0]['destination']['code'],
                'price': raw_offer['price'],
                'currency': raw_offer['currency'],
                'company': self.__class__.name,
                'scrape_date': scrape_date
            }

        data = response.json()
        scrape_date = date.today().isoformat()
        ids = set()

        try:
            best_offers = data['data']['search']['bestOffers']

            if best_offers is None:
                return

            for offer_type in EasyJetSpider.OFFER_TYPES:
                try:
                    parsed_offer = parse_offer(best_offers[offer_type])

                    match parsed_offer:
                        case None:
                            continue
                        case offer_id, offer:
                            if offer_id in ids:
                                continue

                            if offer['source'] not in self.stations or offer['destination'] not in self.stations:
                                continue

                            ids.add(offer_id)

                            yield offer
                except KeyError as ke:
                    self.logger.error(repr(ke))
        except KeyError as ke:
            self.logger.error(repr(ke))

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
