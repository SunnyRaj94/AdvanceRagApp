document.getElementById("chat-form").addEventListener("submit", async function (e) {
  e.preventDefault();

  const query = document.getElementById("query").value;
  const source = document.getElementById("source_type").value;

  const selectedContext = JSON.parse(sessionStorage.getItem("selectedContext") || "null");
  const contextType = sessionStorage.getItem("contextType");

  const requestBody = {
    query: query,
    source: source,
    top_k: 5,
    file_id: contextType === "file" ? selectedContext?.id : null,
    link_id: contextType === "link" ? selectedContext?.id : null,
  };

  showLoading();
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify(requestBody),
    });

    const raw = await response.text();
    console.log("Raw response:", raw);
    const data = JSON.parse(raw);

    if (data.response) {
      document.getElementById("chat-response").innerText = data.response;
    } else {
      document.getElementById("chat-response").innerText = "No response available.";
    }
  } catch (error) {
    console.error("Chat error:", error);
    document.getElementById("chat-response").innerText = "Error: " + error.message;
  } finally {
    hideLoading();
  }
});

async function fetchContext(endpoint, listElementId, type) {
  try {
    const res = await fetch(endpoint);
    const data = await res.json();

    const listEl = document.getElementById(listElementId);
    listEl.innerHTML = "";

    const items = data[Object.keys(data)[0]];

    items.forEach(item => {
      const li = document.createElement("li");

      const name = item.filename || item.source || item.file_path || "Unnamed";
      li.textContent = name;
      li.title = JSON.stringify(item);

      // Handle selection
      li.onclick = () => {
        sessionStorage.setItem("selectedContext", JSON.stringify(item));
        sessionStorage.setItem("contextType", type);
        [...listEl.children].forEach(el => el.classList.remove("selected"));
        li.classList.add("selected");
        console.log("Selected context:", item);
      };

      // Add delete button
      const deleteBtn = document.createElement("button");
      deleteBtn.textContent = "🗑️";
      deleteBtn.style.marginLeft = "10px";
      deleteBtn.onclick = async (e) => {
        e.stopPropagation(); // prevent item selection
        await deleteContext(type, item.id || item.file_id || item.link_id);
      };

      li.appendChild(deleteBtn);
      listEl.appendChild(li);
    });
  } catch (err) {
    console.error("Error loading context:", err);
  }
}

async function deleteContext(type, id) {
  if (!confirm(`Are you sure you want to delete this ${type}?`)) return;

  const endpoint = type === "file" ? `/delete/file/${id}` : `/delete/link/${id}`;

  showLoading();
  try {
    const res = await fetch(endpoint, { method: "DELETE" });
    const data = await res.json();
    if (data.success) {
      alert(`${type} deleted successfully.`);
      refreshContext();
    } else {
      alert(`Failed to delete ${type}: ${JSON.stringify(data)}`);
    }
  } catch (err) {
    console.error("Delete error:", err);
    alert("Error deleting item: " + err.message);
  } finally {
    hideLoading();
  }
}

async function ingestSource() {
  const type = document.getElementById("source-type").value;
  const formData = new FormData();
  let endpoint = "";

  if (type === "file") {
    const file = document.getElementById("file-input").files[0];
    if (!file) {
      alert("Please select a file");
      return;
    }
    formData.append("file", file);
    endpoint = "/ingest/file";
  } else if (type === "link") {
    const link = document.getElementById("link-input").value;
    if (!link) {
      alert("Please enter a link");
      return;
    }
    formData.append("url", link);
    endpoint = "/ingest/link";
  }

  showLoading();
  try {
    const res = await fetch(endpoint, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    if ((type === "file" && data.file_id) || (type === "link" && data.link_id)) {
      alert(`${type === "file" ? "File" : "Link"} ingested successfully!`);

      const contextType = type === "file" ? "file" : "link";
      const newItem = type === "file"
        ? { id: data.file_id, filename: document.getElementById("file-input").files[0].name }
        : { id: data.link_id, source: document.getElementById("link-input").value };

      sessionStorage.setItem("selectedContext", JSON.stringify(newItem));
      sessionStorage.setItem("contextType", contextType);
      document.getElementById("source_type").value = contextType === "link" ? "url" : "file";

      refreshContext(); // refresh and rehighlight
    } else {
      alert("Failed to ingest: " + JSON.stringify(data));
    }
  } catch (err) {
    alert("Error ingesting: " + err.message);
  } finally {
    hideLoading();
  }
}

function toggleInputFields() {
  const type = document.getElementById("source-type").value;
  document.getElementById("file-input-group").style.display = type === "file" ? "block" : "none";
  document.getElementById("link-input-group").style.display = type === "link" ? "block" : "none";
}

function refreshContext() {
  fetchContext("/context/files", "file-list", "file");
  fetchContext("/context/links", "link-list", "link");
}

window.addEventListener("DOMContentLoaded", () => {
  toggleInputFields();
  refreshContext();
});

function showLoading() {
  document.getElementById("loading-spinner").style.display = "flex";
}

function hideLoading() {
  document.getElementById("loading-spinner").style.display = "none";
}
