from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector

class LBCSpider(BaseSpider):
    name = "lbc"
    allowed_domains = ["leboncoin.fr"]
    start_urls = [
        "http://www.leboncoin.fr/annonces/offres/rhone_alpes/occasions/?f=a&th=1&q=brosse+a+dent&location=Paris%2075001"
    ]

    def parse(self, response):
       hxs = HtmlXPathSelector(response)
       sites = hxs.select('//div[@id="ContainerMain"]/div[@class="list-lbc"]')
       items = []
       for site in sites:
           item = DealmonitorItem()
           item['url'] = site.select('a/@href').extract()
           item['title'] = site.select('a/@title').extract()
           item['desc'] = "Placeholder" #site.select('text()').extract()
           item['price'] = site.select('a/div[@class="price"]').extract()
           item['date'] = site.select('a/div[@class="date"]').extract()
           items.append(item)
       return items