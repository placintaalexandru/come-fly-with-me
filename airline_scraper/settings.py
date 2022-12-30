# Scrapy settings for airline_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import logging
import os
from datetime import timedelta

# BOT_NAME = 'airline_scraper'

SPIDER_MODULES = ['airline_scraper.spiders']
NEWSPIDER_MODULE = 'airline_scraper.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'airline_scraper.middlewares.AirlineScraperSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'airline_scraper.middlewares.AirlineScraperDownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    'airline_scraper.pipelines.AirlineScraperPipeline': 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'
TWISTED_REACTOR = 'twisted.internet.asyncioreactor.AsyncioSelectorReactor'

AUTOTHROTTLE_ENABLED = True

# Default 5
AUTOTHROTTLE_START_DELAY = 5

# Default 60
AUTOTHROTTLE_MAX_DELAY = 100

# Default True
RANDOMIZE_DOWNLOAD_DELAY = True

# Default 1.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5

# Default 2
RETRY_TIMES = 0

DOWNLOADER_MIDDLEWARES = {
    # 'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': None,
    # 'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    # 'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': None,
    # 'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': None,
    # 'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': None,
    # 'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': None,
    # 'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': None,
    # 'scrapy.downloadermiddlewares.stats.DownloaderStats': None,
    # 'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 403,
}

LOG_LEVEL = os.environ.get('LOG_LEVEL', logging.INFO)
LOG_FORMAT = os.environ.get('LOG_FORMAT', '[%(name)s] %(asctime)s %(levelname)s: %(message)s')

# Controls the environment variable that holds the pairs of stations to scrape
ENVIRONMENT_SOURCE_PAIRS = 'PAIRS_TO_SCRAPE'

# Want to scrape 6 months in advance
PERIOD_MONTHS = timedelta(days=os.environ.get('MONTHS_TO_SCRAPE', 180))
