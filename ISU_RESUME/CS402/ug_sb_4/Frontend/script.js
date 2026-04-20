document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const templateSelect = document.getElementById("templateSelect");
    const uploadBtn = document.getElementById("uploadBtn");
    const docGrid = document.getElementById("docGrid");
    const status = document.getElementById("status");
    const docxInput = document.getElementById("docxInput");
    const sectionInput = document.getElementById("sectionInput");
    const extractBtn = document.getElementById("extractBtn");
    const extractStatus = document.getElementById("extractStatus");
    const validationSpreadsheetInput = document.getElementById("validationSpreadsheetInput");
    const validationPdfInput = document.getElementById("validationPdfInput");
    const validateBtn = document.getElementById("validateBtn");
    const validationStatus = document.getElementById("validationStatus");

    let documents = [];

    function formatDate(timestamp) {
        const date = new Date(timestamp * 1000);
        return date.toLocaleDateString();
    }

    function renderDocuments() {
        if (!docGrid) return;
        
        documents.sort((a, b) => b.date - a.date);
        
        docGrid.innerHTML = "";

        documents.forEach((doc) => {
            const col = document.createElement("div");
            col.className = "col-md-4";

            col.innerHTML = `
                <div class="card shadow-sm">
                    <div class="card-body">
                        <p class="card-text"> 
                            ${doc.name}
                        </p>
                        <div class="d-flex justify-content-between mt-auto">
                            <div>
                                <button class="btn btn-sm btn-outline-primary me-1">View</button>
                                <button class="btn btn-sm btn-outline-success me-1">Download</button>
                                <button class="btn btn-sm btn-outline-danger">Delete</button>
                            </div>
                            <small class="text-muted"> ${formatDate(doc.date)} </small>
                        </div>
                    </div>
                </div>
            `;

            const [viewBtn, downloadBtn, deleteBtn] = col.querySelectorAll("button");

            viewBtn.addEventListener("click", () => {
                if (doc.pdfName) {
                    window.open(`/download/${encodeURIComponent(doc.pdfName)}`, "_blank");
                } else {
                    alert("Preview not available for this file.");
                }
            });

            downloadBtn.addEventListener("click", () => {
                window.location.href = `/download/${encodeURIComponent(doc.generatedName)}`;
            });

            deleteBtn.addEventListener("click", async () => {
                try {
                    const response = await fetch(`/delete/${encodeURIComponent(doc.generatedName)}`, {
                        method: "DELETE"
                    });
                    const data = await response.json();

                    if (!response.ok) {
                        alert(data.error || "Delete failed.");
                        return;
                    }

                    await loadDocuments();
                } catch (err) {
                    console.error("Error deleting document:", err);
                    alert("Delete failed.");
                }
            });

            docGrid.appendChild(col);
        });
    }

    async function loadDocuments() {
        try {
            const response = await fetch("/documents");
            const data = await response.json();
            documents = data;
            renderDocuments();
        } catch (err) {
            console.error("Error loading documents:", err);
        }
    }

    if (docGrid) {
        loadDocuments();
    }

    if (uploadBtn) {
        uploadBtn.addEventListener("click", async () => {
            const file = fileInput.files[0];
            const template = templateSelect.value;

            if (!file) {
                alert("Please select a spreadsheet first.");
                return;
            }

            const formData = new FormData();
            formData.append("file", file);

            try {
                status.textContent = "Uploading spreadsheet...";
                
                const uploadRes = await fetch("/upload", { method: "POST", body: formData });
                const uploadData = await uploadRes.json();

                if (!uploadRes.ok) {
                    throw new Error(uploadData.error || "Upload failed.");
                }

                status.textContent = "Generating document...";

                const generateRes = await fetch("/generate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        filename: uploadData.filename,
                        template: template
                    })
                });
                const generateData = await generateRes.json();

                if (!generateRes.ok) {
                    throw new Error(generateData.error || "Generation failed.");
                }

                await loadDocuments();

                status.textContent = "Done!";
                setTimeout(() => { status.textContent = ""; }, 3000);

                fileInput.value = "";
            } catch (err) {
                console.error("Error:", err);
                status.textContent = "Failed.";
                alert(err.message || "Upload or generation failed.");
                setTimeout(() => { status.textContent = ""; }, 5000);
            }
        });
    }

    if (extractBtn) {
        extractBtn.addEventListener("click", async () => {
            const file = docxInput.files[0];
            const sectionTitle = sectionInput.value.trim();

            if (!file) {
                alert("Please select a document first.");
                return;
            }

            if (!sectionTitle) {
                alert("Please enter a section title.");
                return;
            }

            const formData = new FormData();
            formData.append("file", file);
            formData.append("sectionTitle", sectionTitle);

            try {
                extractStatus.textContent = "Extracting section...";

                const response = await fetch("/extract-section", {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Section extraction failed.");
                }

                await loadDocuments();

                extractStatus.textContent = "Done!";
                setTimeout(() => { extractStatus.textContent = ""; }, 3000);

                docxInput.value = "";
                sectionInput.value = "";
            } catch (err) {
                console.error("Error:", err);
                alert(err.message || "Section extraction failed.");
                setTimeout(() => { extractStatus.textContent = ""; }, 5000);
            }
        });
    }

    if (validateBtn) {
        validateBtn.addEventListener("click", async () => {
            const spreadsheetFile = validationSpreadsheetInput.files[0];
            const pdfFile = validationPdfInput.files[0];

            if (!spreadsheetFile) {
                alert("Please select a spreadsheet first.");
                return;
            }

            if (!pdfFile) {
                alert("Please select a Streamlyne PDF first.");
                return;
            }

            const formData = new FormData();
            formData.append("spreadsheet", spreadsheetFile);
            formData.append("streamlynePdf", pdfFile);

            try {
                validationStatus.textContent = "Running validation...";

                const response = await fetch("/validate", {
                    method: "POST",
                    body: formData
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.error || "Validation failed.");
                }

                await loadDocuments();

                validationStatus.textContent = "Validation report created.";
                setTimeout(() => { validationStatus.textContent = ""; }, 3000);

                validationSpreadsheetInput.value = "";
                validationPdfInput.value = "";
            } catch (err) {
                console.error("Error:", err);
                alert(err.message || "Validation failed.");
                validationStatus.textContent = "Failed.";
                setTimeout(() => { validationStatus.textContent = ""; }, 5000);
            }
        });
    }
});