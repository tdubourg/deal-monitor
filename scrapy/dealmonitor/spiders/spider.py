from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from dealmonitor.items import *
from BeautifulSoup import BeautifulSoup
import re 

price_regexp = re.compile(".*?(([0-9]+( [0-9]+)?)+)", re.MULTILINE | re.DOTALL)

DBG = True

class LBCSpider(BaseSpider):
    name = "lbc"
    allowed_domains = ["leboncoin.fr"]
    start_urls = [
      "http://www.leboncoin.fr/annonces/offres/rhone_alpes/occasions/?f=a&th=1&q=brosse+a+dent&location=Paris%2075001",
      "http://www.leboncoin.fr/informatique/offres/rhone_alpes/?f=a&th=1&q=g500"
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
            item['title'] = site.select('@title').extract()[0].encode('utf-8')
            item['desc'] = "Placeholder" #site.select('text()').extract()
            date1 = BeautifulSoup(site.select('.//div[@class="date"]/div[position() = 1]/text()').extract()[0].encode('utf-8')).string
            date2 = BeautifulSoup(site.select('.//div[@class="date"]/div[position() = 2]/text()').extract()[0].encode('utf-8')).string
            item['date'] = date1 + " " + date2
            price_l = site.select('.//div[@class="price"]/text()').extract()
            raw_price = price_l[0] if len(price_l) > 0 else ""
            # print "raw_price=", raw_price
            m = price_regexp.match(raw_price)
            # print "Match=", m.groups()
            try:
                item['price'] = int(m.group(1).replace(" ", "")) if m is not None else -1
            except ValueError:
                item['price'] = -1
            items.append(item)
        return items