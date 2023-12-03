import scrapy
from datetime import datetime

class TestSpider(scrapy.Spider):
    name = "TestSpider"
    start_urls = ['https://webscraper.io/test-sites']
    client_identifier = 'test'

    def parse(self, response):
        # Extracting product details using XPath
        products = response.xpath('//div[@class="row test-site"]')
        print('$*$', products)
        for product in products:
            print("PRODUCT:", product)
            title = product.xpath('.//h2/a/text()').get().strip()
            text = product.xpath('.//p/text()').get().strip()
            image = product.xpath('.//img/@src').get().strip()
            print('WHO:', title, image, text)
            yield {
                'Title': title,
                'Text': text,
                'Image': image,
            }

# from scrapy.cmdline import execute
# execute('scrapy crawl TestSpider'.split())