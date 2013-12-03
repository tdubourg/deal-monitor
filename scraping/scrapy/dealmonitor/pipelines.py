# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import urllib2
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__ + "/../../")))
from utils.shell_utils import execute_shell_and_get_stdout as execsh
from utils.ocr import ocr as ocr
from utils.json_utils import load_json, write_json

class DealmonitorPipeline(object):
    def process_item(self, item, spider):
        if item["title"]:
            item["title"] = item["title"].encode('utf-8')
        if item["desc"]:
            item["desc"] = item["desc"].encode('utf-8')
        if item["email"]:
            item["email"] = item["email"].encode('utf-8')
        if item["url"]:
            item["url"] = item["url"].encode('utf-8')

        if item["phone"] is None and item["has_phone_number"] is True:
            # Step 1, get the URL of the image containing the phone number
            data = json.load(
                urllib2.urlopen(
                    urllib2.Request(
                        'http://www2.leboncoin.fr/ajapi/get/phone?list_id=%s' % item["id"],
                        None, 
                        {
                            # Mimeting Firefox's XHR headers
                            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:25.0) Gecko/20100101 Firefox/25.0", 
                            "Origin": "http://www.leboncoin.fr",
                            "Accept": "*/*",
                            "Accept-Language": "en-US,en;q=0.5",
                            "DNT": "1",
                            "Referer": item["url"],
                        }
                    )
                )
            )
            # Step 2, download it and OCR it
            tmpfile = item['id'] + '.gif'
            try:
                execsh('wget', [data["phoneUrl"], "-O", tmpfile])
                item["phone"] = ocr(tmpfile)
                os.remove(tmpfile)
            except (KeyError, TypeError):
                pass
        return item

class JSONExportPipeline(object):
    def __init__(self):
        self.fname = None

    def open_spider(self, spider):
        self.load_items(spider)

    def load_items(self, spider):
        self.fname = spider.export_results_filename
        try:
            self.items = load_json(self.fname)
        except IOError:
            self.items = {}

    def process_item(self, item, spider):
        print "Processing item for JSON Export..."
        if self.fname is None:
            self.load_items(spider)
        self.items[item["id"]] = item.__dict__["_values"]
        return item

    def close_spider(self, spider):
        print "Dumping data to %s" % self.fname
        write_json(self.items, self.fname)
