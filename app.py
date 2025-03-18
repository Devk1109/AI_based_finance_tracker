from flask import Flask, request, jsonify, render_template, session, redirect, url_for
import pandas as pd
import os
import joblib
import plotly.express as px
import random
import string

# Load ML Model & Vectorizer
model = joblib.load("expense_classifier.pkl")
vectorizer = joblib.load("vectorizer.pkl")

# Initialize Flask App
app = Flask(__name__)
app.secret_key = "supersecretkey"

USER_DATA_FOLDER = "user_data"
USER_CREDENTIALS_FILE = "users.csv"

# Ensure User Data Folder Exists
os.makedirs(USER_DATA_FOLDER, exist_ok=True)

# Load users from CSV
def load_users():
    try:
        if not os.path.exists(USER_CREDENTIALS_FILE):
            return {}
        df = pd.read_csv(USER_CREDENTIALS_FILE)
        return dict(zip(df["username"], df["password"]))
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

# Load transactions for a user
def load_transactions(username):
    filepath = os.path.join(USER_DATA_FOLDER, f"{username}_transactions.csv")

    if os.path.exists(filepath):
        transactions = pd.read_csv(filepath)

        # Ensure required columns exist
        required_columns = ["Transaction ID", "Date", "Description", "Amount", "Category"]
        for col in required_columns:
            if col not in transactions.columns:
                transactions[col] = None  # Add missing columns

        # Categorize transactions if Category column is empty
        if transactions["Category"].isnull().any():
            descriptions = transactions["Description"].astype(str).tolist()
            transformed_desc = vectorizer.transform(descriptions)
            transactions["Category"] = model.predict(transformed_desc)
            transactions.to_csv(filepath, index=False)  # Save back to CSV

        return transactions

    return pd.DataFrame(columns=["Transaction ID", "Date", "Description", "Amount", "Category"])

# Identify Unusual Expenses
def identify_unusual_expenses(transactions):
    """ Marks transactions as 'Unusual' if they exceed 2x the category average. """
    if transactions.empty:
        return transactions

    # Convert Amount to float
    transactions["Amount"] = pd.to_numeric(transactions["Amount"], errors="coerce")

    # Calculate average spending per category
    category_avg = transactions.groupby("Category")["Amount"].mean().to_dict()

    # Debugging: Print category averages
    print("Category Averages:", category_avg)

    # Mark unusual transactions
    def is_unusual(row):
        avg = category_avg.get(row["Category"], 0)
        return "Yes" if row["Amount"] > 2 * avg else "No"

    transactions["Unusual"] = transactions.apply(is_unusual, axis=1)

    # Debugging: Check if any transactions are marked unusual
    print("Unusual Transactions:", transactions[transactions["Unusual"] == "Yes"])

    return transactions

# Generate Pie Chart for spending categories
def generate_spending_pie_chart(username):
    transactions = load_transactions(username)

    if transactions.empty or "Category" not in transactions.columns:
        return "<p>No transactions available.</p>"

    category_sums = transactions.groupby("Category")["Amount"].sum().reset_index()

    fig = px.pie(category_sums, names="Category", values="Amount", title="")
    return fig.to_html(full_html=False)

# Generate Bar Chart for spending trends over time
def generate_spending_bar_chart(username):
    transactions = load_transactions(username)

    if transactions.empty:
        return "<p>No transactions available.</p>"

    transactions["Date"] = pd.to_datetime(transactions["Date"], errors="coerce")
    transactions = transactions.dropna(subset=["Date"])  # Remove invalid dates
    transactions["Month"] = transactions["Date"].dt.strftime("%Y-%m")

    monthly_spending = transactions.groupby("Month")["Amount"].sum().reset_index()
    fig = px.bar(monthly_spending, x="Month", y="Amount", title="")

    return fig.to_html(full_html=False)

# Generate Monthly Spending Comparison by Category
def generate_category_monthly_comparison(username):
    transactions = load_transactions(username)

    if transactions.empty:
        return "<p>No transactions available.</p>"

    transactions["Date"] = pd.to_datetime(transactions["Date"], errors="coerce")
    transactions = transactions.dropna(subset=["Date"])  # Remove invalid dates
    transactions["Month"] = transactions["Date"].dt.strftime("%Y-%m")

    category_monthly_spending = transactions.groupby(["Month", "Category"])["Amount"].sum().reset_index()

    fig = px.bar(
        category_monthly_spending,
        x="Month",
        y="Amount",
        color="Category",
        title="",
        barmode="group"
    )
    return fig.to_html(full_html=False)

# Route: Intro Page
@app.route('/')
def intro():
    return render_template("intro.html")

# Route: Home (Login Page)
@app.route('/home')
def home():
    return render_template("home.html")

# Route: Dashboard
@app.route('/dashboard')
def dashboard():
    if "username" not in session:
        return redirect(url_for("home"))

    username = session["username"]
    transactions = load_transactions(username)

    # Mark unusual expenses
    transactions = identify_unusual_expenses(transactions)

    # ✅ Ensure charts are regenerated on every request
    pie_chart = generate_spending_pie_chart(username)
    bar_chart = generate_spending_bar_chart(username)
    category_comparison_chart = generate_category_monthly_comparison(username)

    return render_template(
        "dashboard.html",
        username=username,
        transactions=transactions.to_dict(orient="records"),
        pie_chart=pie_chart,
        bar_chart=bar_chart,
        category_comparison_chart=category_comparison_chart
    )

# API: Login Authentication
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get("username")
        password = data.get("password")

        users = load_users()

        if username in users and users[username] == password:
            session["username"] = username  # Store session
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "message": "Invalid username or password"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# API: Logout
@app.route('/logout', methods=['POST'])
def logout():
    session.pop("username", None)  # Remove user session
    return jsonify({"success": True}), 200

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.json
        transaction_id = data.get("transaction_id", "").strip()
        description = data.get("description", "").strip()
        amount = float(data.get("amount", 0))
        date = data.get("date", "").strip()

        if not transaction_id or not description or amount <= 0 or not date:
            return jsonify({"error": "Missing or invalid fields"}), 400

        category = predict_category(description)
        user_file = os.path.join(USER_DATA_FOLDER, f"{session['username']}_transactions.csv")

        # Append transaction to CSV
        new_entry = pd.DataFrame([[transaction_id, date, description, amount, category]],
                                 columns=["Transaction ID", "Date", "Description", "Amount", "Category"])

        if os.path.exists(user_file):
            df = pd.read_csv(user_file)
            df = pd.concat([df, new_entry], ignore_index=True)
        else:
            df = new_entry

        df.to_csv(user_file, index=False)

        # ✅ Generate updated charts
        pie_chart = generate_spending_pie_chart(session['username'])
        bar_chart = generate_spending_bar_chart(session['username'])
        category_comparison_chart = generate_category_monthly_comparison(session['username'])

        return jsonify({
            "success": True,
            "transactions": df.to_dict(orient='records'),
            "pie_chart": pie_chart,
            "bar_chart": bar_chart,
            "category_comparison_chart": category_comparison_chart
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Define predict_category function
def predict_category(description):
    """ Predicts category using ML model """
    transformed_desc = vectorizer.transform([description])
    return model.predict(transformed_desc)[0]

# Run the Flask App
if __name__ == '__main__':
    app.run(debug=True)
