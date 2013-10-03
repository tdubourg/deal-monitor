from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from dealmonitor.items import *

DBG = True

class LBCSpider(BaseSpider):
    name = "lbc"
    allowed_domains = ["leboncoin.fr"]
    start_urls = [
      "http://www.leboncoin.fr/annonces/offres/rhone_alpes/occasions/?f=a&th=1&q=brosse+a+dent&location=Paris%2075001"
    ]

    def parse(self, response):
        if DBG:
            print "Execution with response=", response
        hxs = HtmlXPathSelector(response)
        sites = hxs.select('//div[@class="list-lbc"]/a')
        # sites = hxs.select('//div[@id="ContainerMain"]/div[@class="list-lbc"]')
        items = []
        if DBG:
            print "Entering foreach for:", sites
        for site in sites:
            print "\n\n\nSite!", site
            item = DealmonitorItem()
            item['url'] = site.select('@href').extract()
            item['title'] = site.select('@title').extract()
            item['desc'] = "Placeholder" #site.select('text()').extract()
            item['date'] = site.select('//div[@class="date"]/div[position() = 1]/text()').extract()[0] + " " + site.select('//div[@class="date"]/div[position() = 2]/text()').extract()[0]
            item['price'] = site.select('//div[@class="price"]/text()').extract()
            items.append(item)
        return items