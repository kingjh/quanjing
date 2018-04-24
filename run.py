import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from quanjing.spiders.spider import QuanjingSpider

process = CrawlerProcess(get_project_settings())

process.crawl(QuanjingSpider)
process.start()  # the script will block here until the crawling is finished
