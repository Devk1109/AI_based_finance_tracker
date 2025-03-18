import pandas as pd
import random
import string
import os
from datetime import datetime, timedelta

# Define sample transactions
transactions = [
    "Netflix subscription", "Uber ride", "Starbucks coffee", "Grocery shopping",
    "Electric bill payment", "Mall shopping", "Spotify subscription",
    "Gas station refill", "Amazon purchase", "Movie tickets",
    "Fast food order", "Train ticket", "Gym membership", "Restaurant dinner"
]

# Function to generate a random alphanumeric transaction ID
def generate_transaction_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Users to generate transactions for
users = ["admin", "user1", "john_doe", "alice"]

# Ensure user_data folder exists
USER_DATA_FOLDER = "user_data"
if not os.path.exists(USER_DATA_FOLDER):
    os.makedirs(USER_DATA_FOLDER)

# Generate random transactions for each user
num_transactions = 50  # Adjust as needed

for user in users:
    data = []

    for _ in range(num_transactions):
        trans_id = generate_transaction_id()  # Alphanumeric ID
        date = datetime.now() - timedelta(days=random.randint(1, 60))  # Random date in last 60 days
        description = random.choice(transactions)  # Random transaction
        amount = round(random.uniform(5, 300), 2)  # Random amount ($5 to $300)
        data.append([trans_id, date.strftime("%Y-%m-%d"), description, amount])

    # Convert to DataFrame and save as CSV
    df = pd.DataFrame(data, columns=["Transaction ID", "Date", "Description", "Amount"])
    df.to_csv(f"user_data/{user}_transactions.csv", index=False)

print("✅ Random transactions generated successfully for all users!")
