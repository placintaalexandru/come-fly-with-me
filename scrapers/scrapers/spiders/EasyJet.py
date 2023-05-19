import datetime
from typing import List, Optional, Tuple, Set

import scrapy
from scrapy import http
from .. import airline_route
from . import base_spider


class EasyJetSpider(base_spider.BaseSpider):
    name = 'EasyJet'
    allowed_domains = ['easyjet.com/']
    start_url = 'http://easyjet.com/'

    WINDOW_SIZE = datetime.timedelta(days=30)

    # EasyJet structures the offers in these 3 categories
    OFFER_TYPES = [
        'RECOMMENDED',
        'QUICKEST',
        'CHEAPEST'
    ]

    API_ENDPOINT = 'https://gateway.prod.dohop.net/api/graphql'

    custom_settings = {
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 10,
        'AUTOTHROTTLE_ENABLED': False
    }

    def __init__(self, *_args, **kwargs):
        super().__init__(self.name, self.__class__.WINDOW_SIZE, **kwargs)
        self.stations = self.stations_set()

    def stations_set(self) -> Set[str]:
        stations: Set[str] = set()

        for route in self.routes:
            stations.add(route.source)
            stations.add(route.destination)

        return stations

    def prepare_request(
            self, 
            route: airline_route.Route, 
            left_date: datetime.date, 
            right_date: datetime.date
        ) -> List[scrapy.Request]:
        requests: List[scrapy.Request] = []
        step = datetime.timedelta(days=1)

        while left_date < right_date:
            requests.append(
                http.JsonRequest(
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
                            "origin": route.source,
                            "destination": route.destination,
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

    # TODO: Look into why other stations are included
    def parse(self, response: http.TextResponse, **kwargs):
        def parse_offer(raw_offer: dict) -> Optional[Tuple[str, dict]]:
            outbound = raw_offer['itinerary']['outbound'][0]

            # Filter only direct flights
            if len(outbound['legs']) > 1:
                return None

            return outbound['id'], {
                'flight_date': datetime.datetime.fromisoformat(outbound['legs'][0]['departure'][:-1]).isoformat(),
                'source': outbound['legs'][0]['origin']['code'],
                'destination': outbound['legs'][0]['destination']['code'],
                'price': raw_offer['price'],
                'currency': raw_offer['currency'],
                'company': self.__class__.name,
                'scrape_date': scrape_date
            }

        data = response.json()
        scrape_date = datetime.date.today().isoformat()
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
