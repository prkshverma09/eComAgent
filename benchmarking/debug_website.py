#!/usr/bin/env python3
"""
Debug script to investigate website search functionality
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

WEBSITE_URL = "https://dash-stride-shop.lovable.app/"

def debug_website():
    print("="*70)
    print("WEBSITE DEBUG ANALYSIS")
    print("="*70)
    print(f"\nTarget URL: {WEBSITE_URL}")

    # Setup Chrome
    options = Options()
    # options.add_argument('--headless')  # Comment out to see browser
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    print("\nStarting Chrome (visible mode for debugging)...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        # Load the page
        print(f"\nLoading website...")
        driver.get(WEBSITE_URL)
        time.sleep(3)

        print(f"\nPage Title: {driver.title}")
        print(f"Current URL: {driver.current_url}")

        # Take screenshot
        screenshot_path = "debug_screenshot_1_initial.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")

        # Find all input elements
        print("\n" + "-"*70)
        print("SEARCHING FOR INPUT ELEMENTS")
        print("-"*70)

        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"\nFound {len(inputs)} input elements:")
        for i, inp in enumerate(inputs):
            inp_type = inp.get_attribute("type")
            inp_name = inp.get_attribute("name")
            inp_placeholder = inp.get_attribute("placeholder")
            inp_class = inp.get_attribute("class")
            print(f"  {i+1}. type='{inp_type}', name='{inp_name}', placeholder='{inp_placeholder}', class='{inp_class[:50] if inp_class else None}'")

        # Look for search-related elements
        print("\n" + "-"*70)
        print("SEARCHING FOR SEARCH-RELATED ELEMENTS")
        print("-"*70)

        search_selectors = [
            ("input[type='search']", "Search input"),
            ("input[placeholder*='search' i]", "Input with search placeholder"),
            ("input[placeholder*='Search' i]", "Input with Search placeholder"),
            ("[class*='search']", "Elements with 'search' in class"),
            ("button[class*='search']", "Search button"),
            ("a[href*='search']", "Search link"),
            ("[aria-label*='search' i]", "Elements with search aria-label"),
            ("svg[class*='search']", "Search icon (SVG)"),
            (".fa-search", "Font Awesome search icon"),
        ]

        for selector, description in search_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"\n✓ Found {len(elements)} element(s): {description}")
                    for elem in elements[:3]:
                        tag = elem.tag_name
                        text = elem.text[:50] if elem.text else ""
                        print(f"    <{tag}> {text}")
            except Exception as e:
                pass

        # Look for product elements
        print("\n" + "-"*70)
        print("SEARCHING FOR PRODUCT ELEMENTS")
        print("-"*70)

        product_selectors = [
            (".product-card", "Product cards"),
            (".product-item", "Product items"),
            ("[data-product]", "Data-product attributes"),
            (".product", "Product class"),
            ("article", "Article elements"),
            (".card", "Card elements"),
            (".grid > div", "Grid children"),
            ("[class*='shoe']", "Elements with 'shoe' in class"),
            ("[class*='product']", "Elements with 'product' in class"),
        ]

        for selector, description in product_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"\n✓ Found {len(elements)} element(s): {description}")
                    for elem in elements[:2]:
                        tag = elem.tag_name
                        text = elem.text[:100].replace('\n', ' ') if elem.text else ""
                        print(f"    <{tag}> {text}...")
            except Exception as e:
                pass

        # Try to find and interact with navigation
        print("\n" + "-"*70)
        print("CHECKING NAVIGATION")
        print("-"*70)

        nav_links = driver.find_elements(By.CSS_SELECTOR, "nav a, header a, a[href*='product'], a[href*='shop']")
        print(f"\nFound {len(nav_links)} navigation links:")
        for link in nav_links[:10]:
            href = link.get_attribute("href")
            text = link.text.strip()
            if text or href:
                print(f"  - '{text}' -> {href}")

        # Try clicking on "Shop" or "Products" link if exists
        print("\n" + "-"*70)
        print("ATTEMPTING TO NAVIGATE TO PRODUCTS PAGE")
        print("-"*70)

        for link in nav_links:
            text = link.text.strip().lower()
            href = (link.get_attribute("href") or "").lower()
            if 'shop' in text or 'product' in text or 'shop' in href or 'product' in href:
                print(f"\nClicking: '{link.text}' -> {link.get_attribute('href')}")
                try:
                    link.click()
                    time.sleep(3)
                    print(f"New URL: {driver.current_url}")

                    # Screenshot after navigation
                    screenshot_path = "debug_screenshot_2_products.png"
                    driver.save_screenshot(screenshot_path)
                    print(f"Screenshot saved: {screenshot_path}")

                    # Look for products again
                    for selector, description in product_selectors:
                        try:
                            elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                print(f"\n✓ After navigation - Found {len(elements)} element(s): {description}")
                        except:
                            pass
                    break
                except Exception as e:
                    print(f"  Could not click: {e}")

        # Check page source for clues
        print("\n" + "-"*70)
        print("PAGE SOURCE ANALYSIS")
        print("-"*70)

        page_source = driver.page_source
        keywords = ['search', 'product', 'shoe', 'cart', 'price', 'filter']
        for keyword in keywords:
            count = page_source.lower().count(keyword)
            print(f"  '{keyword}' appears {count} times in page source")

        # Final screenshot
        screenshot_path = "debug_screenshot_final.png"
        driver.save_screenshot(screenshot_path)
        print(f"\nFinal screenshot saved: {screenshot_path}")

        print("\n" + "="*70)
        print("DEBUG COMPLETE")
        print("="*70)
        print("\nCheck the screenshots to see what the page looks like.")
        print("The website may not have a traditional search feature.")

        input("\nPress Enter to close browser...")

    finally:
        driver.quit()


if __name__ == "__main__":
    debug_website()
