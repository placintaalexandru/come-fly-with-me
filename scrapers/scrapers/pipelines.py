# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import json
import logging
import os

# useful for handling different item types with a single interface
from kafka import KafkaProducer


class AirlineScraperPipeline:

    __slots__ = (
        "producer",
        "topic",
        "logger"
    )

    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=os.environ['KAFKA_BOOTSTRAP_BROKERS'].split(','),
            security_protocol='PLAINTEXT',
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )
        self.topic = os.environ['KAFKA_TOPIC']
        self.logger = logging.getLogger(self.__class__.__name__)

        if self.producer.bootstrap_connected() is False:
            self.logger.error(f'Kafka producer could not connect to {os.environ["KAFKA_BOOTSTRAP_BROKERS"]}')
            raise ConnectionError(f'Kafka producer could not connect to {os.environ["KAFKA_BOOTSTRAP_BROKERS"]}')

        self.logger.info(f'Kafka producer connected to {os.environ["KAFKA_BOOTSTRAP_BROKERS"]}')

    def process_item(self, item, _spider):
        self.logger.info(f'Sending {item} to kafka')
        self.producer.send(self.topic, item)
