let currentPage = 'dashboard';
let charts = {};
let activeData = []; // Store raw active records for the current listing
const apiUrls = window.API_URLS;

// Helper to create HTML tables with Actions (Edit/Delete)
function generateTable(headers, rows, type) {
    if (!rows || rows.length === 0) {
        return `<div class="p-4 text-center text-muted">No records found.</div>`;
    }
    
    // Check if we need action column
    const hasActions = ['products', 'sales', 'expenses'].includes(type);
    const tableHeaders = hasActions ? [...headers, 'Actions'] : headers;
    
    let html = `<div style="overflow:auto"><table><thead><tr>`;
    tableHeaders.forEach(h => {
        html += `<th>${h}</th>`;
    });
    html += `</tr></thead><tbody>`;
    
    rows.forEach((row, rowIndex) => {
        html += `<tr>`;
        row.forEach((cell, cellIndex) => {
            // Hide the expense ID column from display (its last column in expenses row data)
            if (type === 'expenses' && cellIndex === 4) return;
            
            // Format status badges
            if (cellIndex === row.length - 1 && ['Active', 'Completed'].includes(cell)) {
                html += `<td><span class="status">${cell}</span></td>`;
            } else if (cellIndex === row.length - 1 && cell === 'Pending') {
                html += `<td><span class="status pending">${cell}</span></td>`;
            } else if (cellIndex === row.length - 1 && ['Inactive', 'Cancelled'].includes(cell)) {
                html += `<td><span class="status inactive">${cell}</span></td>`;
            } else {
                html += `<td>${cell}</td>`;
            }
        });
        
        // Add Action columns
        if (hasActions) {
            let id = row[0]; // defaults to first cell (e.g. PR-001 or ORD-012)
            if (type === 'expenses') {
                id = row[4]; // expense id is the hidden 5th element
            } else if (type === 'products' || type === 'sales') {
                // Extract digits from PR-001 or ORD-1002
                const match = id.match(/\d+/);
                id = match ? parseInt(match[0], 10) : id;
            }
            
            html += `<td>
                <div class="actions">
                    <button class="edit" onclick="handleEdit('${type}', ${rowIndex}, '${id}')" title="Edit"><i class="bi bi-pencil-square"></i></button>
                    <button class="delete" onclick="handleDelete('${type}', '${id}')" title="Delete"><i class="bi bi-trash"></i></button>
                </div>
            </td>`;
        }
        
        html += `</tr>`;
    });
    
    html += `</tbody></table></div>`;
    return html;
}

