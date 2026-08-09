const form = document.getElementById("convert-form");
const urlInput = document.getElementById("url-input");
const convertBtn = document.getElementById("convert-btn");
const statusEl = document.getElementById("status");
const errorEl = document.getElementById("error");
const previewEl = document.getElementById("preview");
const previewTitleEl = document.getElementById("preview-title");
const previewPlayer = document.getElementById("preview-player");
const downloadBtn = document.getElementById("download-btn");

let currentObjectUrl = null;
let currentFilename = "audio.mp3";

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

function resetPreview() {
  previewEl.hidden = true;
  previewPlayer.pause();
  previewPlayer.removeAttribute("src");
  if (currentObjectUrl) {
    URL.revokeObjectURL(currentObjectUrl);
    currentObjectUrl = null;
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  setError("");
  resetPreview();

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

    if (response.status === 401) {
      window.location.href = "/login";
      return;
    }

    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      setError(data.error || "Something went wrong during conversion.");
      return;
    }

    const blob = await response.blob();
    currentFilename = filenameFromContentDisposition(
      response.headers.get("Content-Disposition"),
      "audio.mp3"
    );
    currentObjectUrl = URL.createObjectURL(blob);

    previewTitleEl.textContent = currentFilename;
    previewPlayer.src = currentObjectUrl;
    previewEl.hidden = false;

    setStatus("Done — preview it below, then download when you're ready.");
  } catch {
    setError("Couldn't reach the server. Check your connection and try again.");
  } finally {
    convertBtn.disabled = false;
  }
});

downloadBtn.addEventListener("click", () => {
  if (!currentObjectUrl) return;

  const link = document.createElement("a");
  link.href = currentObjectUrl;
  link.download = currentFilename;
  document.body.appendChild(link);
  link.click();
  link.remove();
});
