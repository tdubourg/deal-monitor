deal-monitor
============

A bot to monitor second hand / craiglist-like websites for good deals about a given set of keywords.

This is currently VERY EXPERIMENTAL. The program is currently in development. A first prototype is working but works with only one specific website.

Current features:
- Scraping items for a given set of region/query/category of items
- Scraping incrementally (partial runs vs. full runs at different intervals)
- OCR-ing images that contain phone numbers and storing the data OCR-ed.
- Filtering scraped items and, based on filters:
    - Alerting the user (based on price, currently, ASAP: based on content)
    - Auto-contacting the advertiser website's form (POST-based forms only)
    - Auto-contacting the advertiser by text message (an Android app (cf. android/) has to be installed on your phone, text messages will be sent by your phone (thus free, if you have a free texting mobile plan).

