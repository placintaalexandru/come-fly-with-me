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
        self.topic = os.environ['KAFKA_TOPIC']
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_item(self, item, _spider):
        self.producer.send(self.topic, item)

    def open_spider(self, spider):
        self.producer = KafkaProducer(
            bootstrap_servers=os.environ['KAFKA_BOOTSTRAP_BROKERS'].split(','),
            security_protocol='PLAINTEXT',
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        )

        if self.producer.bootstrap_connected() is False:
            raise ConnectionError(
                f'Kafka producer could not connect to {os.environ["KAFKA_BOOTSTRAP_BROKERS"]} for spider {spider.name}'
            )

        self.logger.info(
            f'Kafka producer connected to {os.environ["KAFKA_BOOTSTRAP_BROKERS"]} for spider {spider.name}'
        )

    def close_spider(self, _spider):
        self.producer.close()
