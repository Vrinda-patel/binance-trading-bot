// =========================================================================
// Frontend Logic for the Trading Bot
// =========================================================================

document.addEventListener("DOMContentLoaded", () => {
    fetchHistory();
    
    // Dynamic styling for the submit button based on SIDE
    const sideSelect = document.getElementById("side");
    const submitBtn = document.getElementById("submitBtn");
    
    sideSelect.addEventListener("change", (e) => {
        if (e.target.value === "SELL") {
            submitBtn.classList.add("sell-mode");
        } else {
            submitBtn.classList.remove("sell-mode");
        }
    });
});

// Toggle the price input field based on ORDER_TYPE
function togglePriceField() {
    const type = document.getElementById("type").value;
    const priceGroup = document.getElementById("priceGroup");
    const priceInput = document.getElementById("price");

    if (type === "LIMIT") {
        priceGroup.style.display = "block";
        priceInput.setAttribute("required", "true");
    } else {
        priceGroup.style.display = "none";
        priceInput.removeAttribute("required");
        priceInput.value = ""; // Clear price if switching back to MARKET
    }
}

// Handle Form Submission
document.getElementById("orderForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const btnText = document.querySelector("#submitBtn span");
    const loader = document.getElementById("submitLoader");
    
    // UI Loading state
    btnText.style.display = "none";
    loader.style.display = "block";
    document.getElementById("submitBtn").disabled = true;

    // Gather data
    const payload = {
        symbol: document.getElementById("symbol").value.toUpperCase(),
        side: document.getElementById("side").value,
        type: document.getElementById("type").value,
        quantity: document.getElementById("quantity").value,
        price: document.getElementById("price").value || null
    };

    try {
        const response = await fetch("/api/order", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (response.ok) {
            showToast(`Success! Order ID: ${result.data.orderId}`, "success");
            fetchHistory(); // Refresh history
        } else {
            showToast(`Error: ${result.error}`, "error");
        }
    } catch (error) {
        showToast("Network error. Could not reach the bot backend.", "error");
    } finally {
        // Reset UI Loading state
        btnText.style.display = "block";
        loader.style.display = "none";
        document.getElementById("submitBtn").disabled = false;
    }
});

// Fetch and display order history
async function fetchHistory() {
    const historyList = document.getElementById("historyList");
    
    try {
        const response = await fetch("/api/history");
        const history = await response.json();

        if (history.length === 0) {
            historyList.innerHTML = '<div class="loading-history">No orders yet.</div>';
            return;
        }

        historyList.innerHTML = ""; // Clear list
        
        history.forEach(order => {
            const date = new Date(order.timestamp).toLocaleString();
            const sideClass = `side-${order.request.side}`;
            
            const item = document.createElement("div");
            item.className = "history-item";
            item.innerHTML = `
                <div class="history-header">
                    <span>${order.request.symbol} <span class="${sideClass}">${order.request.side}</span></span>
                    <span>${order.request.order_type}</span>
                </div>
                <div class="history-details">
                    <span>Qty: ${order.request.quantity}</span>
                    <span>Price: ${order.request.price || "MARKET"}</span>
                </div>
                <div class="history-details" style="margin-top: 4px; color: #8b949e; font-size: 0.75rem;">
                    <span>ID: ${order.response.orderId}</span>
                    <span>${date}</span>
                </div>
            `;
            historyList.appendChild(item);
        });

    } catch (error) {
        historyList.innerHTML = '<div class="loading-history">Failed to load history.</div>';
    }
}

// Toast notification system
let toastTimeout;
function showToast(message, type) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.className = `toast hidden`;
    }, 4000);
}
