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

class DealmonitorPipeline(object):
    def process_item(self, item, spider):
        if item["phone"] is None and item["has_phone_number"] is True: # TODO make an actual request and get the right Gif file url to load
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
            execsh('wget', [data["phoneUrl"], "-O", tmpfile])
            item["phone"] = ocr(tmpfile)
            os.remove(tmpfile)
        return item
