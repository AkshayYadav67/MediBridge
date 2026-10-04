// Simple polling chat for telemedicine consultations (no websockets required).
(function () {
  const box = document.getElementById("chat");
  if (!box) return;
  const { messagesUrl, sendUrl, csrf } = box.dataset;
  let last = 0;
  const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  async function poll() {
    try {
      const r = await fetch(`${messagesUrl}?after=${last}`, { credentials: "same-origin" });
      const data = await r.json();
      data.messages.forEach((m) => {
        last = Math.max(last, m.id);
        const d = document.createElement("div");
        d.className = "bubble" + (m.mine ? " mine" : "");
        d.innerHTML = `<small>${esc(m.sender)} · ${m.at}</small>${esc(m.body)}`;
        box.appendChild(d);
      });
      if (data.messages.length) box.scrollTop = box.scrollHeight;
    } catch (e) { /* retry on next tick */ }
  }
  document.getElementById("chat-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("chat-input");
    if (!input.value.trim()) return;
    await fetch(sendUrl, { method: "POST", credentials: "same-origin",
      headers: { "X-CSRFToken": csrf, "Content-Type": "application/x-www-form-urlencoded" },
      body: "body=" + encodeURIComponent(input.value) });
    input.value = "";
    poll();
  });
  poll();
  setInterval(poll, 3000);
})();
