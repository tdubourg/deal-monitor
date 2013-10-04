# -*- coding: utf-8 -*-
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request
from dealmonitor.items import *
from BeautifulSoup import BeautifulSoup
import re 
import time, calendar, datetime
import locale
from threading import Lock

mutex = Lock()
mutex.acquire()

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

price_regexp = re.compile(".*?(([0-9]+( [0-9]+)?)+)", re.MULTILINE | re.DOTALL)
date_regexp = re.compile(" le ([0-9]{1,2} [^ ]+) [^ ]+ ([0-9]{1,2}:[0-9]{1,2})")
extract_number_of_pages_regexp = re.compile(".*?o=([0-9]+)&")

DBG = True

def sitemlist_url(start_url):
    result = start_url.replace("?q=", "\\?o=[0-9]+&q=")
    if DBG:
        print "POUET", result
    return result

# def start_urls_generator(start_url, urls):
#     print "ITEMLIST: init generator called"
#     i = 0
#     l = len(urls)
#     while i < l:
#         print "ITEMLIST: generator called, start of WHILE, i=", i
#         yield urls[i]
#         if i < 10:
#             urls += ["http://pouet"]
#         l = len(urls)
#         i += 1
#         print "ITEMLIST: generator called, end of WHILE, i=", i
#         # mutex.acquire(True)
#         # mutex.release()


class LBCSpider(CrawlSpider):
    name = "lbc"
    allowed_domains = ["leboncoin.fr"]
    __start_url = "http://www.leboncoin.fr/informatique/offres/rhone_alpes/?q=ordinateur"
    # additional_urls_to_crawl = [__start_url]
    start_urls = [__start_url]
    rules = [
        Rule(SgmlLinkExtractor(allow='http:\/\/.*\/.*\.htm', restrict_xpaths='//div[@class="list-lbc"]'), callback='parse_item_page'),
        Rule(SgmlLinkExtractor(
            allow=sitemlist_url(__start_url),
            restrict_xpaths='//nav/ul[@id="paging"]/li[position() = last()]'),
            callback='last_itemlist_page')
    ]

    def parse_item_page(self, response):
        if DBG:
            print "\n\n-----\n\nnamesURL=", response.url

        hxs = HtmlXPathSelector(response)
        item = DealmonitorItem()
        item['title'] = hxs.select('//h2[@id="ad_subject"]').extract()[0].encode('utf-8')
        item['url'] = response.url
        item['price'] = self.extract_price(hxs)
        item['desc'] = BeautifulSoup(hxs.select('//div[@class="AdviewContent"]/div[@class="content"]/text()').extract()[0].encode('utf-8')).string
        item['date'] = self.extract_date(hxs)
        return item

    def last_itemlist_page(self, response):
        if DBG:
            print "\n --- LAST ITEMLIST PAGE --- :", response.url
        m = extract_number_of_pages_regexp.match(response.url)
        if m is None:
            return None
        
        self.max_page = int(m.groups()[0])
        result = []
        for x in xrange(2, self.max_page+1):
            page_url = self.__start_url.replace("?q=", "?o=" + str(x) + "&q=")
            result.append(Request(page_url, callback=self.parse_item_page))
        return result


    def extract_price(self, hxs):
            price_l = hxs.select('//span[@class="price"]/text()').extract()
            raw_price = price_l[0] if len(price_l) > 0 else ""
            m = price_regexp.match(raw_price)
            try:
                price = int(m.group(1).replace(" ", "")) if m is not None else -1
            except ValueError:
                price = -1

            return price

    def extract_date(self, hxs):
        texts = hxs.select('//div[@class="upload_by"]/text()').extract()
        if len(texts) <= 1:
            return ""

        m = date_regexp.match(texts[1])
        if m is None:
            return ""

        if DBG:
            print m.groups()
            print m.groups()[0].encode("UTF-8")

        date = m.groups()[0].encode("UTF-8") + " " + m.groups()[1].encode("UTF-8") if len(m.groups()) > 1 else ""

        dtime = time.strptime(date + " " + str(datetime.datetime.today().year).encode('UTF-8'), "%d %B %H:%M %Y")

        timestamp = calendar.timegm(dtime)

        if DBG:
            print "Datetime generated:", dtime

        return timestamp


