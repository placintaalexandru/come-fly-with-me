CREATE TABLE IF NOT EXISTS flight_data.kafka_queue
(
    flight_date DateTime,
    source String,
    destination String,
    price Float32,
    currency String,
    company String,
    scrape_date Date,
)
ENGINE = Kafka()
settings
    kafka_broker_list  = 'kafka:9092',
    kafka_topic_list = 'flights',
    kafka_group_name = 'clickhouse',
    kafka_format = 'JSONEachRow',
    kafka_thread_per_consumer = 0,
    kafka_num_consumers = 1;

CREATE MATERIALIZED VIEW IF NOT EXISTS  flight_data.kafka_queue_mv TO flight_data.flights AS
SELECT *
FROM flight_data.kafka_queue;
