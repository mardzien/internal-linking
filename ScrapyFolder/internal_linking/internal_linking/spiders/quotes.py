import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader


from ..items import InternalLinkingItem


class QuotesSpider(CrawlSpider):
    name = 'quotes'
    allowed_domains = ['medifem.pl']
    start_urls = [
        'http://medifem.pl',
                  ]

    rules = (
        Rule(LinkExtractor(allow_domains=allowed_domains, allow=r'.*'), callback='parse', follow=True),
    )

    def parse(self, response):
        items = InternalLinkingItem()

        items['URL'] = response.url
        items['H1'] = response.xpath('//h1/text()').extract()
        items['Title'] = response.xpath('//title/text()').extract()
        items['Text'] = response.xpath('//p/text()').extract()

        yield items
