import scrapy
from datetime import datetime

class StockSpider(scrapy.Spider):
    name = "StockSpider"
    start_urls = ['http://www.google.com']
    client_identifier = "nifty"

    def parse(self, response):
        yield {
            "client_identifier": self.client_identifier,
            "Symbol": 'JHJM',
            "timestamp": datetime.now()
        }

