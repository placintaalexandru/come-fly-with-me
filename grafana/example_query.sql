select flight_date as time, min(price) as price, toString(scrape_date) as download_date, company
from flight_data.flights
where $__timeFilter(flight_date) and currency = 'EUR' and source = 'NCE' and destination = 'BSL' and scrape_date in ($scrape_dates)
group by flight_date, download_date, company
order by time
