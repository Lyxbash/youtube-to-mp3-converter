const form = document.getElementById("convert-form");
const urlInput = document.getElementById("url-input");
const convertBtn = document.getElementById("convert-btn");
const statusEl = document.getElementById("status");
const errorEl = document.getElementById("error");

function setStatus(message) {
  statusEl.textContent = message;
  statusEl.hidden = !message;
}

function setError(message) {
  errorEl.textContent = message;
  errorEl.hidden = !message;
}

function filenameFromContentDisposition(header, fallback) {
  if (!header) return fallback;
  const match = header.match(/filename="?([^"]+)"?/);
  return match ? match[1] : fallback;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError("");

  const url = urlInput.value.trim();
  try {
    new URL(url);
  } catch {
    setError("Please enter a valid YouTube video URL.");
    return;
  }

  convertBtn.disabled = true;
  setStatus("Converting… this can take a little while for longer videos.");

  try {
    const response = await fetch("/api/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      setError(data.error || "Something went wrong during conversion.");
      return;
    }

    const blob = await response.blob();
    const filename = filenameFromContentDisposition(
      response.headers.get("Content-Disposition"),
      "audio.mp3"
    );

    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = objectUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(objectUrl);

    setStatus("Done — your download should start automatically.");
  } catch {
    setError("Couldn't reach the server. Check your connection and try again.");
  } finally {
    convertBtn.disabled = false;
  }
});
