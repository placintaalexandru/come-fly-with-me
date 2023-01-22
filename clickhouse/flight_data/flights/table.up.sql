CREATE TABLE IF NOT EXISTS flight_data.flights
(
    flight_date DateTime,
    source String,
    destination String,
    price Float32,
    currency String,
    company String,
    scrape_date Date,
    PRIMARY KEY(flight_date, company)
)
ENGINE = MergeTree;
