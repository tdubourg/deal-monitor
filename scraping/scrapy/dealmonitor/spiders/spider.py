# -*- coding: utf-8 -*-
from scrapy.spider import BaseSpider
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

INTERVAL_BETWEEN_ITEM_PAGE_CRAWL_IN_SECONDS = 0.01
RUN_TYPE_FULL = "full"
RUN_TYPE_PARTIAL = "partial"

# Note: This is in order to have dates parsed correctly, adapte to your own locale...
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

price_regexp = re.compile(".*?(([0-9]+( [0-9]+)?)+)", re.MULTILINE | re.DOTALL)
# This regexp stands for "le [day_of_month] [month] [*] [hour:minutes]"
date_regexp = re.compile(" le ([0-9]{1,2} [^ ]+) [^ ]+ ([0-9]{1,2}:[0-9]{1,2})")
date_time_regexp = re.compile("([0-9]{1,2}:[0-9]{1,2})")
extract_number_of_pages_regexp = re.compile(".*?o=([0-9]+)&")
lbc_url_extract_id_regexp = re.compile("\\/([0-9]+)\\.htm")

DBG = True

if DBG:
    n = 0

def itemlist_url(start_url):
    result = start_url.replace("?q=", "\\?o=[0-9]+&q=")
    if DBG:
        print "POUET", result
    return result

LBC_START_URL_FORMAT = "http://www.leboncoin.fr/%soffres/%s?q=%s"
def lbc_start_url(keywords, region, category):
    if region is not None:
        region = region + "/"
    if category is not None:
        category = category + "/"

    keywords = keywords.replace(" ", "+") #TODO: Actual urlencoding
    return LBC_START_URL_FORMAT % (category, region, keywords)

