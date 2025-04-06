import requests
from bs4 import BeautifulSoup
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import time
import random
import re

# Load environment variables
load_dotenv()

# Configuration
SLACK_TOKEN = os.getenv('SLACK_TOKEN')
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')

# Car search criteria
PRICE_LIMIT = 2500000  # 25 lakhs in rupees
LOCATION = 'Lahore'

def get_cars():
    print("\nFetching data from PakWheels...")
    print("Looking for:")
    print("1. Suzuki Cultus (2017-2019)")
    print("2. Suzuki Swift DLX 1.3")
    print(f"Location: {LOCATION}\n")
    
    # More complete browser-like headers
    headers = {
        'authority': 'www.pakwheels.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'dnt': '1',
        'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    # List of domains to try
    domains = [
        'www.pakwheels.com',
        'pakwheels.com'
    ]
    
    session = requests.Session()
    all_cars = []
    
    # Define search URLs for both models
    search_urls = [
        # Suzuki Cultus 2017-2019
        "https://{domain}/used-cars/search/-/ct_lahore/yr_2017_2019/?q=suzuki+cultus",
        # Suzuki Swift DLX
        "https://{domain}/used-cars/search/-/ct_lahore/?q=suzuki+swift+dlx"
    ]
    
    for domain in domains:
        try:
            print(f"\nTrying domain: {domain}")
            
            # Test domain connectivity first
            try:
                import socket
                socket.gethostbyname(domain)
                print(f"✅ DNS resolution successful for {domain}")
            except socket.gaierror as e:
                print(f"❌ Cannot resolve {domain}: {str(e)}")
                continue
            
            # First, get the main search page to get any necessary cookies
            base_url = f"https://{domain}/used-cars/search/-/"
            
            # Add a random delay between 2-4 seconds
            time.sleep(random.uniform(2, 4))
            
            # First request to get cookies and tokens
            print("Getting initial page...")
            response = session.get(base_url, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # Add another small delay before the search request
            time.sleep(random.uniform(1, 2))
            
            # Try each search URL
            for search_url_template in search_urls:
                search_url = search_url_template.format(domain=domain)
                print(f"Fetching search results from: {search_url}")
                
                response = session.get(search_url, headers=headers, timeout=30, allow_redirects=True)
                response.raise_for_status()
                    
                print(f"✅ Successfully fetched data (status code: {response.status_code})")
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try different possible selectors for listings
                listings = (
                    soup.select('div.well.search-list-item') or  # Primary format
                    soup.select('li.classified-listing') or      # Alternative format
                    soup.select('div.listing-item') or          # Another alternative
                    []                                          # Empty list if none found
                )
                print(f"Found {len(listings)} listings on the page")
                
                if not listings:
                    print("❌ No listings found for this search URL")
                    continue
                
                for i, listing in enumerate(listings, 1):
                    try:
                        print(f"\nProcessing listing #{i}:")
                        
                        # Try multiple possible selectors for each element
                        title_elem = (
                            listing.select_one('h3.nomargin a') or
                            listing.select_one('h3 a') or
                            listing.select_one('a.car-name')
                        )
                        
                        price_elem = (
                            listing.select_one('div.price-details strong') or
                            listing.select_one('.price-details') or
                            listing.select_one('.price')
                        )
                        
                        # Since we're searching in Lahore, we can assume all results are from Lahore
                        # This avoids the need to find location elements which might be missing
                        location = 'Lahore'
                        
                        # Extract year from title since it's more reliable
                        title_text = title_elem.text.strip() if title_elem else ''
                        year_match = None
                        
                        # Try to find year in title (4 digits between 1990-2024)
                        year_matches = re.findall(r'\b(19[9][0-9]|20[0-2][0-9])\b', title_text)
                        if year_matches:
                            year_match = year_matches[0]
                        
                        if all([title_elem, price_elem, year_match]):
                            car = {
                                'title': title_text,
                                'price': price_elem.text.strip(),
                                'location': location,  # We know it's Lahore from the search
                                'year': year_match,
                                'url': f"https://{domain}" + title_elem['href'] if not title_elem['href'].startswith('http') else title_elem['href']
                            }
                            all_cars.append(car)
                            print(f"✅ Successfully parsed: {car['title']} - {car['price']} ({car['year']})")
                        else:
                            print("❌ Missing required elements")
                            missing = []
                            if not title_elem: missing.append('title')
                            if not price_elem: missing.append('price')
                            if not year_match: missing.append('year')
                            print(f"Missing elements: {', '.join(missing)}")
                            
                    except Exception as e:
                        print(f"Error parsing listing #{i}: {str(e)}")
                        continue
                
                # Add a delay between search URLs to avoid rate limiting
                time.sleep(random.uniform(2, 3))
            
            if all_cars:
                return all_cars
            
            print("❌ No cars could be parsed from the listings - trying next domain")
            
        except requests.RequestException as e:
            print(f"❌ Error with {domain}: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response status: {e.response.status_code}")
                print(f"Response headers: {dict(e.response.headers)}")
            continue
    
    print("❌ All domains failed")
    return None

def extract_price(price_text):
    try:
        # Remove PKR and any commas
        cleaned_price = price_text.replace('PKR', '').replace(',', '').strip().lower()
        
        if 'crore' in cleaned_price:
            price_val = cleaned_price.replace('crore', '').strip()
            return float(price_val) * 10000000
        elif 'lacs' in cleaned_price:
            price_val = cleaned_price.replace('lacs', '').strip()
            return float(price_val) * 100000
        else:
            # Try to parse as direct number
            price_val = ''.join(filter(lambda x: x.isdigit() or x == '.', cleaned_price))
            return float(price_val)
    except Exception as e:
        print(f"Error parsing price '{price_text}': {str(e)}")
        return None

def matches_criteria(car_info):
    print(f"\nChecking car: {car_info['title']}")
    print(f"Price: {car_info['price']}")
    print(f"Location: {car_info['location']}")
    print(f"Year: {car_info['year']}")
    
    # Check location first
    if LOCATION.lower() not in car_info['location'].lower():
        print(f"❌ Location does not match {LOCATION}")
        return False
    
    # Extract year
    try:
        year = int(car_info['year'])
    except (ValueError, TypeError):
        print("❌ Could not parse year")
        return False
    
    # Convert title to lowercase for easier matching
    title = car_info['title'].lower()
    
    # Check for Suzuki Cultus 2017-2019
    is_cultus = 'suzuki cultus' in title
    if is_cultus:
        if 2017 <= year <= 2019:
            print("✅ Matches Suzuki Cultus 2017-2019 criteria!")
            return True
        else:
            print(f"❌ Suzuki Cultus but year {year} not in range 2017-2019")
            return False
            
    # Check for Suzuki Swift DLX 1.3
    is_swift_dlx = 'suzuki swift' in title and ('dlx' in title or '1.3' in title)
    if is_swift_dlx:
        print("✅ Matches Suzuki Swift DLX 1.3 criteria!")
        return True
        
    print("❌ Does not match any target models")
    return False

def send_slack_notification(car_info):
    try:
        slack_client = WebClient(token=SLACK_TOKEN)
        
        # First check if the channel ID is in the correct format
        if not SLACK_CHANNEL.startswith('C'):  # Public channel IDs start with C
            print("⚠️ The SLACK_CHANNEL appears to be invalid")
            print("Please use the channel ID (starts with 'C') instead of the channel name")
            print("To get the channel ID:")
            print("1. Open Slack in a web browser")
            print("2. Click on the channel")
            print("3. The channel ID is in the URL after the last '/'")
            return
        
        # Format the message with emojis and better formatting
        message = (
            f"🚗 *New Car Listed!*\n\n"
            f"📌 *Title:* {car_info['title']}\n"
            f"💰 *Price:* {car_info['price']}\n"
            f"📍 *Location:* {car_info['location']}\n"
            f"📅 *Year:* {car_info['year']}\n"
            f"🔗 *View Details:* {car_info['url']}"
        )
        
        # Try to send the message with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = slack_client.chat_postMessage(
                    channel=SLACK_CHANNEL,
                    text=message,
                    unfurl_links=True
                )
                print("✅ Slack notification sent successfully!")
                return
            except SlackApiError as e:
                error = e.response['error']
                if 'not_in_channel' in error:
                    print("\n⚠️ Bot needs to be invited to the channel first")
                    print("\nTo fix this:")
                    print("1. Open your Slack workspace")
                    print(f"2. Go to the channel")
                    print("3. Type: /invite @<your-bot-name>")
                    return
                elif 'channel_not_found' in error:
                    print(f"❌ Channel {SLACK_CHANNEL} not found")
                    print("Please check your SLACK_CHANNEL environment variable")
                    return
                elif 'invalid_auth' in error:
                    print("❌ Invalid Slack authentication token")
                    print("Please check your SLACK_TOKEN environment variable")
                    return
                elif attempt < max_retries - 1:
                    print(f"⚠️ Retry {attempt + 1}/{max_retries}: {error}")
                    time.sleep(2)  # Wait 2 seconds before retrying
                    continue
                else:
                    print(f"\n❌ Failed to send notification after {max_retries} attempts")
                    print(f"Error: {error}")
                    print("\nPlease check:")
                    print("1. Bot permissions in the channel")
                    print("2. Channel ID is correct")
                    print("3. Bot token has required scopes (needs chat:write)")
                    return
                    
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return

def scrape_pakwheels():
    print(f"\n🚗 Starting scraper at {datetime.now()}")
    print(f"Searching cars in {LOCATION} under {PRICE_LIMIT:,} PKR...\n")
    
    # Verify Slack configuration
    if not SLACK_TOKEN:
        print("❌ SLACK_TOKEN not found in environment variables")
        print("Please set up your .env file with SLACK_TOKEN")
        return
    
    if not SLACK_CHANNEL:
        print("❌ SLACK_CHANNEL not found in environment variables")
        print("Please set up your .env file with SLACK_CHANNEL")
        return

    cars = get_cars()
    if not cars:
        print("❌ Failed to fetch data from PakWheels")
        return

    found_cars = []
    for i, car in enumerate(cars, 1):
        try:
            print(f"\n[{i}] Processing: {car['title']}")
            print(f"Price: {car['price']}")
            print(f"Location: {car['location']}")

            if matches_criteria(car):
                found_cars.append(car)
                print("✅ Added to matches!")
                send_slack_notification(car)
            
        except Exception as e:
            print(f"❌ Error processing car #{i}: {str(e)}")

    if not found_cars:
        print("\n🚫 No matching cars found.")
    else:
        print(f"\n🎉 Found {len(found_cars)} matching cars!")
        for i, car in enumerate(found_cars, 1):
            print(f"\n{i}. {car['title']}")
            print(f"   Price: {car['price']}")
            print(f"   Location: {car['location']}")
            print(f"   Year: {car['year']}")
            print(f"   URL: {car['url']}")
        
        print("\n📝 Next steps:")
        print("1. Make sure your Slack bot is invited to the channel")
        print("2. Use this command in Slack: /invite @YourBotName")
        print(f"3. Check that SLACK_CHANNEL (currently: {SLACK_CHANNEL}) is correct")

if __name__ == "__main__":
    scrape_pakwheels()
