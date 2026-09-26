import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# 1. Authenticate to get the Admin JWT token
login_url = "http://127.0.0.1:5000/api/login"
login_payload = {
    "email": os.getenv("ADMIN_EMAIL"),
    "password": os.getenv("ADMIN_PASS")
}

session = requests.Session()
response = session.post(login_url, json=login_payload)

if response.status_code == 200:
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Fetch the analytics summary payload from your backend
    analytics_url = "http://127.0.0.1:5000/api/analytics/summary"
    analytics_response = session.get(analytics_url, headers=headers)
    
    if analytics_response.status_code == 200:
        data = analytics_response.json()
        
        # 3. Convert MongoDB collections into Pandas DataFrames
        events_df = pd.DataFrame(data.get("events", []))
        tasks_df = pd.DataFrame(data.get("tasks", []))
        budgets_df = pd.DataFrame(data.get("budgets", []))
        
        print("Successfully loaded data into DataFrames!")
        print(f"Total Events: {len(events_df)}")
        print(f"Total Tasks: {len(tasks_df)}")
        print(f"Total Budgets: {len(budgets_df)}")

        # Save DataFrames as CSV files for Power BI ingestion
        events_df.to_csv("events_export.csv", index=False)
        tasks_df.to_csv("tasks_export.csv", index=False)
        budgets_df.to_csv("budgets_export.csv", index=False)

        print("Exported all collections to CSV successfully!")
    else:
        print("Failed to fetch analytics data:", analytics_response.text)
else:
    print("Admin authentication failed:", response.text)