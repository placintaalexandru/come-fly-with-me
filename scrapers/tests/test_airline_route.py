
from scrapers.airline_route import Route

def test_return_route():
    route = Route('a', 'b')
    return_route = route.return_route()

    assert(route.source != route.destination)
    assert(return_route.source == route.destination)
    assert(return_route.destination == route.source)

def test_parse_airline_route():
    s = """
        {
            \"source\": \"GVA\",
            \"destination\": \"OTP\"
        }
    """
    route = Route.schema().loads(s)

    assert(route.source == 'GVA')
    assert(route.destination == 'OTP')

