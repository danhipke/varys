# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item, Field


class SearchResultsItem(Item):
    title = Field()
    price = Field()
    url = Field()
    facet_label = Field()
    facet_value = Field()


class ProductInfoItem(Item):
    title = Field()
    image = Field()
