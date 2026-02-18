// Table Management Utilities

class DataTable {
    constructor(tableSelector, options = {}) {
        this.table = document.querySelector(tableSelector);
        this.currentPage = 1;
        this.itemsPerPage = options.itemsPerPage || 10;
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.data = [];
        
        if (this.table) {
            this.init();
        }
    }

    init() {
        this.extractData();
        this.makeHeadersSortable();
        this.addPagination();
    }

    extractData() {
        const tbody = this.table.querySelector('tbody');
        if (!tbody) return;
        
        this.data = Array.from(tbody.querySelectorAll('tr')).map(row => ({
            element: row,
            cells: Array.from(row.querySelectorAll('td')).map(cell => cell.textContent.trim())
        }));
    }

    makeHeadersSortable() {
        const headers = this.table.querySelectorAll('thead th');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.style.userSelect = 'none';
            header.style.padding = '8px';
            
            header.addEventListener('click', () => {
                this.sortTable(index, header);
            });
            
            // Add hover effect
            header.addEventListener('mouseover', () => {
                header.style.background = '#f3f4f6';
            });
            header.addEventListener('mouseout', () => {
                header.style.background = '';
            });
        });
    }

    sortTable(columnIndex, headerElement) {
        // Toggle sort direction
        if (this.sortColumn === columnIndex) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortDirection = 'asc';
        }
        
        this.sortColumn = columnIndex;
        
        // Update header styling
        document.querySelectorAll('thead th').forEach(h => {
            h.style.fontWeight = 'normal';
            h.innerHTML = h.innerHTML.replace(' ▲', '').replace(' ▼', '');
        });
        
        let headerText = headerElement.innerHTML;
        headerText += this.sortDirection === 'asc' ? ' ▲' : ' ▼';
        headerElement.innerHTML = headerText;
        headerElement.style.fontWeight = 'bold';
        
        // Sort data
        this.data.sort((a, b) => {
            let aVal = a.cells[columnIndex] || '';
            let bVal = b.cells[columnIndex] || '';
            
            // Try numeric sort
            const aNum = parseFloat(aVal);
            const bNum = parseFloat(bVal);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return this.sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
            }
            
            // String sort
            return this.sortDirection === 'asc' 
                ? aVal.localeCompare(bVal) 
                : bVal.localeCompare(aVal);
        });
        
        this.currentPage = 1;
        this.renderTable();
    }

    renderTable() {
        const tbody = this.table.querySelector('tbody');
        tbody.innerHTML = '';
        
        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        const pageData = this.data.slice(start, end);
        
        pageData.forEach(item => {
            tbody.appendChild(item.element);
        });
        
        this.updatePagination();
    }

    addPagination() {
        const totalPages = Math.ceil(this.data.length / this.itemsPerPage);
        
        if (totalPages <= 1) return;
        
        const paginationDiv = document.createElement('div');
        paginationDiv.className = 'pagination-controls';
        paginationDiv.style.cssText = `
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            margin-top: 24px;
            padding: 16px;
            background: #f9fafb;
            border-radius: 8px;
        `;
        
        this.paginationDiv = paginationDiv;
        this.table.parentElement.insertAdjacentElement('afterend', paginationDiv);
        
        this.renderTable();
    }

    updatePagination() {
        const totalPages = Math.ceil(this.data.length / this.itemsPerPage);
        const paginationDiv = this.paginationDiv;
        
        if (!paginationDiv || totalPages <= 1) return;
        
        paginationDiv.innerHTML = '';
        
        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '← Previous';
        prevBtn.style.cssText = `
            padding: 8px 16px;
            border: 1px solid #d1d5db;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s ease;
        `;
        prevBtn.disabled = this.currentPage === 1;
        prevBtn.onclick = () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.renderTable();
            }
        };
        paginationDiv.appendChild(prevBtn);
        
        // Page indicators
        const pageSpan = document.createElement('span');
        pageSpan.textContent = `Page ${this.currentPage} of ${totalPages}`;
        pageSpan.style.cssText = `
            padding: 8px 16px;
            font-weight: 500;
            color: #6b7280;
        `;
        paginationDiv.appendChild(pageSpan);
        
        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.textContent = 'Next →';
        nextBtn.style.cssText = `
            padding: 8px 16px;
            border: 1px solid #d1d5db;
            background: white;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.2s ease;
        `;
        nextBtn.disabled = this.currentPage === totalPages;
        nextBtn.onclick = () => {
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.renderTable();
            }
        };
        paginationDiv.appendChild(nextBtn);
    }

    search(query) {
        query = query.toLowerCase();
        this.currentPage = 1;
        
        const tbody = this.table.querySelector('tbody');
        tbody.innerHTML = '';
        
        const filtered = this.data.filter(item => 
            item.cells.some(cell => cell.toLowerCase().includes(query))
        );
        
        const start = (this.currentPage - 1) * this.itemsPerPage;
        const end = start + this.itemsPerPage;
        
        filtered.slice(start, end).forEach(item => {
            tbody.appendChild(item.element);
        });
    }
}

// Delete handler with confirmation
function deleteItem(url, itemName = 'this item') {
    showConfirmation(`Are you sure you want to delete ${itemName}? This action cannot be undone.`, () => {
        window.location.href = url;
    });
}

// Export to CSV
function exportTableToCSV(tableSelector, filename = 'export.csv') {
    const table = document.querySelector(tableSelector);
    let csv = [];
    
    // Get headers
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent);
    csv.push(headers.join(','));
    
    // Get rows
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const cells = Array.from(row.querySelectorAll('td')).map(td => {
            let text = td.textContent.trim();
            // Escape quotes and wrap in quotes if contains comma
            if (text.includes(',')) {
                text = `"${text.replace(/"/g, '""')}"`;
            }
            return text;
        });
        csv.push(cells.join(','));
    });
    
    // Download
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    
    showToast('Table exported to CSV successfully!', 'success');
}

// Print table
function printTable(tableSelector, title = 'Report') {
    const table = document.querySelector(tableSelector);
    const printWindow = window.open('', '', 'height=600,width=900');
    printWindow.document.write('<html><head><title>' + title + '</title>');
    printWindow.document.write(`<style>
        body { font-family: Arial, sans-serif; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #2563eb; color: white; }
        tr:nth-child(even) { background-color: #f9fafb; }
        h1 { color: #1f2937; }
    </style>`);
    printWindow.document.write('</head><body>');
    printWindow.document.write('<h1>' + title + '</h1>');
    printWindow.document.write('<p>Generated on: ' + new Date().toLocaleString() + '</p>');
    printWindow.document.write(table.outerHTML);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}
