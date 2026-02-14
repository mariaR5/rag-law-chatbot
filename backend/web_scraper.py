import requests
import json
import time
import re
from bs4 import BeautifulSoup

def scrape_with_brightdata(user_query, api_token):
    dataset_id = "gd_mbz66arm2mf9cu856y"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    
    # Trigger scrape
    trigger_url = f"https://api.brightdata.com/datasets/v3/trigger?dataset_id={dataset_id}&include_errors=true"
    payload = json.dumps([{"url": "https://gemini.google.com/", "prompt": user_query, "index": 1}])

    print(f"Triggering scrape for: '{user_query}'...")
    response = requests.post(trigger_url, headers=headers, data=payload)
    
    if response.status_code != 200:
        return f"Error triggering: {response.text}"

    snapshot_id = response.json().get("snapshot_id")
    print(f"Scrape started. Snapshot ID: {snapshot_id}")
    snapshot_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
    
    # Poll for results
    raw_data = None
    while True:
        result_response = requests.get(snapshot_url, headers=headers)
        if result_response.status_code == 200:
            raw_data = result_response.json()
            print("Scrape complete! Parsing data...")
            break
        elif result_response.status_code == 202:
            print("Still processing... waiting 10s")
            time.sleep(10)
        else:
            return f"Error retrieving data: {result_response.status_code}"

    # Extract and clean data
    try:
        # Print keys to see what we actually got
        if not raw_data or not isinstance(raw_data, list):
            return "No data returned or unexpected format."
        
        first_record = raw_data[0]
        
        # Try multiple common keys for the answer content
        html_content = (
            first_record.get("message-content") or 
            first_record.get("answer_text_markdown") or 
            first_record.get("response_text") or 
            ""
        )
        
        if not html_content:
            return "Could not find content field in response."

        # Strip HTML tags
        soup = BeautifulSoup(html_content, "html.parser")
        for sup in soup.find_all(["sup", "script", "style"]):
            sup.decompose()
        
        clean_text = soup.get_text(separator=" ", strip=True)
        
        clean_text = clean_text.replace("", "").strip()

        # Take first two sentences
        sentences = re.findall(r'[^.!?]+[.!?]', clean_text)
        
        if len(sentences) >= 1:
            return " ".join(sentences[:2])
        else:
            return clean_text[:250] + "..."
            
    except Exception as e:
        return f"Parsing Error: {str(e)}"