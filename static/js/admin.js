// Tab switching
document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
    item.addEventListener('click', function() {
        const tabName = this.getAttribute('data-tab');
        
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        this.classList.add('active');
        document.getElementById(tabName + '-tab').classList.add('active');
        
        // Load data when switching tabs
        if (tabName === 'project-review') {
            loadPendingProjects();
        } else if (tabName === 'hours-review') {
            loadPendingRecords();
        } else if (tabName === 'user-management') {
            loadUsers();
        }
    });
});

async function fetchDashboardData() {
    try {
        const response = await fetch('/api/v1/users/me/dashboard');
        if (response.status === 401) {
            return { error: 'Please log in as an administrator to view dashboard data.' };
        }
        if (!response.ok) {
            throw new Error('Failed to load admin data');
        }
        return await response.json();
    } catch (error) {
        console.error(error);
        return { error: 'Unable to load admin data. Please try again later.' };
    }
}

function renderPendingProjects(projects) {
    const container = document.querySelector('#project-review-tab');
    if (!container) return;
    
    if (!projects.length) {
        container.innerHTML = `
            <div class="mb-8">
                <h2>Project Review</h2>
                <p class="text-gray-600">Review volunteer projects submitted by organizations</p>
            </div>
            <div class="card">
                <div class="card-content">
                    <p class="text-gray-500 text-center py-8">No pending projects to review.</p>
                </div>
            </div>
        `;
        return;
    }
    
    const projectsHTML = projects.map(project => {
        const rating = project.rating || 0;
        const stars = Math.round(rating);
        let starsHTML = '';
        for (let i = 1; i <= 5; i++) {
            const filled = i <= stars ? 'filled' : '';
            starsHTML += `
                <svg class="star ${filled}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${filled ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
            `;
        }
        
        return `
            <div class="card mb-6">
                <div class="card-header">
                    <div class="flex items-center justify-between">
                        <div>
                            <h3 style="margin: 0;">${project.title}</h3>
                            <div class="flex items-center gap-2 mt-2">
                                <span class="badge badge-orange">Pending Review</span>
                                <span class="text-sm text-gray-600">${project.organization_name} · Submitted ${project.submitted_date}</span>
                            </div>
                        </div>
                        <div class="sustainability-rating rating-high">
                            <div class="stars">${starsHTML}</div>
                        </div>
                    </div>
                </div>
                <div class="card-content">
                    <div class="grid grid-cols-3 gap-4 mb-4 text-sm">
                        <div>
                            <span class="text-gray-600">Activity Date: </span>
                            <span>${project.date || 'TBD'}</span>
                        </div>
                        <div>
                            <span class="text-gray-600">Expected Participants: </span>
                            <span>${project.max_participants} people</span>
                        </div>
                        <div>
                            <span class="text-gray-600">Sustainability Rating: </span>
                            <span>${rating.toFixed(1)}/5.0</span>
                        </div>
                    </div>
                    <div style="background-color: var(--gray-50); padding: 1rem; border-radius: var(--border-radius); margin-bottom: 1rem;">
                        <p class="text-sm text-gray-700 mb-2">Project Description:</p>
                        <p class="text-sm text-gray-600">${project.description || 'No description provided.'}</p>
                    </div>
                    <div class="flex gap-3">
                        <button class="btn btn-primary" onclick="approveProject(${project.id})">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 0.5rem;">
                                <polyline points="20 6 9 17 4 12"/>
                            </svg>
                            Approve
                        </button>
                        <button class="btn" style="background-color: #ef4444; color: white;" onclick="rejectProject(${project.id})">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 0.5rem;">
                                <line x1="18" y1="6" x2="6" y2="18"/>
                                <line x1="6" y1="6" x2="18" y2="18"/>
                            </svg>
                            Reject
                        </button>
                        <button class="btn btn-outline" onclick="window.location.href='/project/${project.id}'">View Details</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = `
        <div class="mb-8">
            <h2>Project Review</h2>
            <p class="text-gray-600">Review volunteer projects submitted by organizations</p>
        </div>
        ${projectsHTML}
    `;
}

function renderPendingRecords(records) {
    const container = document.querySelector('#hours-review-tab .card .card-content');
    if (!container) return;
    
    if (!records.length) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">No pending hour records to review.</p>';
        updateBatchApproveButton(0);
        return;
    }
    
    const tableHTML = `
        <table>
            <thead>
                <tr>
                    <th style="width: 3rem;">
                        <input type="checkbox" id="select-all-records" style="width: 1rem; height: 1rem;">
                    </th>
                    <th>Participant</th>
                    <th>Project Name</th>
                    <th>Organization</th>
                    <th>Hours</th>
                    <th>Points</th>
                    <th>Completion Date</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${records.map(record => `
                    <tr>
                        <td><input type="checkbox" class="record-checkbox" data-record-id="${record.id}" style="width: 1rem; height: 1rem;"></td>
                        <td>${record.participant_name}</td>
                        <td>${record.project_name}</td>
                        <td class="text-sm text-gray-600">${record.organization_name}</td>
                        <td><span class="badge badge-secondary">${record.hours}h</span></td>
                        <td><span class="badge badge-blue">${record.points} pts</span></td>
                        <td class="text-sm text-gray-600">${record.completion_date || 'N/A'}</td>
                        <td>
                            <div class="flex gap-2">
                                <button class="btn btn-outline btn-sm" style="color: var(--primary-green);" onclick="approveRecord(${record.id})">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 0.25rem;">
                                        <polyline points="20 6 9 17 4 12"/>
                                    </svg>
                                    Approve
                                </button>
                                <button class="btn btn-outline btn-sm" style="color: #ef4444;" onclick="rejectRecord(${record.id})">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 0.25rem;">
                                        <line x1="18" y1="6" x2="6" y2="18"/>
                                        <line x1="6" y1="6" x2="18" y2="18"/>
                                    </svg>
                                    Reject
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = tableHTML;
    
    // Setup select all checkbox
    const selectAllCheckbox = document.getElementById('select-all-records');
    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            const checkboxes = document.querySelectorAll('.record-checkbox');
            checkboxes.forEach(cb => cb.checked = this.checked);
            updateBatchApproveButton();
        });
    }
    
    // Setup individual checkbox change handlers
    const checkboxes = document.querySelectorAll('.record-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateBatchApproveButton();
            updateSelectAllCheckbox();
        });
    });
    
    updateBatchApproveButton(0);
}

function updateSelectAllCheckbox() {
    const selectAllCheckbox = document.getElementById('select-all-records');
    if (!selectAllCheckbox) return;
    
    const checkboxes = document.querySelectorAll('.record-checkbox');
    const checkedCount = document.querySelectorAll('.record-checkbox:checked').length;
    
    if (checkedCount === 0) {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = false;
    } else if (checkedCount === checkboxes.length) {
        selectAllCheckbox.checked = true;
        selectAllCheckbox.indeterminate = false;
    } else {
        selectAllCheckbox.checked = false;
        selectAllCheckbox.indeterminate = true;
    }
}

function updateBatchApproveButton(count) {
    const button = document.querySelector('#hours-review-tab .btn-primary');
    if (!button) return;
    
    if (count !== undefined) {
        button.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 0.5rem;">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
            Batch Approve (${count})
        `;
    } else {
        const checkedCount = document.querySelectorAll('.record-checkbox:checked').length;
        button.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 0.5rem;">
                <polyline points="20 6 9 17 4 12"/>
            </svg>
            Batch Approve (${checkedCount})
        `;
    }
}

async function batchApproveRecords() {
    const checkedBoxes = document.querySelectorAll('.record-checkbox:checked');
    if (checkedBoxes.length === 0) {
        alert('Please select at least one record to approve.');
        return;
    }
    
    const recordIds = Array.from(checkedBoxes).map(cb => parseInt(cb.getAttribute('data-record-id')));
    
    if (!confirm(`Are you sure you want to approve ${recordIds.length} hour record(s)?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/v1/records/batch', {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ record_ids: recordIds, status: 'approved' })
        });
        
        const result = await response.json();
        if (response.ok) {
            alert(`Successfully approved ${result.updated_count} hour record(s)!`);
            loadPendingRecords();
        } else {
            alert('Error: ' + (result.error || 'Failed to approve records'));
        }
    } catch (error) {
        console.error(error);
        alert('Error approving records. Please try again.');
    }
}

function renderUsers(users) {
    const container = document.querySelector('#user-management-tab .card .card-content');
    if (!container) return;
    
    if (!users.length) {
        container.innerHTML = '<p class="text-gray-500 text-center py-8">No users found.</p>';
        return;
    }
    
    const tableHTML = `
        <table>
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Type</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Registration Date</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${users.map(user => {
                    const isActive = user.is_active !== false; // Default to true if not set
                    return `
                    <tr>
                        <td>${user.display_name || user.username}</td>
                        <td><span class="badge badge-secondary">${user.user_type.charAt(0).toUpperCase() + user.user_type.slice(1)}</span></td>
                        <td class="text-sm text-gray-600">${user.email}</td>
                        <td>
                            ${isActive 
                                ? '<span class="badge badge-success">Active</span>' 
                                : '<span class="badge" style="background-color: #ef4444; color: white;">Disabled</span>'}
                        </td>
                        <td class="text-sm text-gray-600">${user.created_at || 'N/A'}</td>
                        <td>
                            <div class="flex gap-2">
                                <button class="btn btn-outline btn-sm">View</button>
                                ${isActive
                                    ? `<button class="btn btn-outline btn-sm" style="color: #ef4444;" onclick="toggleUserStatus(${user.id}, false)">Disable</button>`
                                    : `<button class="btn btn-outline btn-sm" style="color: var(--primary-green);" onclick="toggleUserStatus(${user.id}, true)">Enable</button>`}
                            </div>
                        </td>
                    </tr>
                `;
                }).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = tableHTML;
}

async function toggleUserStatus(userId, enable) {
    const action = enable ? 'enable' : 'disable';
    if (!confirm(`Are you sure you want to ${action} this user?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/users/${userId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ is_active: enable })
        });
        
        const result = await response.json();
        if (response.ok) {
            alert(`User ${enable ? 'enabled' : 'disabled'} successfully!`);
            loadUsers();
        } else {
            alert('Error: ' + (result.error || `Failed to ${action} user`));
        }
    } catch (error) {
        console.error(error);
        alert(`Error ${action}ing user. Please try again.`);
    }
}

