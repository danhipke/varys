from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import sys
import csv

from varys.spiders.crawl_spider import VarysCrawlSpider

def main():
    f = open(sys.argv[1], 'rb')
    reader = csv.reader(f)
    rows = [r for r in reader]
    row = rows[1]
    #spider = VarysCrawlSpider()
    #process = CrawlerProcess({
    #    'USER_AGENT': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
    #})
    process = CrawlerProcess(get_project_settings())
    process.crawl(VarysCrawlSpider, name='varys-spider', allowed_domains=[row[0]], start_urls=[row[1]],
                  pdp_link_css_selector=row[2], paginate_link_css_selector=row[3])
    process.start() # the script will block here until the crawling is finished

if __name__ == "__main__":
    main()