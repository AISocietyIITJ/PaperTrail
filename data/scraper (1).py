import pandas as pd
from bs4 import BeautifulSoup
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re

def scrape_scholar_org(org_id):
    url = f"https://scholar.google.com/citations?view_op=view_org&org={org_id}&hl=en"
    scholars_data = []

    print("Initializing browser...")
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
    })
    
    print(f"Navigating to {url}")
    driver.get(url)

    time.sleep(3)

    page_num = 1
    while True:
        print(f"Scraping page {page_num}...")
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.gsc_1usr"))
            )
        except Exception:
            time.sleep(30)
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.gsc_1usr"))
                )
            except:
                print("no profiles found")
                break

        html = driver.page_source
        if page_num == 1:
            with open("debug_page1.html", "w", encoding="utf-8") as f:
                f.write(html)

        soup = BeautifulSoup(html, "html.parser")
        profiles = soup.find_all("div", class_="gsc_1usr")
        
        if not profiles:
            break
            
        for idx, profile in enumerate(profiles):
            name_tag = profile.find("h3", class_="gs_ai_name")
            name = name_tag.text.strip() if name_tag else ""
            
            profile_url = ""
            if name_tag and name_tag.find("a"):
                href = name_tag.find("a").get("href", "")
                if href:
                    profile_url = "https://scholar.google.com" + href

            affil_tag = profile.find("div", class_="gs_ai_aff")
            affiliation = affil_tag.text.strip() if affil_tag else ""
            
            cited_tag = profile.find("div", class_="gs_ai_cby")
            cited_by = cited_tag.text.replace("Cited by", "").strip() if cited_tag else ""

            interests = [a.text.strip() for a in profile.find_all("a", class_="gs_ai_one_int")]
            
            scholar_info = {
                'Name': name,
                'Affiliation': affiliation,
                'Interests': ', '.join(interests),
                'Cited By': cited_by,
                'Profile URL': profile_url
            }
            
            if name:
                scholars_data.append(scholar_info)

        print(f"Scraped {len(profiles)} authors on page {page_num}. Total: {len(scholars_data)}")

        try:
            next_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Next']")
            if next_button.is_enabled():
                if next_button.get_attribute("disabled"):
                    break
                driver.execute_script("arguments[0].click();", next_button)
                time.sleep(random.uniform(2.0, 4.0)) 
                page_num += 1
            else:
                break
        except Exception as e:
            print(f"Error {e}")
            break

    driver.quit()

    print(f"Total authors retrieved: {len(scholars_data)}")
    
    if scholars_data:
        df = pd.DataFrame(scholars_data)
        df.drop_duplicates(subset=['Profile URL'], inplace=True)
        csv_filename = "scholars_data.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"Data saved to {csv_filename} with {len(df)} unique records.")
    else:
        print("No data was retrieved.")

if __name__ == "__main__":
    ORG_ID = "4137058844232715996"
    scrape_scholar_org(9904414229552554802)
