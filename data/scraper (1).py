import pandas as pd
from bs4 import BeautifulSoup
import time
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import re

# Skip profiles whose Affiliation contains any of these (case-insensitive) —
# used to filter out students (M.Tech, research scholars, PhD scholars etc.)
# and keep only actual faculty/professors.
EXCLUDED_AFFILIATION_KEYWORDS = [
    "research scholar",
    "m tech",
    "m.tech",
    "mtech",
]

# Hard cap on number of professors to collect. The script stops scraping
# new pages once this many qualifying professors have been gathered.
# Can end up with FEWER than this (e.g. if the org has fewer profiles, or
# many get filtered out), but never MORE.
MAX_PROFESSORS = 200

# Persistent Chrome profile directory. Using a fixed folder here means
# cookies / login sessions are SAVED between runs, so you won't have to log
# in again each time you run the script. First run: log in normally when
# prompted. Every run after that: Chrome will already be logged in.
CHROME_PROFILE_DIR = "./chrome_profile"


def is_excluded_affiliation(affiliation: str) -> bool:
    aff_lower = affiliation.lower()
    return any(keyword in aff_lower for keyword in EXCLUDED_AFFILIATION_KEYWORDS)


def fetch_indices(driver, profile_url):
    """Visit a scholar's profile page and pull their h-index and i10-index."""
    h_index, i10_index = "", ""
    try:
        driver.get(profile_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.gsc_rsb_std"))
        )
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        stats = soup.select("td.gsc_rsb_std")
        values = [s.text.strip() for s in stats]
        # order: [Citations-All, Citations-Since, h-index-All, h-index-Since, i10-index-All, i10-index-Since]
        if len(values) >= 6:
            h_index = values[2]
            i10_index = values[4]
    except Exception as e:
        print(f"    [warn] could not fetch indices for {profile_url}: {e}")
    return h_index, i10_index


def scrape_scholar_org(org_id,csv_filename):
    url = f"https://scholar.google.com/citations?view_op=view_org&org={org_id}&hl=en"
    scholars_data = []

    print("Initializing browser...")
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(f"--user-data-dir={os.path.abspath(CHROME_PROFILE_DIR)}")
    options.add_argument("--profile-directory=Default")
    
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
            
            if name and not is_excluded_affiliation(affiliation):
                scholars_data.append(scholar_info)

            if len(scholars_data) >= MAX_PROFESSORS:
                break

        print(f"Scraped {len(profiles)} authors on page {page_num}. Total: {len(scholars_data)}")

        if len(scholars_data) >= MAX_PROFESSORS:
            print(f"Reached MAX_PROFESSORS cap ({MAX_PROFESSORS}), stopping.")
            break

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

    # Safety net: guarantee we never exceed MAX_PROFESSORS, even if pagination
    # logic above ever changes. Never adds rows, only trims if over.
    if len(scholars_data) > MAX_PROFESSORS:
        scholars_data = scholars_data[:MAX_PROFESSORS]

    # --- Fetch h-index / i10-index for every scholar collected above ---
    print(f"\nFetching h-index and i10-index for {len(scholars_data)} scholars...")
    for i, scholar in enumerate(scholars_data, start=1):
        profile_url = scholar.get('Profile URL', '')
        if not profile_url:
            scholar['h-index'] = ''
            scholar['i10-index'] = ''
            continue

        print(f"  [{i}/{len(scholars_data)}] {scholar['Name']}")
        h_index, i10_index = fetch_indices(driver, profile_url)
        scholar['h-index'] = h_index
        scholar['i10-index'] = i10_index

        if h_index:
            print(f"    -> h-index={h_index}, i10-index={i10_index}")
        else:
            print("    -> could not retrieve indices")

        time.sleep(random.uniform(2.0, 4.0))

    driver.quit()

    print(f"Total authors retrieved: {len(scholars_data)}")
    
    if scholars_data:
        df = pd.DataFrame(scholars_data)
        df.drop_duplicates(subset=['Profile URL'], inplace=True)
        # csv_filename = "kharagpur_data.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8')
        print(f"Data saved to {csv_filename} with {len(df)} unique records.")
    else:
        print("No data was retrieved.")

# if __name__ == "__main__":
#     ORG_ID = 9904414229552554802
#     csv_file = "kanpur.csv"
#     scrape_scholar_org(ORG_ID,csv_filename=csv_file)

orgs = {8653688121748243861:"kanpur_data.csv",7829249322942557987:"indore_data.csv", 1706247663701369794:"hyderabad_data.csv",11345352608396081237:"guwahati_data.csv"}

for key, val in orgs.items():
    scrape_scholar_org(key,val)