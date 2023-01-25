# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from dataclasses import dataclass


# @dataclasses
# class ScrapyFrameworkItem(scrapy.Item):
#     # define the fields for your item here like:
#     name : str

class ScrapyFrameworkItem(scrapy.Item):
    # define the fields for your item here like:
    name = scrapy.Field()