async function loadPendingProjects() {
    const data = await fetchDashboardData();
    if (data.error) {
        console.error(data.error);
        return;
    }
    renderPendingProjects(data.pending_projects || []);
}

async function loadPendingRecords() {
    const data = await fetchDashboardData();
    if (data.error) {
        console.error(data.error);
        return;
    }
    renderPendingRecords(data.pending_records || []);
}

async function loadUsers() {
    const data = await fetchDashboardData();
    if (data.error) {
        console.error(data.error);
        return;
    }
    renderUsers(data.users || []);
}

async function approveProject(projectId) {
    if (!confirm('Are you sure you want to approve this project?')) return;
    
    try {
        const response = await fetch(`/api/v1/projects/${projectId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'approved' })
        });
        const result = await response.json();
        if (response.ok) {
            alert('Project approved successfully!');
            loadPendingProjects();
        } else {
            alert('Error: ' + (result.error || 'Failed to approve project'));
        }
    } catch (error) {
        console.error(error);
        alert('Error approving project. Please try again.');
    }
}

async function rejectProject(projectId) {
    if (!confirm('Are you sure you want to reject this project?')) return;
    
    try {
        const response = await fetch(`/api/v1/projects/${projectId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'rejected' })
        });
        const result = await response.json();
        if (response.ok) {
            alert('Project rejected.');
            loadPendingProjects();
        } else {
            alert('Error: ' + (result.error || 'Failed to reject project'));
        }
    } catch (error) {
        console.error(error);
        alert('Error rejecting project. Please try again.');
    }
}

