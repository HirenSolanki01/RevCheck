import time
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from selenium_stealth import stealth

def scrape_booking_reviews(url, max_reviews=50):
    """
    Scrapes reviews for a given Booking.com hotel URL with stealth capabilities.
    """
    print("Initializing browser in stealth mode...")
    try:
        service = Service()
        options = webdriver.ChromeOptions()
        
        # Use Linux Chromium settings only when available (deployment/server).
        if os.name != 'nt' and os.path.exists('/usr/bin/chromium'):
            options.binary_location = '/usr/bin/chromium'
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

        # options.add_argument("start-maximized") # You can remove or comment this out for server
        # --- STEALTH OPTIONS ---
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        # To run without a visible browser, uncomment the line below
        # options.add_argument('--headless')
        
        driver = webdriver.Chrome(service=service, options=options)
        
        # --- Configure Stealth ---
        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )

    except Exception as e:
        print(f"Error: ChromeDriver setup failed. Details: {e}")
        return pd.DataFrame()

    driver.get(url)
    wait = WebDriverWait(driver, 20) 

    # --- 2. Handle Pop-ups (Cookies) ---
    try:
        accept_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
        accept_button.click()
        print("Accepted cookie policy.")
        time.sleep(1)
    except TimeoutException:
        print("Cookie banner not found or already accepted.")

    # --- 3. Open the Reviews Modal ---
    try:
        reviews_tab_id = 'reviews-tab-trigger'
        print("Waiting for the reviews tab to be clickable...")
        
        reviews_button = wait.until(EC.element_to_be_clickable((By.ID, reviews_tab_id)))
        
        print("Reviews tab is clickable. Scrolling and clicking...")
        driver.execute_script("arguments[0].scrollIntoView(true);", reviews_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", reviews_button)
        
        print("Successfully opened the reviews panel.")

    except TimeoutException as e:
        print(f"Could not find or click the reviews tab with ID '{reviews_tab_id}'. The page structure may have changed. Error: {e}")
        driver.quit()
        return pd.DataFrame()

    # --- 4. Wait for Review Content to be Visible ---
    try:
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-testid="review-card"]')))
        print("Review content is now visible.")
    except TimeoutException:
        print("Review content did not load after clicking the button.")
        driver.quit()
        return pd.DataFrame()
        
    # --- 5. Scrape Reviews with Pagination ---
    scraped_data = []
    unique_reviews = set() # <-- RENAMED for clarity
    print(f"Starting to scrape up to {max_reviews} reviews...")
    
    page_count = 1
    while len(scraped_data) < max_reviews:
        print(f"Scraping page {page_count}...")
        
        time.sleep(2) 
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        review_cards = soup.select('div[data-testid="review-card"]')
        if not review_cards:
            print("Could not find review cards on the page. Ending scrape.")
            break

        new_reviews_found_on_page = 0
        for card in review_cards:
            if len(scraped_data) >= max_reviews:
                break
            
            # Scrape only the title using the data-testid you provided
            title_element = card.select_one('h4[data-testid="review-title"]')
            review_title = title_element.get_text(strip=True) if title_element else "No Title"

            # Avoid duplicate reviews based on the title text
            if review_title and review_title not in unique_reviews:
                unique_reviews.add(review_title)
                # Append a dictionary with the 'review' key as requested
                scraped_data.append({'review': review_title})
                new_reviews_found_on_page += 1
            # --- MODIFICATION END ---

        print(f"Found {new_reviews_found_on_page} new unique reviews on this page.")
        if len(scraped_data) >= max_reviews:
            print(f"Reached the target of {max_reviews} reviews.")
            break

        try:
            next_page_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[aria-label="Next page"]')))
            driver.execute_script("arguments[0].click();", next_page_button)
            page_count += 1
            print("Navigating to next page...")
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, 'div[data-testid="reviews-list-loading-spinner"]')))
        except TimeoutException:
            print("Next page button not found or not clickable. Reached the end.")
            break
        except Exception as e:
            print(f"An error occurred during pagination: {e}")
            break

    # --- 6. Clean up and return data ---
    driver.quit()
    print(f"\nScraping complete. Total unique reviews collected: {len(scraped_data)}")
    
    return pd.DataFrame(scraped_data)

# --- Example Usage ---
if __name__ == '__main__':
    target_url = "https://www.booking.com/hotel/in/the-leela-mumbai.en-gb.html"
    review_df = scrape_booking_reviews(target_url, max_reviews=50)

    if not review_df.empty:
        print("\n--- Scraped Reviews (First 5) ---")
        print(review_df.head())
        review_df.to_csv('scraped_booking_reviews.csv', index=False, encoding='utf-8-sig')
        print("\nSuccessfully saved scraped reviews to 'scraped_booking_reviews.csv'")