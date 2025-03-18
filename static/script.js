document.addEventListener("DOMContentLoaded", function () {
    console.log("📢 DOM fully loaded and parsed!");

    // Attach event listener using event delegation
    document.addEventListener("click", function (event) {
        if (event.target.id === "add-transaction-btn") {
            console.log("✅ Add Transaction Button Clicked!");
            submitTransaction();
        } else if (event.target.id === "logout-btn") {
            console.log("🚪 Logout button clicked!");
            logout();
        }
    });

    // Login Button Listener
    let loginBtn = document.getElementById("login-btn");
    if (loginBtn) {
        loginBtn.addEventListener("click", loginUser);
    }

    // Filter Transactions on Search
    let searchInput = document.getElementById("search");
    if (searchInput) {
        searchInput.addEventListener("input", filterTransactions);
    }
});

// Function to handle user login
function loginUser() {
    let username = document.getElementById("username").value.trim();
    let password = document.getElementById("password").value.trim();
    let errorMsg = document.getElementById("login-error");

    if (!username || !password) {
        errorMsg.innerText = "⚠️ Please enter both username and password.";
        return;
    }

    fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ "username": username, "password": password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.href = "/dashboard";  // Redirect to dashboard
        } else {
            errorMsg.innerText = "❌ Invalid username or password.";
        }
    })
    .catch(error => {
        errorMsg.innerText = "❌ Error logging in.";
        console.error("Login Error:", error);
    });
}

// Function to submit a new transaction
function submitTransaction() {
    let transactionId = document.getElementById("entry-transaction-id").value.trim();
    let description = document.getElementById("entry-description").value.trim();
    let amount = document.getElementById("entry-amount").value.trim();
    let date = document.getElementById("entry-date").value.trim();

    if (!transactionId || !description || !amount || !date) {
        alert("⚠️ Please fill in all fields.");
        return;
    }

    let transactionData = {
        transaction_id: transactionId,
        description: description,
        amount: parseFloat(amount),
        date: date
    };

    fetch('/add_transaction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(transactionData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log("✅ Transaction added successfully!");

            // ✅ Clear input fields
            document.getElementById("entry-transaction-id").value = "";
            document.getElementById("entry-description").value = "";
            document.getElementById("entry-amount").value = "";
            document.getElementById("entry-date").value = "";

            // ✅ Update Transactions Table
            updateTransactionTable(data.transactions);

            // ✅ Update Charts
            updateCharts(data.pie_chart, data.bar_chart, data.category_comparison_chart);

            // ✅ First Refresh (Immediate)
            location.reload();

            // ✅ Second Refresh (After 1 second delay)
            setTimeout(() => {
                location.reload();
            }, 1000);

        } else {
            alert("❌ Failed to add transaction. Try again.");
        }
    })
    .catch(error => {
        console.error("❌ Error:", error);
        alert("❌ Server error while adding transaction.");
    });
}

// Function to update the transaction table
function updateTransactionTable(transactions) {
    let tableBody = document.getElementById("transactions-table");

    if (!tableBody) {
        console.error("❌ Error: transactions-table element not found!");
        return;
    }

    tableBody.innerHTML = ""; // Clear old data

    transactions.forEach(tx => {
        let row = `<tr>
            <td>${tx["Transaction ID"]}</td>
            <td>${tx["Date"]}</td>
            <td>${tx["Description"]}</td>
            <td>$${tx["Amount"].toFixed(2)}</td>
            <td>${tx["Category"]}</td>
        </tr>`;
        tableBody.innerHTML += row;
    });
}

// Function to update charts dynamically
function updateCharts(pieChart, barChart, categoryChart) {
    let pie = document.getElementById("pie-chart-container");
    let bar = document.getElementById("bar-chart-container");
    let category = document.getElementById("category-comparison-container");

    if (pie) pie.innerHTML = pieChart;
    else console.warn("⚠️ Warning: 'pie-chart-container' not found!");

    if (bar) bar.innerHTML = barChart;
    else console.warn("⚠️ Warning: 'bar-chart-container' not found!");

    if (category) category.innerHTML = categoryChart;
    else console.warn("⚠️ Warning: 'category-comparison-container' not found!");
}


// Function to filter transactions based on search input
function filterTransactions() {
    let input = document.getElementById("search").value.toLowerCase();
    let rows = document.querySelectorAll("#transactions-table tbody tr");

    rows.forEach(row => {
        let description = row.cells[1].innerText.toLowerCase();
        row.style.display = description.includes(input) ? "" : "none";
    });
}

// Function to logout
function logout() {
    fetch("/logout", { method: "POST" })
    .then(() => {
        console.log("🚪 Logged out successfully!");
        window.location.href = "/home";
    })
    .catch(error => console.error("Logout Error:", error));
}