async function approveRecord(recordId) {
    if (!confirm('Are you sure you want to approve this hour record?')) return;
    
    try {
        const response = await fetch(`/api/v1/records/${recordId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'approved' })
        });
        const result = await response.json();
        if (response.ok) {
            alert('Hour record approved successfully!');
            loadPendingRecords();
        } else {
            alert('Error: ' + (result.error || 'Failed to approve record'));
        }
    } catch (error) {
        console.error(error);
        alert('Error approving record. Please try again.');
    }
}

async function rejectRecord(recordId) {
    if (!confirm('Are you sure you want to reject this hour record?')) return;
    
    try {
        const response = await fetch(`/api/v1/records/${recordId}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'rejected' })
        });
        const result = await response.json();
        if (response.ok) {
            alert('Hour record rejected.');
            loadPendingRecords();
        } else {
            alert('Error: ' + (result.error || 'Failed to reject record'));
        }
    } catch (error) {
        console.error(error);
        alert('Error rejecting record. Please try again.');
    }
}

// System Settings Functions
async function loadSettings() {
    try {
        const response = await fetch('/api/v1/admin/settings');
        if (!response.ok) {
            throw new Error('Failed to load settings');
        }
        const settings = await response.json();
        
        // Load points per hour
        const pointsInput = document.getElementById('points-per-hour-input');
        if (pointsInput) {
            pointsInput.value = settings.points_per_hour || '20';
        }
        
        // Load auto-approve setting
        const autoApproveCheckbox = document.getElementById('auto-approve-checkbox');
        if (autoApproveCheckbox) {
            autoApproveCheckbox.checked = settings.auto_approve_under_hours === 'true';
        }
        
        // Load project review requirement
        const projectReviewCheckbox = document.getElementById('project-review-checkbox');
        if (projectReviewCheckbox) {
            projectReviewCheckbox.checked = settings.project_requires_review === 'true';
        }
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

async function savePointsSettings() {
    const pointsInput = document.getElementById('points-per-hour-input');
    if (!pointsInput) return;
    
    const points = parseInt(pointsInput.value);
    if (isNaN(points) || points < 1) {
        alert('Please enter a valid number (at least 1) for points per hour.');
        return;
    }
    
    const saveBtn = document.getElementById('save-points-settings-btn');
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    try {
        const response = await fetch('/api/v1/admin/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                points_per_hour: points
            })
        });
        
        const result = await response.json();
        if (response.ok) {
            alert('Points settings saved successfully!');
        } else {
            alert('Error: ' + (result.error || 'Failed to save settings'));
        }
    } catch (error) {
        console.error(error);
        alert('Error saving settings. Please try again.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
    }
}

