const form = document.getElementById("match-form");
const resultBox = document.getElementById("result");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    resultBox.innerHTML = `<div class="loading">Analyzing resume...</div>`;

    const fileInput = document.getElementById("resume");
    const jobDescription = document.getElementById("job-description").value;

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);
    formData.append("job_description", jobDescription);

    try {
        const response = await fetch("/match", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok) {
            resultBox.innerHTML = `
                <div class="error">
                    <strong>Error:</strong> ${result.detail || "Something went wrong."}
                </div>
            `;
            return;
        }

        const data = result.data;
        const scorePercent = Math.round(data.match_score * 100);
        const semanticPercent = Math.round((data.semantic_score || 0) * 100);

        resultBox.innerHTML = `
            <div class="result-card">
                <div class="result-header">
                    <div>
                        <h2>Analysis Result</h2>
                        <p class="file-name">${data.filename}</p>
                    </div>
                    <div class="score-badge">${scorePercent}%</div>
                </div>

                <div class="score-bar">
                    <div class="score-fill" style="width: ${scorePercent}%"></div>
                </div>

                <p class="score-text">${data.score_explanation}</p>

                <p><strong>Semantic Score:</strong> ${semanticPercent}%</p>

                <p><strong>Semantic Source:</strong> ${data.semantic_source}</p>

                <div class="result-grid">
                    <div class="result-section">
                        <h3>Matched Skills</h3>
                        <ul>
                            ${renderList(data.matched_skills, "No matched skills found.")}
                        </ul>
                    </div>

                    <div class="result-section">
                        <h3>Missing Skills</h3>
                        <ul>
                            ${renderList(data.missing_skills, "No missing skills found.")}
                        </ul>
                    </div>
                </div>

                <div class="result-section feedback-section">
                    <h3>Feedback</h3>
                    <ul>
                        ${renderList(data.feedback, "No major feedback needed.")}
                    </ul>
                </div>
            </div>
        `;

    } catch (error) {
        resultBox.innerHTML = `
            <div class="error">
                <strong>Error:</strong> Failed to connect to the server.
            </div>
        `;
    }
});


function renderList(items, emptyMessage) {
    if (!items || items.length === 0) {
        return `<li>${emptyMessage}</li>`;
    }

    return items.map(item => `<li>${item}</li>`).join("");
}
