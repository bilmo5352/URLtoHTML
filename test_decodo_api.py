# fixed_decodo_poll.py
import requests
import time
import os
import re
from urllib.parse import urlparse

USERNAME = "U0000326616"
PASSWORD = "PW_1cbb25eb0fb4a38c0ba6a049c18da34be"

BATCH_URL = "https://scraper-api.decodo.com/v2/task/batch"
RESULT_URL = "https://scraper-api.decodo.com/v2/task/{task_id}/results"

# Function to save HTML to file
def save_html(url, html_content, task_id):
    """Save HTML content to a file in the root folder."""
    # Create a safe filename from the URL
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '').replace('.', '_')
    path = parsed.path.strip('/').replace('/', '_')
    if not path:
        path = 'index'
    
    # Remove query parameters from path and add them as suffix if needed
    if parsed.query:
        query_part = parsed.query[:30].replace('=', '_').replace('&', '_')
        query_part = re.sub(r'[^\w\-_]', '_', query_part)
        path = f"{path}_{query_part}"
    
    # Remove any special characters
    filename = re.sub(r'[^\w\-_]', '_', f"decodo_{domain}_{path}_{task_id}")
    filename = f"{filename}.html"
    
    # Save to root folder (current directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"    💾 Saved to: {filename}")
        return filepath
    except Exception as e:
        print(f"    ❌ Failed to save: {e}")
        return None

# Example URLs
urls = [
    "https://www.meesho.com/search?q=saree",
]

payload = {
    # use "url" or "queries" depending on preferred format; here we use "url"
    "url": urls,
    "target": "universal",
    # Force JS rendering if desired:
    # "headless": True,
    "render_js": True,
    "device_type": "desktop"
}

# Submit batch
resp = requests.post(BATCH_URL, auth=(USERNAME, PASSWORD), json=payload)
resp.raise_for_status()
batch_resp = resp.json()
print("Batch submission response (top-level):")
print(batch_resp)

# --- Extract per-URL task ids (handle both "queries" and "tasks") ---
task_entries = []
if isinstance(batch_resp, dict):
    if "queries" in batch_resp and isinstance(batch_resp["queries"], list):
        task_entries = batch_resp["queries"]
    elif "tasks" in batch_resp and isinstance(batch_resp["tasks"], list):
        task_entries = batch_resp["tasks"]
    elif isinstance(batch_resp.get("id"), (str, int)) and "url" in batch_resp:
        # single-task response fallback
        task_entries = [batch_resp]
elif isinstance(batch_resp, list):
    task_entries = batch_resp

# Build mapping: task_id -> url (if available)
task_map = {}   # task_id (str) -> url (str or None)
for entry in task_entries:
    if isinstance(entry, dict):
        tid = entry.get("id") or entry.get("task_id") or entry.get("query_id")
        url_field = entry.get("url") or entry.get("query") or None
        if tid:
            task_map[str(tid)] = url_field
    elif isinstance(entry, str):
        # sometimes API returns list of ids as strings
        task_map[entry] = None

if not task_map:
    # if nothing found, fall back to batch id (helpful for debugging)
    print("Warning: no individual task ids found in the batch response.")
    if isinstance(batch_resp, dict) and "id" in batch_resp:
        print("Batch id:", batch_resp["id"])
    raise SystemExit("No per-task ids to poll. Inspect batch response above.")

print("\nTask mapping (task_id -> url):")
for k, v in task_map.items():
    print(f"{k} -> {v}")

# --- Poll results for each task id ---
def fetch_results(task_id):
    url = RESULT_URL.format(task_id=task_id)
    return requests.get(url, auth=(USERNAME, PASSWORD))

results = {}
max_wait = 180         # seconds total wait per task (tune as needed)
initial_interval = 2.0

for tid, original_url in task_map.items():
    print(f"\nPolling task {tid} (url: {original_url}) ...")
    print(f"  Max wait time: {max_wait}s")
    waited = 0.0
    interval = initial_interval
    poll_count = 0
    while waited < max_wait:
        poll_count += 1
        if poll_count % 10 == 0:  # Log every 10 attempts
            print(f"  Still polling... ({poll_count} attempts, {waited:.1f}s elapsed)")
        try:
            r = fetch_results(tid)
            # If 404 or 204, treat as "not ready yet" and retry
            # 404 = task not found yet, 204 = no content (still processing)
            if r.status_code in (404, 204):
                if waited == 0:
                    print(f"  {tid}: Task not ready yet (status {r.status_code}), starting polling...")
                time.sleep(interval)
                waited += interval
                interval = min(interval * 1.5, 10)
                continue
            r.raise_for_status()
            data = r.json()
        except requests.exceptions.HTTPError as e:
            # For other HTTP errors, print and retry a few times
            print(f"  HTTP error for {tid}: {e} — waiting {interval}s and retrying...")
            time.sleep(interval)
            waited += interval
            interval = min(interval * 1.5, 10)
            continue
        except ValueError:
            # Non-JSON response (task still processing or not ready)
            if waited == 0:
                print(f"  {tid}: Waiting for task to start processing...")
            time.sleep(interval)
            waited += interval
            interval = min(interval * 1.5, 10)
            continue

        # Check common "done" indicator (API responses vary)
        status = None
        if isinstance(data, dict):
            status = data.get("status") or data.get("state")
        # If the API returns actual result data fields, treat it as ready
        if status == "done" or "result" in data or "data" in data or data:
            print(f"  Task {tid} ready. Storing result.")
            results[tid] = data
            break

        # Not ready yet
        print(f"  Task {tid} status: {status} — waiting {interval}s...")
        time.sleep(interval)
        waited += interval
        interval = min(interval * 1.5, 10)
    else:
        print(f"  Timed out waiting for {tid} after {max_wait} seconds.")
        results[tid] = None

# --- Print summary ---
print("\n" + "=" * 60)
print("=== Results summary ===")
print("=" * 60)
saved_count = 0
for tid, res in results.items():
    print(f"\n--- {tid} (url: {task_map.get(tid)}) ---")
    if res is None:
        print("No result (timed out or failed).")
        continue

    if isinstance(res, dict) and "results" in res:
        r0 = res["results"][0]  # first page of the result

        html = r0.get("content")
        status = r0.get("status")
        final_url = r0.get("url")

        print("Status:", status)
        print("Final URL:", final_url)

        if html:
            print("\n--- HTML PREVIEW (first 500 chars) ---")
            print(html[:500])
            print()
            # Save HTML to file
            original_url = task_map.get(tid, final_url)
            saved_file = save_html(original_url, html, tid)
            if saved_file:
                saved_count += 1
        else:
            print("No HTML content returned.")

    else:
        print("Unexpected result format:")
        print(str(res)[:500])

print("\n" + "=" * 60)
if saved_count > 0:
    print(f"✅ Processing complete! {saved_count} HTML file(s) saved in the root folder.")
else:
    print("⚠️ Processing complete, but no HTML files were saved.")
    print("   (Tasks may still be processing or failed)")
print("=" * 60)
