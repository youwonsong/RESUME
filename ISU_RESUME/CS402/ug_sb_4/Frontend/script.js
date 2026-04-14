document.addEventListener("DOMContentLoaded", () => {
    const fileInput = document.getElementById("fileInput");
    const templateSelect = document.getElementById("templateSelect");
    const uploadBtn = document.getElementById("uploadBtn");
    const docGrid = document.getElementById("docGrid");
    const status = document.getElementById("status");

    let documents = [];

    function formatDate(timestamp) {
        const date = new Date(timestamp * 1000);
        return date.toLocaleDateString();
    }

    function renderDocuments() {
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
                                
                                <button class="btn btn-sm btn-outline-success me-1">Download</button>
                                <button class="btn btn-sm btn-outline-danger">Delete</button>
                            </div>
                            <small class="text-muted"> ${formatDate(doc.date)} </small>
                        </div>
                    </div>
                </div>
            `;

            // View button temporarily removed: <button class="btn btn-sm btn-outline-primary me-1">View</button>

            const [downloadBtn, deleteBtn] = col.querySelectorAll("button");

            // viewBtn.addEventListener("click", () => {
            //     window.open(`/download/${encodeURIComponent(doc.generatedName)}`, "_blank");
            // });

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

    loadDocuments();

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
            console.log(uploadData.message);

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
            console.log(generateData.message);

            await loadDocuments();

            status.textContent = "Done!";
            setTimeout(() => { status.textContent = ""; }, 3000);

            fileInput.value = "";
        } catch (err) {
            console.error("Error:", err);
            alert("Upload or generation failed.");
            setTimeout(() => { status.textContent = ""; }, 5000);
        }
    });
});