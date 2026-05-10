const form = document.getElementById("match-form");
const resultBox = document.getElementById("result");

form.addEventListener("submit", async (e) => {
    e.preventDefault();

    resultBox.innerHTML = "Analyzing...";

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

        resultBox.innerHTML = `
            <div class="result-card">
                <h2>Analysis Result</h2>

                <p><strong>File:</strong> ${data.filename}</p>

                <p>
                    <strong>Match Score:</strong>
                    ${(data.match_score * 100).toFixed(0)}%
                </p>

                <p><strong>Score Explanation:</strong> ${data.score_explanation}</p>

                <h3>Matched Skills</h3>
                <ul>
                    ${renderList(data.matched_skills, "No matched skills found.")}
                </ul>

                <h3>Missing Skills</h3>
                <ul>
                    ${renderList(data.missing_skills, "No missing skills found.")}
                </ul>

                <h3>Feedback</h3>
                <ul>
                    ${renderList(data.feedback, "No major feedback needed.")}
                </ul>
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