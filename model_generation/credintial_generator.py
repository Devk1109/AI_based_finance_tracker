import pandas as pd

# Sample user data (username, password)
users_data = [
    {"username": "admin", "password": "password123"},
    {"username": "dev", "password": "102303351"},
    {"username": "jayasheel", "password": "102303354"},
    {"username": "gagan", "password": "102303349"},
]

# Convert to DataFrame and save to CSV
df = pd.DataFrame(users_data)
df.to_csv("users.csv", index=False)

print("✅ users.csv file created successfully!")
