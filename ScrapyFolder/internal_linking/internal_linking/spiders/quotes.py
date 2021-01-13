import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.crawler import CrawlerProcess
from scrapy.loader import ItemLoader


from ...internal_linking.items import InternalLinkingItem


class QuotesSpider(CrawlSpider):
    name = 'quotes'

    def __init__(self, domain_name: str, input_class: str, *args, **kwargs):
        super(QuotesSpider, self).__init__(*args, **kwargs)
        self.domain_name = domain_name
        self.input_class = input_class

        self.allowed_domains = [domain_name]
        self.start_urls = [domain_name, ]

        self.rules = (
            Rule(LinkExtractor(allow_domains=self.allowed_domains, allow=r'.*'), callback='parse', follow=True),
        )

    def parse(self, response, *args, **kwargs):

        items = InternalLinkingItem()
        items['URL'] = response.url
        items['H1'] = response.xpath('//h1/text()').getall()
        items['Title'] = response.xpath('//title/text()').getall()
        main_selector = response.xpath(f'//[@class="{self.input_class}"]')
        items['Text'] = response.xpath('//p/text()').getall()

        yield items


process = CrawlerProcess(settings={
    "FEEDS": {
        "items.json": {"format": "json"},
    },
})

process.crawl(QuotesSpider)
process.start()  # the script will block here until the crawling is finished