async function saveReviewSettings() {
    const autoApproveCheckbox = document.getElementById('auto-approve-checkbox');
    const projectReviewCheckbox = document.getElementById('project-review-checkbox');
    
    if (!autoApproveCheckbox || !projectReviewCheckbox) return;
    
    const saveBtn = document.getElementById('save-review-settings-btn');
    const originalText = saveBtn.textContent;
    saveBtn.disabled = true;
    saveBtn.textContent = 'Saving...';
    
    try {
        const response = await fetch('/api/v1/admin/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                auto_approve_under_hours: autoApproveCheckbox.checked,
                project_requires_review: projectReviewCheckbox.checked
            })
        });
        
        const result = await response.json();
        if (response.ok) {
            alert('Review settings saved successfully!');
        } else {
            alert('Error: ' + (result.error || 'Failed to save settings'));
        }
    } catch (error) {
        console.error(error);
        alert('Error saving settings. Please try again.');
    } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
    }
}

// Load data on page load
document.addEventListener('DOMContentLoaded', function() {
    loadPendingProjects();
    
    // Load settings when switching to settings tab
    document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
        item.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            if (tabName === 'settings') {
                loadSettings();
            }
        });
    });
    
    // Load settings if settings tab is active on page load
    const settingsTab = document.getElementById('settings-tab');
    if (settingsTab && settingsTab.classList.contains('active')) {
        loadSettings();
    }
    
    // Setup save buttons
    const savePointsBtn = document.getElementById('save-points-settings-btn');
    if (savePointsBtn) {
        savePointsBtn.addEventListener('click', savePointsSettings);
    }
    
    const saveReviewBtn = document.getElementById('save-review-settings-btn');
    if (saveReviewBtn) {
        saveReviewBtn.addEventListener('click', saveReviewSettings);
    }
});



