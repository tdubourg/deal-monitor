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
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../../../")))
print 
from utils.shell_utils import execute_shell_and_get_stdout as execsh
from utils.ocr import ocr as ocr


mutex = Lock()
mutex.acquire()

INTERVAL_BETWEEN_ITEM_PAGE_CRAWL_IN_SECONDS = 0.01

locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

price_regexp = re.compile(".*?(([0-9]+( [0-9]+)?)+)", re.MULTILINE | re.DOTALL)
date_regexp = re.compile(" le ([0-9]{1,2} [^ ]+) [^ ]+ ([0-9]{1,2}:[0-9]{1,2})")
extract_number_of_pages_regexp = re.compile(".*?o=([0-9]+)&")
lbc_url_extract_id_regexp = re.compile("\\/([0-9]+)\\.htm")

DBG = True

if DBG:
    n = 0

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

LBC_START_URL_FORMAT = "http://www.leboncoin.fr/%soffres/%s?q=%s"
def lbc_start_url(keywords, region, category):
    if region is not None:
        region = region + "/"
    if category is not None:
        category = category + "/"

    keywords = keywords.replace(" ", "+") #TODO: Actual urlencoding
    return LBC_START_URL_FORMAT % (category, region, keywords)

class LBCSpider(CrawlSpider):
    total_of_items_url = 0
    name = "lbc"
    allowed_domains = ["leboncoin.fr"]
    __start_url = "http://www.leboncoin.fr/consoles_jeux_video/offres/rhone_alpes/?q=gamecube"
    # additional_urls_to_crawl = [__start_url]
    # start_urls = [__start_url]
    start_url = None

    def __init__(self, keywords, category, region):
        self.keywords = keywords
        self.category = category
        self.region = region
        self.start_url = lbc_start_url(keywords, region, category)
        self._rules = [
            Rule(
                SgmlLinkExtractor(
                    allow='http:\/\/.*\/.*\.htm'
                    , restrict_xpaths='//div[@class="list-lbc"]'
                )
                , callback=self.parse_item_page
            )
            , Rule(SgmlLinkExtractor(
                allow=sitemlist_url(self.start_url)
                , restrict_xpaths='//nav/ul[@id="paging"]/li[position() = last()]')
                , callback=self.last_itemlist_page
                )
        ]
        self.start_urls = [self.start_url]

    def parse_item_page(self, response):
        if DBG:
            print "\n\n-----\n\nnamesURL=", response.url
            # raw_input()

        # Wait for some time in order not to be banned / detected as a violent crawler by the website
        time.sleep(INTERVAL_BETWEEN_ITEM_PAGE_CRAWL_IN_SECONDS)

        hxs = HtmlXPathSelector(response)
        item = DealmonitorItem()
        item['id'] = self.extract_id_from_url(response.url)
        item['title'] = hxs.select('//h2[@id="ad_subject"]/text()').extract()[0].encode('utf-8')
        item['url'] = response.url
        item['price'] = self.extract_price(hxs)
        item['desc'] = BeautifulSoup(hxs.select('//div[@class="AdviewContent"]/div[@class="content"]/text()').extract()[0].encode('utf-8')).string
        item['date'] = self.extract_date(hxs)

        phone_num_img_url = hxs.select('//img[@class="AdPhonenum"]/@src').extract()

        if phone_num_img_url is not None and len(phone_num_img_url) > 0:
            tmpfile = item['id'] + '.gif'
            execsh('wget', [phone_num_img_url[0], "-O", tmpfile])
            item["phone"] = ocr(tmpfile)
            os.remove(tmpfile)


        if DBG:
            global n
            n += 1
            print "This was the ", n, "-th item page to be scrapped"
        return item

    def last_itemlist_page(self, response):
        if DBG:
            print "\n --- LAST ITEMLIST PAGE --- :", response.url
        m = extract_number_of_pages_regexp.match(response.url)
        if m is None:
            return None
        
        self.max_page = int(m.groups()[0])
        result = []
        for x in xrange(2, self.max_page):
            page_url = self.__start_url.replace("?q=", "?o=" + str(x) + "&q=")
            result.append(Request(page_url, callback=self.parse_itemlist_page))

        # WHile we are at it, scrap this page's items:
        result.extend(self.parse_itemlist_page(response))

        if DBG:
            print "Returning", result
            # raw_input()
        return result

    def parse_itemlist_page(self, response):
        if DBG:
            print "\n\n--- PARSING ITEMLIST PAGE", response.url, "---\n\n"
        hxs = HtmlXPathSelector(response)
        sites = hxs.select('//div[@class="list-lbc"]/a')
        # sites = hxs.select('//div[@id="ContainerMain"]/div[@class="list-lbc"]')
        items_urls = []
        for site in sites:
            url = site.select('@href').extract()[0]
            items_urls.append(Request(url, callback=self.parse_item_page))

        if DBG:
            self.total_of_items_url += len(items_urls)
            print "## Total number of items urls generated is now", self.total_of_items_url
        return items_urls


    def extract_price(self, hxs):
            price_l = hxs.select('//span[@class="price"]/text()').extract()
            raw_price = price_l[0] if len(price_l) > 0 else ""
            m = price_regexp.match(raw_price)
            try:
                price = int(m.group(1).replace(" ", "")) if m is not None else -1
            except ValueError:
                price = -1

            return price

    def extract_id_from_url(self, url):
        m = lbc_url_extract_id_regexp.search(url)
        if m is None:
            return -1
        return m.groups()[0]

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


