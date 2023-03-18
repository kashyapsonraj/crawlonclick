import scrapy

class AmazonSpider(scrapy.Spider):
    name = "AmazonSpider"
    start_urls = [
        "https://www.amazon.com/s?k=laptop",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        for product in response.css('.s-result-item'):
            item = {}
            item['name'] = product.css('.s-product-name::text').get().strip()
            item['price'] = product.css('.s-price::text').get().strip()
            yield item