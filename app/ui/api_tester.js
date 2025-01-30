async function executeCode() {
    const code = document.getElementById("code").value;
    const language = document.getElementById("language").value;

    // Show executing message in the results area
    document.getElementById("result-output").textContent = "Executing...";

    const response = await fetch("/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language })
    });

    const result = await response.json();
    if (!result.job_id) {
        document.getElementById("result-output").textContent = "Error: Could not retrieve job ID.";
        return;
    }

    // Poll for result
    await pollResult(result.job_id);

    // Fetch history after execution completes
    await fetchHistory();
}

async function pollResult(jobId) {
    while (true) {
        const response = await fetch(`/result/${jobId}`);
        const result = await response.json();

        if (result.status !== "queued") {
            document.getElementById("result-output").textContent = JSON.stringify(result, null, 2);
            break;
        }

        await new Promise(resolve => setTimeout(resolve, 1000)); // Wait 1 second before polling again
    }
}

async function fetchHistory() {
    const response = await fetch("/history");
    const history = await response.json();

    const historyTable = document.getElementById("history-output");
    historyTable.innerHTML = ""; // Clear previous entries

    history.forEach(entry => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${entry.language}</td>
            <td><pre>${escapeHtml(entry.code)}</pre></td>
            <td><pre>${escapeHtml(entry.output)}</pre></td>
            <td>${new Date(entry.timestamp * 1000).toLocaleString()}</td>
        `;

        historyTable.appendChild(row);
    });
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Fetch history on page load
window.onload = fetchHistory;
