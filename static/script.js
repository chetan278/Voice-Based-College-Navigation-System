async function navigate() {
  const start = document.getElementById("start").value;
  const end = document.getElementById("end").value;

  const resultDiv = document.getElementById("result");
  resultDiv.innerText = "🔄 Calculating route...";

  const response = await fetch("/navigate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ start, end })
  });

  const data = await response.json();
  if (data.error) {
    resultDiv.innerText = "❌ " + data.error;
  } else {
    resultDiv.innerText = "✅ Path: " + data.path.join(" → ");
    document.getElementById("mapFrame").src = data.map;
  }
}