class LBCSpider(BaseSpider):
    total_of_items_url = 0
    name = "lbc"
    allowed_domains = ["leboncoin.fr"]
    start_url = None
    start_urls = []

    def __init__(self, keywords, category, region, run, export_path, upto=None):
        self.category = category
        self.region = region
        self.run_type = run
        self.export_results_filename = export_path

        if self.run_type != RUN_TYPE_FULL and self.run_type != RUN_TYPE_PARTIAL:
            print "Error, a run can only take the following values: ", RUN_TYPE_PARTIAL, ",", RUN_TYPE_FULL
            exit(1)
        if self.run_type == RUN_TYPE_PARTIAL:
            if upto is None:
                print "Error, upto parameter must be provided when run is partial"
                exit(1)
            self.is_partial = True
            self.partial_stopped = False
            self.upto = int(upto)
        else:
            self.is_partial = False
        self.start_url = lbc_start_url(keywords, region, category)
        # self._rules = [
        #     Rule(
        #         SgmlLinkExtractor(
        #             allow='http:\/\/.*\/.*\.htm'
        #             , restrict_xpaths='//div[@class="list-lbc"]'
        #         )
        #         , callback=self.parse_item_page
        #     )
        #     , Rule(SgmlLinkExtractor(
        #         allow=itemlist_url(self.start_url)
        #         , restrict_xpaths='//nav/ul[@id="paging"]/li[position() = last()]')
        #         , callback=self.last_itemlist_page
        #         )
        # ]
        self.start_urls = [self.start_url]

    def parse(self, response):
        for r in self.first_itemlist_page(response):
            yield r


    def first_itemlist_page(self, response):
        if DBG:
            print "\n --- FIRST ITEMLIST PAGE --- :", response.url
        
        # Parse 1st page's items
        for r in self.parse_itemlist_page(response):
            yield r

        # Find the total number of pages...
        m = extract_number_of_pages_regexp.match(response.url)
        
        # No other page? Stop here
        if m is None:
            return 

        self.max_page = int(m.groups()[0])
        for x in xrange(2, self.max_page + 1):
            if self.is_partial and self.partial_stopped:
                break
            page_url = self.start_url.replace("?q=", "?o=" + str(x) + "&q=")
            yield Request(page_url, callback=self.parse_itemlist_page)


    def parse_itemlist_page(self, response):
        if self.is_partial and self.partial_stopped:
            return

        if DBG:
            print "\n\n--- PARSING ITEMLIST PAGE", response.url, "---\n\n"
        
        hxs = HtmlXPathSelector(response)
        item_page_urls = hxs.select('//div[@class="list-lbc"]/a')
        if DBG:
            print "Found", len(item_page_urls), "items on this page"

        for item in item_page_urls:
            url = item.select('@href').extract()[0]
        
            if self.is_partial:
                if DBG:
                    print "Partial run case, special things happening"
                # If the run is partial, perform some checks about the datetime this item was updated
                # in order to know when to stop the partial run
                date_date = BeautifulSoup(item.select('.//div[@class="date"]/div[position() = 1]/text()').extract()[0]).string.strip().encode('utf-8')
                date_time = BeautifulSoup(item.select('.//div[@class="date"]/div[position() = 2]/text()').extract()[0]).string.strip().encode('utf-8')
                # Grab the date of the currently being analyzed item
                date = self.extract_date_on_itemlist_page(date_date, date_time)
                if DBG:
                    print "Date of this item is", date
                # If this item is older than the datetime we're supposed to check up to, stop the partial run here.
                if date < self.upto:
                    if DBG:
                        print "The item %s was date=%s and thus older than upto=%s" % (url, str(date), str(self.upto))
                    self.partial_stopped = True
                    return

            self.total_of_items_url += 1
            yield Request(url, callback=self.parse_item_page)
            # Wait for some time in order not to be banned / detected as a violent crawler by the website
            time.sleep(INTERVAL_BETWEEN_ITEM_PAGE_CRAWL_IN_SECONDS)

        
        if DBG:
            print "## Total number of items urls generated is now", self.total_of_items_url

    def parse_item_page(self, response):
        if DBG:
            print "\n\n-----\n\nnamesURL=", response.url
            # raw_input()

        hxs = HtmlXPathSelector(response)
        item = DealmonitorItem()
        item['id'] = self.extract_id_from_url(response.url)
        item['title'] = hxs.select('//h2[@id="ad_subject"]/text()').extract()[0]
        item['url'] = response.url
        item['price'] = self.extract_price(hxs)
        item['desc'] = BeautifulSoup(hxs.select('//div[@class="AdviewContent"]/div[@class="content"]/text()').extract()[0]).string
        item['date'] = self.extract_date_on_item_page(hxs)
        item['phone'] = None
        item['email'] = None
        
        item["has_phone_number"] = True # due to a current bug on the website, we can grab all the phone numbers, so, hard set that to True for now # hxs.select('//span[@id="phoneNumber"]').extract() is not None

        if DBG:
            global n
            n += 1
            print "This was the ", n, "-th item page to be scrapped"
        return item

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

    #TOOD: All this code is very LBC specific, move it to somwhere else?
    @staticmethod
    def extract_date_on_itemlist_page(date_date, date_time):
        today = datetime.datetime.today()
        # This method, is, clear, not optimized (in the case of today & yesterday): we could make the time tuple ourselves
        # instead of creating the string and then parsing it...
        # well, lazyness, your beat me
        if date_date == "Aujourd'hui":
            date_str = "%s %s %s %s" % (
                  str(today.day)
                , time.strftime("%b", today.timetuple())
                , date_time
                , str(today.year)
            )
        elif date_date == "Hier":
            yesterday = today - datetime.timedelta(1)
            date_str = "%s %s %s %s" % (
                  str(yesterday.day)
                , time.strftime("%b", today.timetuple())
                , date_time
                , str(yesterday.year)
            )
        else:
            # TODO: Fix the year's hack that will not work when today's year is not the same as ad's year
            date_str = date_date.title() + ". " + date_time + " " + str(today.year)

        dtime = time.strptime(date_str, "%d %b %H:%M %Y") # WARNING, here, month is abbreviated

        timestamp = calendar.timegm(dtime)

        if DBG:
            print "Datetime generated:", dtime

        return timestamp

    @staticmethod
    def extract_date_on_item_page(hxs):
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

        # TODO: Fix the year's hack that will not work when today's year is not the same as ad's year
        dtime = time.strptime(date + " " + str(datetime.datetime.today().year).encode('UTF-8'), "%d %B %H:%M %Y")

        timestamp = calendar.timegm(dtime)

        if DBG:
            print "Datetime generated:", dtime

        return timestamp


