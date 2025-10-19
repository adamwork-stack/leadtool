"""
Scrapy settings for LeadTool spider
"""
import os

# Scrapy settings
BOT_NAME = 'LeadTool'
SPIDER_MODULES = ['app.scraper']
NEWSPIDER_MODULE = 'app.scraper'

# Obey robots.txt
ROBOTSTXT_OBEY = False

# Configure delays
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = 0.5

# Configure concurrent requests
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Configure pipelines
ITEM_PIPELINES = {
    'app.scraper.pipelines.DatabasePipeline': 300,
}

# Configure middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler': 855,
}

# Playwright settings
PLAYWRIGHT_BROWSER_TYPE = 'chromium'
PLAYWRIGHT_LAUNCH_OPTIONS = {
    'headless': False,  # Set to False to see the browser window
    'slow_mo': 2000,  # Slow down actions by 2 seconds so you can see them
    'args': [
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--start-maximized'  # Start browser maximized
    ]
}

# AutoThrottle settings
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Configure logging
LOG_LEVEL = 'INFO'

# Database settings
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/leadtool.db')

# User agent
USER_AGENT = 'LeadTool/1.0 (+https://leadtool.example.com)'

# Disable cookies
COOKIES_ENABLED = False

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False
