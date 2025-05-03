// frontend/static/js/app.js

async function getRagResponse(query) {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query, top_k: 5 }),
  });
  const data = await response.json();
  return data.response;
}

document
  .getElementById("queryForm")
  .addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = document.getElementById("queryInput").value;
    const response = await getRagResponse(query);
    document.getElementById("responseOutput").innerText = response;
  });
