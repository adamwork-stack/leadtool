"""
Google Maps spider for LeadTool with Playwright integration
"""
import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.http import Request
import yaml
import os
from datetime import datetime
import re
import json
import urllib.parse
import time


class GoogleMapsSpider(scrapy.Spider):
    name = 'google_maps'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.month_key = datetime.now().strftime("%Y-%m")
        self.config = self.load_config()
        self.search_queries = self.config.get('search_queries', [])
        
    def load_config(self):
        """Load scraping configuration from YAML file"""
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'sites.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {config_path}")
            return {'search_queries': []}
    
    def start_requests(self):
        """Generate initial requests for each search query"""
        print(f"\nStarting scraper with {len(self.search_queries)} search queries")
        
        for i, query in enumerate(self.search_queries, 1):
            print(f"\nQuery {i}/{len(self.search_queries)}: {query.get('name', 'Unnamed')}")
            print(f"   Keywords: {query.get('keywords', 'N/A')}")
            print(f"   Location: {query.get('location', 'N/A')}")
            
            search_url = self.build_search_url(query)
            print(f"   URL: {search_url}")
            
            yield Request(
                url=search_url,
                callback=self.parse,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'networkidle'),
                        PageMethod('wait_for_timeout', 5000),
                        PageMethod('evaluate', 'window.scraper_page = this;')  # Make page available
                    ],
                    'query_config': query,
                    'google_maps_config': self.config.get('google_maps', {})
                }
            )
    
    def build_search_url(self, query_config):
        """Build Google Maps search URL"""
        keywords = query_config.get('keywords', '')
        location = query_config.get('location', '')
        search_query = f"{keywords} in {location}"
        encoded_query = urllib.parse.quote(search_query)
        return f"https://www.google.com/maps/search/{encoded_query}"
    
    def parse(self, response):
        """Parse Google Maps search results and extract business data"""
        query_config = response.meta['query_config']
        google_maps_config = response.meta['google_maps_config']
        
        self.logger.info(f"Processing search query: {query_config.get('name', 'Unknown')}")
        print(f"\nProcessing: {query_config.get('name', 'Unknown')}")
        print(f"URL: {response.url}")
        print("Waiting 5 seconds so you can see the browser...")
        time.sleep(5)  # Pause so you can see the browser
        
        # Get the page object for interactions
        page = response.meta.get('playwright_page')
        if not page:
            # Try to get page from browser context
            try:
                page = response.meta.get('playwright_browser_context').pages[0]
            except:
                print("Could not access page object")
                page = None
        
        if page:
            print("Starting interactive scraping...")
            
            # Wait for results to load
            try:
                page.wait_for_selector('[data-result-index]', timeout=10000)
                print("Found search results, starting to scroll...")
            except:
                print("No results found or timeout waiting for results")
            
            # Scroll through results multiple times
            for scroll_attempt in range(5):
                print(f"Scroll attempt {scroll_attempt + 1}/5")
                
                # Scroll down to load more results
                page.evaluate("""
                    const scrollContainer = document.querySelector('.m6QErb') || 
                                         document.querySelector('[role="main"]') ||
                                         document.querySelector('.section-scrollbox');
                    if (scrollContainer) {
                        scrollContainer.scrollTop = scrollContainer.scrollHeight;
                    } else {
                        window.scrollTo(0, document.body.scrollHeight);
                    }
                """)
                
                # Wait for new results to load
                time.sleep(3)
                
                # Try to click on some business listings
                try:
                    business_links = page.query_selector_all('a[href*="/maps/place/"]')
                    print(f"Found {len(business_links)} business links")
                    
                    # Click on first few business listings
                    for i, link in enumerate(business_links[:3]):
                        try:
                            print(f"Clicking on business {i+1}")
                            link.click()
                            time.sleep(2)  # Wait for details to load
                            
                            # Try to extract business details from the opened panel
                            business_name = page.query_selector('h1') or page.query_selector('.x3AX1-LfntMc-header-title-title')
                            if business_name:
                                print(f"  Business name: {business_name.inner_text()}")
                            
                            # Go back to results
                            page.go_back()
                            time.sleep(2)
                            
                        except Exception as e:
                            print(f"  Error clicking business {i+1}: {e}")
                            continue
                            
                except Exception as e:
                    print(f"Error finding business links: {e}")
        
        # Extract business listings using the updated method
        businesses = self.extract_businesses(response, google_maps_config)
        
        print(f"Found {len(businesses)} businesses")
        
        for i, business_data in enumerate(businesses, 1):
            print(f"  {i}. {business_data.get('name', 'Unknown')} - {business_data.get('category', 'N/A')}")
            # Store business data as company
            yield {
                'type': 'company',
                'month_key': self.month_key,
                'source_url': response.url,
                'query_name': query_config.get('name', ''),
                'data': business_data
            }
        
        # Close browser after scraping is complete
        if page:
            print("Scraping completed, closing browser...")
            try:
                page.close()
                print("Browser tab closed successfully")
            except Exception as e:
                print(f"Error closing browser: {e}")
    
    def scroll_and_parse(self, response):
        """Scroll through results and extract business data"""
        query_config = response.meta['query_config']
        google_maps_config = response.meta['google_maps_config']
        scroll_attempts = response.meta.get('scroll_attempts', 0)
        max_scroll_attempts = google_maps_config.get('search_settings', {}).get('max_scroll_attempts', 10)
        
        # Extract business listings
        businesses = self.extract_businesses(response, google_maps_config)
        
        for business_data in businesses:
            # Store business data as company
            yield {
                'type': 'company',
                'month_key': self.month_key,
                'source_url': response.url,
                'query_name': query_config.get('name', ''),
                'data': business_data
            }
        
        # Continue scrolling if we haven't reached max attempts
        if scroll_attempts < max_scroll_attempts:
            yield Request(
                url=response.url,
                callback=self.scroll_and_parse,
                meta={
                    'playwright': True,
                    'playwright_page_methods': [
                        PageMethod('wait_for_load_state', 'networkidle'),
                        PageMethod('wait_for_timeout', 2000),
                        PageMethod('evaluate', self.get_scroll_script()),
                        PageMethod('wait_for_timeout', 3000)
                    ],
                    'query_config': query_config,
                    'google_maps_config': google_maps_config,
                    'scroll_attempts': scroll_attempts + 1
                }
            )
    
    def extract_businesses(self, response, google_maps_config):
        """Extract business data from Google Maps results"""
        businesses = []
        
        # Try to extract real data from Google Maps
        try:
            businesses = self.extract_businesses_fallback(response, google_maps_config)
            if not businesses:
                self.logger.warning("No businesses found with fallback method")
        except Exception as e:
            self.logger.error(f"Error extracting businesses: {e}")
        
        self.logger.info(f"Extracted {len(businesses)} businesses")
        return businesses
    
    def extract_businesses_fallback(self, response, google_maps_config):
        """Fallback method using CSS selectors"""
        businesses = []
        selectors = google_maps_config.get('selectors', {})
        
        # Try multiple selector patterns
        business_listing_selectors = [
            selectors.get('business_listing', '[data-result-index]'),
            '.Nv2PK',
            '.VkpGBb', 
            '.lI9IFe',
            '[data-result-index]',
            '.section-result',
            '.search-result'
        ]
        
        business_listings = []
        for selector in business_listing_selectors:
            listings = response.css(selector)
            if listings:
                business_listings = listings
                self.logger.info(f"Found {len(listings)} listings with selector: {selector}")
                break
        
        if not business_listings:
            # Try to find any business-like elements
            business_listings = response.css('div').css('a[href*="/maps/place/"]').getall()
            self.logger.warning(f"No business listings found with standard selectors. Found {len(business_listings)} potential links")
        
        for listing in business_listings:
            business_data = self.extract_business_data(listing, selectors)
            if business_data and business_data.get('name'):
                businesses.append(business_data)
        
        return businesses
    
    def extract_business_data(self, listing, selectors):
        """Extract data from a single business listing"""
        try:
            business_data = {
                'name': self.clean_text(listing.css(selectors.get('business_name', 'h3::text')).get()),
                'category': self.clean_text(listing.css(selectors.get('business_category', '.fontBodyMedium::text')).get()),
                'address': self.clean_text(listing.css(selectors.get('business_address', '.fontBodyMedium span::text')).get()),
                'phone': self.clean_phone(listing.css(selectors.get('business_phone', 'a[href^="tel:"]::attr(href)')).get()),
                'website': self.clean_website(listing.css(selectors.get('business_website', 'a[href^="http"]::attr(href)')).get()),
                'rating': self.clean_rating(listing.css(selectors.get('business_rating', '.fontDisplayLarge::text')).get()),
                'review_count': self.clean_review_count(listing.css(selectors.get('business_review_count', '.fontBodyMedium::text')).get()),
                'source': 'Google Maps'
            }
            
            # Clean and validate data
            business_data = {k: v for k, v in business_data.items() if v}
            
            return business_data
            
        except Exception as e:
            self.logger.error(f"Error extracting business data: {e}")
            return None
    
    def clean_text(self, text):
        """Clean and normalize text data"""
        if not text:
            return None
        return text.strip()
    
    def clean_phone(self, phone):
        """Clean phone number"""
        if not phone:
            return None
        # Remove tel: prefix
        phone = phone.replace('tel:', '').strip()
        return phone if phone else None
    
    def clean_website(self, website):
        """Clean website URL"""
        if not website:
            return None
        # Ensure it's a proper URL
        if website.startswith('http'):
            return website
        return None
    
    def clean_rating(self, rating):
        """Clean rating data"""
        if not rating:
            return None
        try:
            # Extract numeric rating
            rating_match = re.search(r'(\d+\.?\d*)', rating)
            if rating_match:
                return float(rating_match.group(1))
        except:
            pass
        return None
    
    def clean_review_count(self, review_text):
        """Clean review count"""
        if not review_text:
            return None
        try:
            # Extract number from review text
            review_match = re.search(r'(\d+)', review_text)
            if review_match:
                return int(review_match.group(1))
        except:
            pass
        return None
    
    def closed(self, spider):
        """Called when the spider is closed"""
        print("Spider finished, cleaning up browser...")
        # The browser will be automatically closed by Scrapy-Playwright
        print("Returning to dashboard...")
    
    def get_scroll_script(self):
        """Get JavaScript to scroll the results container"""
        return """
        () => {
            // Try multiple possible scroll containers
            const containers = [
                '.m6QErb',
                '[role="main"]',
                '.section-scrollbox',
                '.scrollable-y'
            ];
            
            for (const selector of containers) {
                const container = document.querySelector(selector);
                if (container) {
                    container.scrollTop = container.scrollHeight;
                    return true;
                }
            }
            
            // Fallback: scroll the window
            window.scrollTo(0, document.body.scrollHeight);
            return true;
        }
        """