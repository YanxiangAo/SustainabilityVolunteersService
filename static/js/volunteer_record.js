/**
 * volunteer_record.js - Volunteer Record Page Script
 * Handles functionality for volunteer record page:
 * - Filtering records by year and category
 * - Exporting records (all or filtered)
 * - Updating summary statistics
 */

// Get records data from page
function getRecordsData() {
    const container = document.getElementById('volunteer-records-container') || document.body;
    const recordsDataJson = container.dataset.recordsData;
    if (recordsDataJson) {
        try {
            return JSON.parse(recordsDataJson);
        } catch (e) {
            console.error('Failed to parse records data:', e);
            return [];
        }
    }
    return [];
}

// Store original records data for filtering
let allRecords = [];

// Filter records by year and category
function filterRecords() {
    const yearFilter = document.getElementById('year-filter').value;
    const categoryFilter = document.getElementById('category-filter').value;
    const tbody = document.getElementById('records-tbody');

    if (!tbody) return;

    let filtered = allRecords;

    if (yearFilter) {
        filtered = filtered.filter(item => {
            if (!item.record.completed_at) return false;
            const year = item.record.completed_at.split('-')[0];
            return year === yearFilter;
        });
    }

    if (categoryFilter) {
        filtered = filtered.filter(item => {
            return item.project && item.project.category === categoryFilter;
        });
    }

    // Re-render table
    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-gray-500 py-8">No records match the selected filters.</td></tr>';
    } else {
        tbody.innerHTML = filtered.map(item => {
            const record = item.record;
            const project = item.project;
            const organization = item.organization;

            const categoryBadge = project ? (
                project.category === 'Environmental' ? '<span class="badge badge-primary">Environmental</span>' :
                    project.category === 'Education' ? '<span class="badge badge-blue">Education</span>' :
                        project.category === 'Care' ? '<span class="badge" style="background-color: #fce7f3; color: #831843;">Care</span>' :
                            `<span class="badge badge-secondary">${project.category}</span>`
            ) : '<span class="badge badge-secondary">N/A</span>';

            const statusBadge = record.status === 'approved' ?
                '<span class="badge badge-success">Certified</span>' :
                record.status === 'pending' ?
                    '<span class="badge badge-orange">Pending</span>' :
                    `<span class="badge badge-secondary">${record.status}</span>`;

            const completedDate = record.completed_at || 'N/A';

            const projectLink = project && project.id ?
                `<a href="/project/${project.id}" style="color: inherit; text-decoration: none;">${project.title}</a>` :
                'Unknown Project';

            const orgName = organization ?
                (organization.display_name || organization.username) :
                'Unknown Organization';

            return `
                <tr>
                    <td>${projectLink}</td>
                    <td>${categoryBadge}</td>
                    <td class="text-sm text-gray-600">${orgName}</td>
                    <td>${completedDate}</td>
                    <td>
                        <div class="flex items-center gap-1">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--gray-500);">
                                <circle cx="12" cy="12" r="10"/>
                                <polyline points="12 6 12 12 16 14"/>
                            </svg>
                            <span>${record.hours.toFixed(1)}h</span>
                        </div>
                    </td>
                    <td>
                        <div class="flex items-center gap-1">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--secondary-blue);">
                                <circle cx="12" cy="8" r="7"/>
                                <polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>
                            </svg>
                            <span style="color: var(--secondary-blue);">${record.points}</span>
                        </div>
                    </td>
                    <td>${statusBadge}</td>
                </tr>
            `;
        }).join('');
    }

    // Update summary
    const filteredHours = filtered.reduce((sum, item) => {
        return sum + (item.record.status === 'approved' ? item.record.hours : 0);
    }, 0);
    const filteredPoints = filtered.reduce((sum, item) => {
        return sum + (item.record.status === 'approved' ? item.record.points : 0);
    }, 0);
    const filteredCompleted = filtered.filter(item => item.record.status === 'approved').length;

    const summaryText = document.querySelector('.card.mt-6 .text-sm.text-gray-600');
    const summarySubtext = document.querySelector('.card.mt-6 .text-xs.text-gray-500');

    if (summaryText) {
        summaryText.textContent = `Showing ${filtered.length} record${filtered.length !== 1 ? 's' : ''}, totaling ${filteredHours.toFixed(1)} hours and ${filteredPoints} points`;
    }
    if (summarySubtext) {
        if (filteredCompleted > 0) {
            summarySubtext.textContent = `You have completed ${filteredCompleted} volunteer project${filteredCompleted !== 1 ? 's' : ''}. Keep up the great work!`;
        } else {
            summarySubtext.textContent = 'Start volunteering to earn hours and points!';
        }
    }
}

// Clear all filters
function clearFilters() {
    document.getElementById('year-filter').value = '';
    document.getElementById('category-filter').value = '';
    filterRecords();
}

// Export all records
function exportAllRecords() {
    window.location.href = '/api/participant/export-all-records';
}

// Export filtered records
function exportFilteredRecords() {
    const yearFilter = document.getElementById('year-filter').value;
    const categoryFilter = document.getElementById('category-filter').value;

    fetch('/api/participant/export-filtered-records', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            year: yearFilter || null,
            category: categoryFilter || null
        })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Export failed');
            }
            // Extract filename from Content-Disposition header
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'filtered_volunteer_records.xlsx';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1].replace(/['"]/g, '');
                }
            }
            return response.blob().then(blob => ({ blob, filename }));
        })
        .then(({ blob, filename }) => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(async error => {
            // Network or server-side error while exporting the Excel file
            console.error('Export error:', error);
            await Modal.error('Failed to export records. Please try again.');
        });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    // Load records data
    allRecords = getRecordsData();
    
    const yearFilter = document.getElementById('year-filter');
    const categoryFilter = document.getElementById('category-filter');
    const exportAllBtn = document.getElementById('export-all-btn');
    const exportFilteredBtn = document.getElementById('export-filtered-btn');

    if (yearFilter) {
        yearFilter.addEventListener('change', filterRecords);
    }
    if (categoryFilter) {
        categoryFilter.addEventListener('change', filterRecords);
    }
    if (exportAllBtn) {
        exportAllBtn.addEventListener('click', exportAllRecords);
    }
    if (exportFilteredBtn) {
        exportFilteredBtn.addEventListener('click', exportFilteredRecords);
    }
    
    // Make functions globally available for onclick handlers in HTML
    window.filterRecords = filterRecords;
    window.clearFilters = clearFilters;
    window.exportAllRecords = exportAllRecords;
    window.exportFilteredRecords = exportFilteredRecords;
});
