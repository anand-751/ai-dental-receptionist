"""
FastAPI routes for Stripe success/cancel redirects.
Place at: backend/api/payment_pages.py

Key fix: payment-success page sends window.opener.postMessage("payment_success")
so the original tab knows payment is done WITHOUT relying on window.focus events
(which don't work reliably on Android Chrome).
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["payment-pages"])


PAYMENT_SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Payment Successful</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      min-height: 100vh;
      display: flex; align-items: center; justify-content: center;
      background: linear-gradient(135deg, #0f172a, #1e293b);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      color: white;
    }
    .card {
      text-align: center; padding: 48px 40px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(74,222,128,0.3);
      border-radius: 20px; max-width: 420px; width: 90%;
    }
    .icon { font-size: 64px; margin-bottom: 16px; }
    h1 { font-size: 28px; color: #4ade80; margin-bottom: 12px; }
    p { color: #94a3b8; line-height: 1.6; margin-bottom: 8px; font-size: 15px; }
    .highlight { color: #e2e8f0; font-weight: 600; }
    button {
      margin-top: 24px; padding: 12px 32px;
      background: #16a34a; color: white; border: none;
      border-radius: 999px; font-size: 15px; font-weight: 600;
      cursor: pointer; transition: background 0.2s;
    }
    button:hover { background: #15803d; }
    .timer { margin-top: 12px; font-size: 12px; color: #64748b; }
    .status { margin-top: 8px; font-size: 12px; color: #4ade80; min-height: 16px; }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">✅</div>
    <h1>Payment Successful!</h1>
    <p class="highlight">Your ₹500 booking fee has been received.</p>
    <p>Return to the previous tab — your appointment will confirm automatically.</p>
    <p class="status" id="status"></p>
    <button onclick="goBack()">← Go Back to App</button>
    <p class="timer" id="timer">Returning automatically in 5 seconds...</p>
  </div>

  <script>
    var notified = false;

    function notifyOpener() {
      // Method 1: postMessage to opener (works when opened via window.open)
      try {
        if (window.opener && !window.opener.closed) {
          window.opener.postMessage("payment_success", "*");
          document.getElementById("status").textContent = "✓ App notified";
          notified = true;
        }
      } catch(e) {}

      // Method 2: BroadcastChannel (works same-origin across tabs on Android)
      try {
        var bc = new BroadcastChannel("payment_channel");
        bc.postMessage("payment_success");
        bc.close();
        notified = true;
      } catch(e) {}

      // Method 3: localStorage event (fallback for same-origin)
      try {
        localStorage.setItem("payment_status", "success_" + Date.now());
      } catch(e) {}
    }

    function goBack() {
      notifyOpener();
      // Try to go back in history first (most reliable on mobile)
      if (window.history.length > 1) {
        window.history.back();
      }
      // Try to focus opener
      try {
        if (window.opener && !window.opener.closed) {
          window.opener.focus();
        }
      } catch(e) {}
      // Try to close this tab
      setTimeout(function() {
        try { window.close(); } catch(e) {}
      }, 300);
    }

    // Notify as soon as page loads
    notifyOpener();

    // Auto countdown
    var count = 5;
    var timerEl = document.getElementById("timer");
    var interval = setInterval(function() {
      count--;
      if (count <= 0) {
        clearInterval(interval);
        timerEl.textContent = "Returning now...";
        goBack();
      } else {
        timerEl.textContent = "Returning automatically in " + count + " seconds...";
      }
    }, 1000);
  </script>
</body>
</html>
"""

PAYMENT_CANCEL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Payment Cancelled</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      min-height: 100vh;
      display: flex; align-items: center; justify-content: center;
      background: linear-gradient(135deg, #0f172a, #1e293b);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      color: white;
    }
    .card {
      text-align: center; padding: 48px 40px;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(248,113,113,0.3);
      border-radius: 20px; max-width: 420px; width: 90%;
    }
    .icon { font-size: 64px; margin-bottom: 16px; }
    h1 { font-size: 28px; color: #f87171; margin-bottom: 12px; }
    p { color: #94a3b8; line-height: 1.6; margin-bottom: 8px; font-size: 15px; }
    .highlight { color: #e2e8f0; font-weight: 600; }
    button {
      margin-top: 24px; padding: 12px 32px;
      background: #475569; color: white; border: none;
      border-radius: 999px; font-size: 15px; font-weight: 600;
      cursor: pointer; transition: background 0.2s;
    }
    button:hover { background: #334155; }
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">❌</div>
    <h1>Payment Cancelled</h1>
    <p class="highlight">Your slot is still reserved for now.</p>
    <p>Return to the previous tab and click <strong>"Pay ₹500 Now"</strong> to try again.</p>
    <button onclick="goBack()">← Go Back to App</button>
  </div>
  <script>
    function goBack() {
      try {
        var bc = new BroadcastChannel("payment_channel");
        bc.postMessage("payment_cancelled");
        bc.close();
      } catch(e) {}
      try { localStorage.setItem("payment_status", "cancelled_" + Date.now()); } catch(e) {}
      if (window.history.length > 1) { window.history.back(); }
      try {
        if (window.opener && !window.opener.closed) { window.opener.focus(); }
      } catch(e) {}
      setTimeout(function() { try { window.close(); } catch(e) {} }, 300);
    }
    // Auto-notify on load
    try {
      var bc = new BroadcastChannel("payment_channel");
      bc.postMessage("payment_cancelled");
      bc.close();
    } catch(e) {}
    try { localStorage.setItem("payment_status", "cancelled_" + Date.now()); } catch(e) {}
  </script>
</body>
</html>
"""


@router.get("/payment-success", response_class=HTMLResponse)
async def payment_success():
    return HTMLResponse(content=PAYMENT_SUCCESS_HTML)


@router.get("/payment-cancel", response_class=HTMLResponse)
async def payment_cancel():
    return HTMLResponse(content=PAYMENT_CANCEL_HTML)