# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
from kafka.producer import KafkaProducer
from pymongo import MongoClient
from scrapy.exporters import CsvItemExporter


class VarysPipeline(object):
    def __init__(self):
        self.file = open("items.csv", 'wb')
        self.exporter = CsvItemExporter(self.file, unicode)
        self.exporter.start_exporting()
        #self.producer = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        self.mongo_client = MongoClient('localhost', 27017)
        self.db = self.mongo_client['varysDb']
        self.collection = self.db['varys']

    def close_spider(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        product = {'title': item['title']}


        if item['price'] in item:
            product['price'] = item['price']
        if item['facet_label'] is not None:
            facet = {item['facet_label']: item['facet_value']}
            self.collection.update_one({'_id': item['title']}, {"$set": product, "$addToSet": facet}, upsert=True)
        else:
            self.collection.update_one({'_id': item['title']}, {"$set": product}, upsert=True)
        #self.producer.send('varys', item['title'])
        return item