// Render Dashboard View
function renderDashboard(data) {
    const kpis = data.kpis;
    const lists = data.lists;
    const totalRevenue = Number(kpis.total_revenue || 0);
const totalProfit = Number(kpis.total_profit || 0);
const totalExpenses = Number(kpis.total_expenses || 0);
const totalCustomers = Number(kpis.total_customers || 0);

const revenueGrowth = Number(kpis.revenue_growth || 0);
const profitGrowth = Number(kpis.profit_growth || 0);
const expenseGrowth = Number(kpis.expense_growth || 0);
const customerGrowth = Number(kpis.customer_growth || 0);
    
    return `<div class="content">
        <!-- Business Summary Banner -->
        <div class="alert alert-info py-2 px-3 mb-3 d-flex align-items-center" style="border-radius:10px; font-size:12px;">
            <span class="me-2">💡</span>
            <strong>Summary:</strong> &nbsp; <span id="performance-banner">${data.performance_summary}</span>
        </div>

        <div class="kpis">
            ${renderKpiCard('Total Revenue', `$${totalRevenue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, `${revenueGrowth >= 0 ? '+' : ''}${revenueGrowth}%`, '💵', 'green', revenueGrowth < 0)}
            ${renderKpiCard('Total Profit', `$${totalProfit.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, `${profitGrowth >= 0 ? '+' : ''}${profitGrowth}%`, '◉', 'purple', profitGrowth < 0)}
            ${renderKpiCard('Total Expenses', `$${totalExpenses.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`, `${expenseGrowth >= 0 ? '+' : ''}${expenseGrowth}%`, '▣', 'orange', expenseGrowth > 0)}
            ${renderKpiCard('Total Customers', totalCustomers.toString(), `${customerGrowth >= 0 ? '+' : ''}${customerGrowth}%`, '♟', 'blue', customerGrowth < 0)}
    </div>
        
        <div class="charts">
            <div class="card">
                <div class="cardhead">Revenue & Profit Trend ($)</div>
                <div class="chartbox"><canvas id="rev-chart"></canvas></div>
            </div>
            <div class="card">
                <div class="cardhead">Revenue by Category</div>
                <div class="chartbox"><canvas id="cat-chart"></canvas></div>
            </div>
        </div>
        
        <div class="bottom">
            <div class="card tablecard">
                <div class="cardhead">Top Selling Products</div>
${generateTable(['Item Type', 'Units Sold', 'Revenue', 'Profit'], lists.top_items, 'top_items')}            </div>
            <div class="card tablecard">
                <div class="cardhead">Recent Sales</div>
${generateTable(['Order ID', 'Country', 'Item Type', 'Date', 'Channel', 'Revenue', 'Profit'], lists.recent_orders, 'recent_orders')}            </div>
        </div>
    </div>`;
}

function renderKpiCard(label, val, growth, icon, colorClass, isDown) {
    return `<div class="card kpi">
        <div>
            <div class="label">${label}</div>
            <div class="value">${val}</div>
            <div class="${isDown ? 'down' : 'up'}">${growth} <span style="color:#9aa5b5">vs last month</span></div>
        </div>
        <div class="ico ${colorClass}">${icon}</div>
    </div>`;
}

// Render Listing Page (Customers, Products, Sales, Expenses)
function renderListing(type, data) {
    const config = {
        customers: ['Regional Distribution', ['Region', 'Number of Records']],
        products: ['Products', ['ID', 'Product', 'Category', 'Price', 'Stock', 'Revenue']],
        sales: ['Sales', ['Order ID', 'Customer', 'Date', 'Amount', 'Status']],
        expenses: ['Expenses', ['Date', 'Category', 'Description', 'Amount']]
    }[type];
    
    return `<div class="content">
        <div class="toolbar">
            <div>
                <div class="page-title">${config[0]}</div>
                <small style="color:#9aa5b5">Dashboard / ${config[0]}</small>
            </div>
            <button onclick="handleCreate('${type}')">＋ Add ${type === 'sales' ? 'Sale' : type === 'expenses' ? 'Expense' : type.slice(0, -1)}</button>
        </div>
        <div class="card">${generateTable(config[1], data, type)}</div>
    </div>`;
}

// Render Reports View
function renderReports() {
    return `<div class="content">
        <div class="toolbar">
            <div>
                <div class="page-title">Reports & Analytics</div>
                <small style="color:#9aa5b5">Dashboard / Reports</small>
            </div>
            <button onclick="exportReportCSV()" style="background:#16a34a;"><i class="bi bi-file-earmark-excel me-1"></i> Export CSV</button>
        </div>
        
        <div class="card mb-3">
            <div class="cardhead">Filter Report Period</div>
            <div class="row align-items-end g-3 py-2">
                <div class="col-md-4 form-group">
                    <label>START DATE</label>
                    <input type="date" id="report-start-date" required>
                </div>
                <div class="col-md-4 form-group">
                    <label>END DATE</label>
                    <input type="date" id="report-end-date" required>
                </div>
                <div class="col-md-4">
                    <button onclick="loadFilteredReport()" class="w-100" style="height: 38px; border:0; background:var(--blue); color:#fff; font-weight:600; border-radius:8px;">Apply Filters</button>
                </div>
            </div>
        </div>

        <div class="card" id="report-results" style="display:none;">
            <div class="cardhead">Performance Summary Report</div>
            <div class="kpis mt-2" id="report-kpis"></div>
            <hr style="border-color:var(--border);">
            <div class="chartbox mt-3"><canvas id="report-chart"></canvas></div>
        </div>
    </div>`;
}

// Render Profile View
function renderProfile() {
    return `<div class="content">
        <div class="toolbar">
            <div>
                <div class="page-title">My Profile</div>
                <small style="color:#9aa5b5">Dashboard / Profile</small>
            </div>
        </div>
        <div class="card" style="max-width: 500px;">
            <div class="cardhead">Update Account Settings</div>
            <div id="profile-success" class="alert alert-success py-2" style="display:none; font-size:12px;"></div>
            <div id="profile-error" class="alert alert-danger py-2" style="display:none; font-size:12px;"></div>
            <form id="profile-form">
                <div class="form-group mb-3">
                    <label>USERNAME</label>
                    <input type="text" id="prof-username" readonly style="background:#f1f5f9; cursor:not-allowed;">
                </div>
                <div class="form-group mb-3">
                    <label>EMAIL ADDRESS</label>
                    <input type="email" id="prof-email" required placeholder="Enter email">
                </div>
                <div class="form-group mb-4">
                    <label>NEW PASSWORD (LEAVE BLANK TO KEEP UNCHANGED)</label>
                    <input type="password" id="prof-password" placeholder="Enter new password">
                </div>
                <button type="submit" class="w-100" style="height: 38px; border:0; background:var(--blue); color:#fff; font-weight:600; border-radius:8px;">Save Settings</button>
            </form>
        </div>
    </div>`;
}

// Render Settings View
function renderSettings() {
    return `<div class="content">
        <div class="toolbar">
            <div>
                <div class="page-title">System Settings</div>
                <small style="color:#9aa5b5">Dashboard / Settings</small>
            </div>
        </div>
        <div class="card" style="max-width: 600px;">
            <div class="cardhead">Application Context & Details</div>
            <table class="table mt-3" style="border:0;">
                <tbody>
                    <tr>
                        <td style="font-weight:700; width:150px;">Project Title</td>
                        <td>Business Performance KPI Dashboard</td>
                    </tr>
                    <tr>
                        <td style="font-weight:700;">Academic Code</td>
                        <td>BCA 5th Semester Minor Project</td>
                    </tr>
                    <tr>
                        <td style="font-weight:700;">Technology Stack</td>
                        <td>Flask / Python 3 / MySQL / Chart.js / Bootstrap 5</td>
                    </tr>
                    <tr>
                        <td style="font-weight:700;">Database Name</td>
                        <td>business_kpi_db</td>
                    </tr>
                    <tr>
                        <td style="font-weight:700;">Authentication</td>
                        <td>Session-based with bcrypt password hashing</td>
                    </tr>
                    <tr>
                        <td style="font-weight:700;">Status</td>
                        <td><span class="status">Fully Operational</span></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>`;
}

// Fetch and render views
async function navigate(page) {
    currentPage = page;
    document.querySelectorAll('nav button[data-page]').forEach(b => b.classList.toggle('active', b.dataset.page === page));
    document.getElementById('title').textContent = page.charAt(0).toUpperCase() + page.slice(1);
    document.getElementById('crumb').textContent = page.charAt(0).toUpperCase() + page.slice(1);
    
    // Toggle Search box visibility for listings
    const searchBox = document.getElementById('table-search');
    if (['customers', 'products', 'sales', 'expenses'].includes(page)) {
        searchBox.style.display = 'block';
        searchBox.value = '';
    } else {
        searchBox.style.display = 'none';
    }

    const appSection = document.getElementById('app');
    appSection.innerHTML = `<div class="p-5 text-center"><div class="spinner-border text-primary" role="status"></div><div class="mt-2 text-muted">Loading data...</div></div>`;
    
    try {
        if (page === 'dashboard') {
    try {
        const res = await fetch(apiUrls.dashboard);

        console.log("Dashboard response status:", res.status);

        const resData = await res.json();

        console.log("Dashboard API data:", resData);

        if (resData.success) {
            appSection.innerHTML = renderDashboard(resData);

            console.log("Dashboard HTML rendered successfully");

            drawDashboardCharts(resData.charts);

            console.log("Dashboard charts rendered successfully");
        } else {
            appSection.innerHTML =
                `<div class="alert alert-danger m-3">${resData.error}</div>`;
        }

    } catch (err) {
        console.error("DASHBOARD ERROR:", err);

        appSection.innerHTML =
            `<div class="alert alert-danger m-3">
                Dashboard error: ${err.message}
             </div>`;
    }
} else if (['customers', 'products', 'sales', 'expenses'].includes(page)) {
            const res = await fetch(apiUrls[page]);
            const resData = await res.json();
            if (resData.success) {
                activeData = resData.data;
                appSection.innerHTML = renderListing(page, activeData);
            } else {
                appSection.innerHTML = `<div class="alert alert-danger m-3">${resData.error}</div>`;
            }
        } else if (page === 'reports') {
            appSection.innerHTML = renderReports();
            // Default dates
            const today = new Date();
            const lastMonth = new Date(today.getFullYear(), today.getMonth() - 1, today.getDate());
            document.getElementById('report-start-date').value = lastMonth.toISOString().split('T')[0];
            document.getElementById('report-end-date').value = today.toISOString().split('T')[0];
            loadFilteredReport();
        } else if (page === 'profile') {
            appSection.innerHTML = renderProfile();
            loadProfileForm();
        } else if (page === 'settings') {
            appSection.innerHTML = renderSettings();
        }
    } catch (err) {
        appSection.innerHTML = `<div class="alert alert-danger m-3">Connection error: Could not reach the server API.</div>`;
    }
}

// Chart.js Helpers
function drawDashboardCharts(chartData) {
    // Destroy previous chart instances to avoid overlap issues
    charts.rev?.destroy();
    charts.cat?.destroy();
    
    const revCtx = document.getElementById('rev-chart');
    const catCtx = document.getElementById('cat-chart');
    
    if (revCtx) {
        charts.rev = new Chart(revCtx, {
            type: 'line',
            data: {
                labels: chartData.trends.labels,
                datasets: [
                    {
                        label: 'Revenue',
                        data: chartData.trends.revenue,
                        borderColor: '#2563eb',
                        backgroundColor: '#2563eb22',
                        fill: true,
                        tension: 0.35
                    },
                    {
                        label: 'Profit',
                        data: chartData.trends.profit,
                        borderColor: '#7c3aed',
                        backgroundColor: '#7c3aed11',
                        fill: true,
                        tension: 0.35
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { boxWidth: 12, font: { size: 10 } } } },
                scales: {
                    y: { ticks: { callback: v => '$' + v.toLocaleString() } },
                    x: { grid: { display: false } }
                }
            }
        });
    }
    
    if (catCtx) {
        charts.cat = new Chart(catCtx, {
            type: 'doughnut',
            data: {
                labels: chartData.categories.labels,
                datasets: [{
                    data: chartData.categories.values,
                    backgroundColor: ['#2563eb', '#16a34a', '#f59e0b', '#7c3aed', '#ec4899'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { position: 'bottom', labels: { boxWidth: 10, padding: 15, font: { size: 9 } } }
                }
            }
        });
    }
}

// Load and draw reports bar chart
async function loadFilteredReport() {
    const start = document.getElementById('report-start-date').value;
    const end = document.getElementById('report-end-date').value;
    const resBox = document.getElementById('report-results');
    
    try {
        const res = await fetch(`${apiUrls.reports}?start_date=${start}&end_date=${end}`);
        const data = await res.json();
        if (data.success) {
            resBox.style.display = 'block';
            
            // Set dynamic KPI statistics
            const kpis = data.kpis;
            document.getElementById('report-kpis').innerHTML = `
                ${renderKpiCard('Selected Revenue', `$${kpis.total_revenue.toLocaleString()}`, '', '💵', 'green', false)}
                ${renderKpiCard('Selected Profit', `$${kpis.total_profit.toLocaleString()}`, '', '◉', 'purple', false)}
                ${renderKpiCard('Selected Expenses', `$${kpis.total_expenses.toLocaleString()}`, '', '▣', 'orange', false)}
                ${renderKpiCard('Active Customers', kpis.total_customers.toString(), '', '♟', 'blue', false)}
            `;
            
            // Draw chart
            charts.report?.destroy();
            charts.report = new Chart(document.getElementById('report-chart'), {
                type: 'bar',
                data: {
                    labels: data.chart.labels,
                    datasets: [{
                        data: data.chart.values,
                        backgroundColor: '#3b82f6',
                        borderRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { ticks: { callback: v => '$' + v.toLocaleString() } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }
    } catch (err) {
        alert("Failed to load report data.");
    }
}

function exportReportCSV() {
    const start = document.getElementById('report-start-date').value;
    const end = document.getElementById('report-end-date').value;
    window.location.href = `/api/reports/export?start_date=${start}&end_date=${end}`;
}

// Profile Settings Form Handling
async function loadProfileForm() {
    try {
        const res = await fetch(apiUrls.profile);
        const data = await res.json();
        if (data.user) {
            document.getElementById('prof-username').value = data.user.username;
            document.getElementById('prof-email').value = data.user.email;
        }
    } catch (err) {
        console.error("Profile load failed.");
    }
    
    document.getElementById('profile-form').onsubmit = async (e) => {
        e.preventDefault();
        const success = document.getElementById('profile-success');
        const errBox = document.getElementById('profile-error');
        success.style.display = 'none';
        errBox.style.display = 'none';
        
        const email = document.getElementById('prof-email').value;
        const password = document.getElementById('prof-password').value;
        
        try {
            const res = await fetch(apiUrls.profile, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await res.json();
            if (data.success) {
                success.textContent = data.message;
                success.style.display = 'block';
                document.getElementById('prof-password').value = '';
            } else {
                errBox.textContent = data.error;
                errBox.style.display = 'block';
            }
        } catch (err) {
            errBox.textContent = "Could not connect to server.";
            errBox.style.display = 'block';
        }
    };
}

// Search dynamic tables
document.getElementById('table-search').oninput = async (e) => {
    const val = e.target.value.trim();
    try {
        const res = await fetch(`${apiUrls[currentPage]}?search=${encodeURIComponent(val)}`);
        const resData = await res.json();
        if (resData.success) {
            activeData = resData.data;
            document.getElementById('app').innerHTML = renderListing(currentPage, activeData);
        }
    } catch (err) {
        console.error("Search fetch failed.");
    }
};

// --- CRUD Operations ---
const modal = {
    backdrop: document.getElementById('modal-backdrop'),
    title: document.getElementById('modal-title'),
    fields: document.getElementById('modal-form-fields'),
    error: document.getElementById('modal-error'),
    submitBtn: document.getElementById('modal-submit-btn')
};

// Close Modal
function closeModal() {
    modal.backdrop.style.display = 'none';
}

document.getElementById('modal-close-btn').onclick = closeModal;
document.getElementById('modal-cancel-btn').onclick = closeModal;

// Create Record
async function handleCreate(type) {
    modal.title.textContent = `Add New ${type === 'sales' ? 'Sale' : type === 'expenses' ? 'Expense' : type.slice(0, -1)}`;
    modal.error.style.display = 'none';
    modal.fields.innerHTML = '<div class="text-center py-3">Loading form elements...</div>';
    modal.backdrop.style.display = 'grid';
    
    // Inject form HTML dynamically
    const fieldsHtml = await generateFormFields(type);
    modal.fields.innerHTML = fieldsHtml;
    
    modal.submitBtn.onclick = () => saveRecord(type, 'create');
}

// Edit Record
async function handleEdit(type, rowIndex, id) {
    modal.title.textContent = `Edit ${type === 'sales' ? 'Sale' : type === 'expenses' ? 'Expense' : type.slice(0, -1)}`;
    modal.error.style.display = 'none';
    modal.fields.innerHTML = '<div class="text-center py-3">Loading form elements...</div>';
    modal.backdrop.style.display = 'grid';
    
    // Get original row details
    const row = activeData[rowIndex];
    const fieldsHtml = await generateFormFields(type, row);
    modal.fields.innerHTML = fieldsHtml;
    
    modal.submitBtn.onclick = () => saveRecord(type, 'edit', id);
}

// Delete Record
async function handleDelete(type, id) {
    if (confirm("Are you sure you want to delete this record? This action cannot be undone.")) {
        try {
            const res = await fetch(`/api/${type}/${id}`, { method: 'DELETE' });
            const data = await res.json();
            if (data.success) {
                navigate(currentPage);
            } else {
                alert(data.error || "Failed to delete record.");
            }
        } catch (err) {
            alert("Database communication error.");
        }
    }
}

// Generate HTML inputs based on module type
async function generateFormFields(type, rowData = null) {
    if (type === 'customers') {
        const valName = rowData ? rowData[1] : '';
        const valEmail = rowData ? rowData[2] : '';
        const valPhone = rowData ? rowData[3] : ''; // wait: city is index 3 in customers route response? Let's check
        // Customers route response: [r['id'], r['name'], r['email'], r['city'], r['status']]
        // Index mapping: 0=id, 1=name, 2=email, 3=city, 4=status. (phone was omitted in listing response to keep it clean)
        // Since phone was not in the row list, let's load it from row data if available or just check
        const valCity = rowData ? rowData[3] : '';
        const valStatus = rowData ? rowData[4] : 'Active';
        
        return `
            <div class="form-group mb-3">
                <label>CUSTOMER NAME *</label>
                <input type="text" id="cust-name" required value="${valName}">
            </div>
            <div class="form-group mb-3">
                <label>EMAIL ADDRESS *</label>
                <input type="email" id="cust-email" required value="${valEmail}">
            </div>
            <div class="form-group mb-3">
                <label>CITY</label>
                <input type="text" id="cust-city" value="${valCity}">
            </div>
            <div class="form-group mb-3">
                <label>STATUS</label>
                <select id="cust-status">
                    <option value="Active" ${valStatus === 'Active' ? 'selected' : ''}>Active</option>
                    <option value="Inactive" ${valStatus === 'Inactive' ? 'selected' : ''}>Inactive</option>
                </select>
            </div>
        `;
    }
    
    if (type === 'products') {
        const valName = rowData ? rowData[1] : '';
        const valCategory = rowData ? rowData[2] : 'Electronics';
        const valPrice = rowData ? parseFloat(rowData[3].replace('$', '')) : '';
        const valStock = rowData ? parseInt(rowData[4]) : 0;
        
        return `
            <div class="form-group mb-3">
                <label>PRODUCT NAME *</label>
                <input type="text" id="prod-name" required value="${valName}">
            </div>
            <div class="form-group mb-3">
                <label>CATEGORY *</label>
                <select id="prod-category">
                    <option value="Electronics" ${valCategory === 'Electronics' ? 'selected' : ''}>Electronics</option>
                    <option value="Clothing" ${valCategory === 'Clothing' ? 'selected' : ''}>Clothing</option>
                    <option value="Home Appliances" ${valCategory === 'Home Appliances' ? 'selected' : ''}>Home Appliances</option>
                    <option value="Accessories" ${valCategory === 'Accessories' ? 'selected' : ''}>Accessories</option>
                    <option value="Others" ${valCategory === 'Others' ? 'selected' : ''}>Others</option>
                </select>
            </div>
            <div class="form-group mb-3">
                <label>PRICE ($) *</label>
                <input type="number" step="0.01" id="prod-price" required value="${valPrice}">
            </div>
            <div class="form-group mb-3">
                <label>STOCK LEVEL *</label>
                <input type="number" id="prod-stock" required value="${valStock}">
            </div>
        `;
    }
    
    if (type === 'sales') {
        const valCustName = rowData ? rowData[1] : '';
        const valQty = rowData ? parseInt(rowData[3]) : 1; // wait: [id, customer_name, date, total, status]
        // Sales route: ORD-0001, John Smith, 18 Jul 2026, $1250, Completed.
        // We will fetch customer list and product list from database to render select dropdowns!
        let customerOptions = '';
        let productOptions = '';
        
        try {
            const [custRes, prodRes] = await Promise.all([
                fetch('/api/sales-customers'),
                fetch('/api/products')
            ]);
            const cData = await custRes.json();
            const pData = await prodRes.json();
            
          if (cData.success && Array.isArray(cData.data)) {
    cData.data.forEach(c => {
        const cId = c[0];
        const cName = c[1];
        const isSelected = rowData && cName === valCustName ? 'selected' : '';
        customerOptions += `<option value="${cId}" ${isSelected}>${cName} (ID: ${cId})</option>`;
    });
}
            
            pData.data.forEach(p => {
                // p: [f"PR-{r['id']}", name, category, price, stock, revenue]
                const matchId = p[0].match(/\d+/);
                const pId = matchId ? parseInt(matchId[0]) : p[0];
                const pName = p[1];
                productOptions += `<option value="${pId}">${pName} (${p[3]}, Stock: ${p[4]})</option>`;
            });
        } catch (err) {
            console.error("Failed to load list options.");
        }
        
        const valDate = rowData ? parseFormattedDate(rowData[2]) : new Date().toISOString().split('T')[0];
        const valStatus = rowData ? rowData[4] : 'Completed';
        
        return `
            <div class="form-group mb-3">
                <label>CUSTOMER *</label>
                <select id="sale-cust-id" required>${customerOptions}</select>
            </div>
            <div class="form-group mb-3">
                <label>PRODUCT *</label>
                <select id="sale-prod-id" required>${productOptions}</select>
            </div>
            <div class="form-group mb-3">
                <label>QUANTITY *</label>
                <input type="number" id="sale-qty" min="1" required value="${rowData ? '' : 1}">
            </div>
            <div class="form-group mb-3">
                <label>SALE DATE *</label>
                <input type="date" id="sale-date" required value="${valDate}">
            </div>
            <div class="form-group mb-3">
                <label>STATUS</label>
                <select id="sale-status">
                    <option value="Completed" ${valStatus === 'Completed' ? 'selected' : ''}>Completed</option>
                    <option value="Pending" ${valStatus === 'Pending' ? 'selected' : ''}>Pending</option>
                    <option value="Cancelled" ${valStatus === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
                </select>
            </div>
        `;
    }
    
    if (type === 'expenses') {
        // rowData: ['18 Jul 2026', 'Rent', 'Office Rent', '$2500', '1']
        const valDate = rowData ? parseFormattedDate(rowData[0]) : new Date().toISOString().split('T')[0];
        const valCategory = rowData ? rowData[1] : 'Rent';
        const valDesc = rowData ? rowData[2] : '';
        const valAmt = rowData ? parseFloat(rowData[3].replace('$', '').replace(',', '')) : '';
        
        return `
            <div class="form-group mb-3">
                <label>EXPENSE DATE *</label>
                <input type="date" id="exp-date" required value="${valDate}">
            </div>
            <div class="form-group mb-3">
                <label>CATEGORY *</label>
                <select id="exp-category">
                    <option value="Rent" ${valCategory === 'Rent' ? 'selected' : ''}>Rent</option>
                    <option value="Utilities" ${valCategory === 'Utilities' ? 'selected' : ''}>Utilities</option>
                    <option value="Salaries" ${valCategory === 'Salaries' ? 'selected' : ''}>Salaries</option>
                    <option value="Marketing" ${valCategory === 'Marketing' ? 'selected' : ''}>Marketing</option>
                    <option value="Others" ${valCategory === 'Others' ? 'selected' : ''}>Others</option>
                </select>
            </div>
            <div class="form-group mb-3">
                <label>DESCRIPTION</label>
                <input type="text" id="exp-desc" value="${valDesc}">
            </div>
            <div class="form-group mb-3">
                <label>AMOUNT ($) *</label>
                <input type="number" step="0.01" id="exp-amt" required value="${valAmt}">
            </div>
        `;
    }
}

// Convert "18 Jul 2026" to "2026-07-18" for input type="date"
function parseFormattedDate(str) {
    if (!str) return '';
    const dateObj = new Date(str);
    if (isNaN(dateObj)) return '';
    return dateObj.toISOString().split('T')[0];
}

// Collect inputs and submit
async function saveRecord(type, action, id = null) {
    modal.error.style.display = 'none';
    let payload = {};
    let url = `/api/${type}`;
    let method = 'POST';
    
    if (action === 'edit' && id) {
        url = `/api/${type}/${id}`;
        method = 'PUT';
    }
    
    if (type === 'customers') {
        payload = {
            name: document.getElementById('cust-name').value.trim(),
            email: document.getElementById('cust-email').value.trim(),
            city: document.getElementById('cust-city').value.trim(),
            status: document.getElementById('cust-status').value
        };
        if (!payload.name || !payload.email) {
            showFormError("Name and Email are required.");
            return;
        }
    } else if (type === 'products') {
        payload = {
            name: document.getElementById('prod-name').value.trim(),
            category: document.getElementById('prod-category').value,
            price: parseFloat(document.getElementById('prod-price').value),
            stock: parseInt(document.getElementById('prod-stock').value)
        };
        if (!payload.name || isNaN(payload.price) || isNaN(payload.stock)) {
            showFormError("Please fill all required numeric values correctly.");
            return;
        }
    } else if (type === 'sales') {
        payload = {
            customer_id: document.getElementById('sale-cust-id').value,
            product_id: document.getElementById('sale-prod-id').value,
            quantity: parseInt(document.getElementById('sale-qty').value),
            sale_date: document.getElementById('sale-date').value,
            status: document.getElementById('sale-status').value
        };
        if (!payload.customer_id || !payload.product_id || isNaN(payload.quantity) || !payload.sale_date) {
            showFormError("All fields are required.");
            return;
        }
    } else if (type === 'expenses') {
        payload = {
            date: document.getElementById('exp-date').value,
            category: document.getElementById('exp-category').value,
            description: document.getElementById('exp-desc').value.trim(),
            amount: parseFloat(document.getElementById('exp-amt').value)
        };
        if (!payload.date || isNaN(payload.amount)) {
            showFormError("Date and Amount are required.");
            return;
        }
    }
    
    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (data.success) {
            closeModal();
            navigate(currentPage);
        } else {
            showFormError(data.error || "An error occurred.");
        }
    } catch (err) {
        showFormError("Communication failed with server.");
    }
}

function showFormError(msg) {
    modal.error.textContent = msg;
    modal.error.style.display = 'block';
}

// Theme toggler placeholder
document.getElementById('theme-toggle').onclick = () => {
    document.body.classList.toggle('dark-mode');
    alert("Dark mode feature is configured! Style rules can be customized in css.");
};

// Handle Sidebar toggle on small screens
document.getElementById('menu').onclick = () => {
    document.getElementById('sidebar').classList.toggle('open');
};

// Logout click
document.getElementById('logout-btn').onclick = async () => {
    if (confirm("Are you sure you want to logout?")) {
        window.location.href = apiUrls.logout;
    }
};

// Initialize
document.querySelectorAll('nav button[data-page]').forEach(b => {
    b.onclick = () => {
        navigate(b.dataset.page);
        document.getElementById('sidebar').classList.remove('open');
    };
});

// Navigate to Dashboard on initial load
navigate('dashboard');
