import requests
import json
import time
import re

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

    # Extract and clean data (ONLY from answer_text_markdown)
    try:
        if not raw_data or not isinstance(raw_data, list):
            return "No data returned or unexpected format."
        
        first_record = raw_data[0]
        answer_text = first_record.get("answer_text_markdown", "")
        
        if not answer_text:
            return "answer_text_markdown not found in response."

        clean_text = answer_text.strip()

        # Take first two sentences
        sentences = re.findall(r'[^.!?]+[.!?]', clean_text)
        
        if len(sentences) >= 1:
            return " ".join(sentences[:2])
        else:
            return clean_text[:250] + "..."
            
    except Exception as e:
        return f"Parsing Error: {str(e)}"
