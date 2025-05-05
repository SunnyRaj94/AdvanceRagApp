document.getElementById("chat-form").addEventListener("submit", async function (e) {
  e.preventDefault();

  const query = document.getElementById("query").value;
  const source = document.getElementById("source_type").value;

  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query: query,
        source: source,
        top_k: 5,
      }),
    });

    const data = await response.json();
    document.getElementById("chat-response").innerText = data.response || data.error;
  } catch (error) {
    document.getElementById("chat-response").innerText = "Error: " + error.message;
  }
});
