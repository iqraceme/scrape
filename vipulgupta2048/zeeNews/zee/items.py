# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class ZeeItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    summary = scrapy.Field()
    image = scrapy.Field()
    datetime = scrapy.Field()
    headline = scrapy.Field()
    link = scrapy.Field()
    
