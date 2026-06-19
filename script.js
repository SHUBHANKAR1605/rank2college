document.getElementById('predictorForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    const tbody = document.getElementById('tableBody');
    
    const selectedCategory = document.getElementById('category').value;
    const crlValue = document.getElementById('crlRank').value;
    const typedCatRank = document.getElementById('catRank').value;

    // Strict Clean-up: If user selects OPEN, override category rank entries
    let finalCatRank = crlValue; 
    if (selectedCategory !== "OPEN" && typedCatRank !== "") {
        finalCatRank = typedCatRank;
    }
    
    const payload = {
        examType: document.getElementById('examType').value,
        crlRank: crlValue,
        category: selectedCategory,
        catRank: finalCatRank,
        gender: document.getElementById('gender').value,
        quota: document.getElementById('quota').value,
        branchKeyword: document.getElementById('branchKeyword').value
    };

    submitBtn.textContent = "Querying Live DB...";
    submitBtn.style.opacity = "0.7";
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center;">Fetching +/- 10% Window...</td></tr>`;

    try {
        // 👇 THIS IS YOUR LIVE RENDER SERVER LINK 👇
        const response = await fetch('https://rank2college-8rku.onrender.com/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error("Backend Error");
        
        const realDatabaseRows = await response.json();
        renderDatabaseTable(realDatabaseRows);
        
    } catch (error) {
        // Updated error message for cloud deployment
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #dc2626; font-weight: 500;">Could not reach cloud server. Please try again in a moment.</td></tr>`;
    } finally {
        submitBtn.textContent = "Analyze Prospects";
        submitBtn.style.opacity = "1";
    }
});

function renderDatabaseTable(data) {
    const tbody = document.getElementById('tableBody');
    
    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center;">No matches found matching these parameters in the dataset.</td></tr>`;
        return;
    }

    // Added title attributes so full text shows on mouse hover
    tbody.innerHTML = data.map(row => `
        <tr>
            <td title="${row.institute}" style="font-weight: 500;">${row.institute}</td>
            <td title="${row.branch}" style="color: var(--text-muted); font-size: 0.875rem;">${row.branch}</td>
            <td>${row.quota}</td>
            <td>${row.seat}</td>
            <td style="font-family: monospace; font-weight: 600;">${row.rank}</td>
            <td><span class="badge ${row.chance.toLowerCase()}">${row.chance}</span></td>
        </tr>
    `).join('');
}

// --- Modal Control Logic ---
function openModal(id) {
    document.getElementById(id).style.display = "block";
}

function closeModal(id) {
    document.getElementById(id).style.display = "none";
}

// Close modal if user clicks outside the white box
window.onclick = function(event) {
    if (event.target.className === 'modal') {
        event.target.style.display = "none";
    }
}