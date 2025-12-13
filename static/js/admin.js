// Tab switching
document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
    item.addEventListener('click', function () {
        const tabName = this.getAttribute('data-tab');

        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        this.classList.add('active');
        document.getElementById(tabName + '-tab').classList.add('active');

        // Load data on tab switch
        if (tabName === 'hours-review') loadHourRecords();
        if (tabName === 'project-review') loadPendingProjects();
        if (tabName === 'user-management') loadUsers();
        if (tabName === 'logs') loadLogs();
    });
});

// Load pending projects
async function loadPendingProjects() {
    try {
        const response = await fetch('/api/v1/projects?all=true');
        if (!response.ok) throw new Error('Failed to load projects');

        const projects = await response.json();
        const pendingProjects = projects.filter(p => p.status === 'pending');

        const container = document.getElementById('project-review-tab');
        const header = container.querySelector('.mb-8');

        let html = '';
        if (pendingProjects.length === 0) {
            html = '<div class="card"><div class="card-content"><p class="text-gray-500 text-center py-6">No pending projects to review.</p></div></div>';
        } else {
            html = pendingProjects.map(project => `
                <div class="card mb-6">
                    <div class="card-header">
                        <div class="flex items-center justify-between">
                            <div>
                                <h3 style="margin: 0;">${project.title}</h3>
                                <div class="flex items-center gap-2 mt-2">
                                    <span class="badge badge-orange">Pending Review</span>
                                    <span class="text-sm text-gray-600">${project.organization_name || 'Organization'} · Submitted ${project.created_at || 'Recently'}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="card-content">
                        <div class="grid grid-cols-3 gap-4 mb-4 text-sm">
                            <div><span class="text-gray-600">Date: </span><span>${project.date}</span></div>
                            <div><span class="text-gray-600">Location: </span><span>${project.location}</span></div>
                            <div><span class="text-gray-600">Participants: </span><span>${project.max_participants}</span></div>
                        </div>
                        <div style="background-color: var(--gray-50); padding: 1rem; border-radius: var(--border-radius); margin-bottom: 1rem;">
                            <p class="text-sm text-gray-700 mb-2">Description:</p>
                            <p class="text-sm text-gray-600">${project.description}</p>
                        </div>
                        <div class="flex gap-3">
                            <button class="btn btn-primary" onclick="reviewProject(${project.id}, 'approved')">Approve</button>
                            <button class="btn" style="background-color: #ef4444; color: white;" onclick="reviewProject(${project.id}, 'rejected')">Reject</button>
                        </div>
                    </div>
                </div>
    `).join('');
        }

        container.innerHTML = '';
        if (header) container.appendChild(header);
        const listDiv = document.createElement('div');
        listDiv.innerHTML = html;
        container.appendChild(listDiv);

    } catch (e) {
        console.error(e);
    }
}

// Review project
async function reviewProject(projectId, status) {
    const action = status === 'approved' ? 'approve' : 'reject';
    const confirmed = await Modal.confirm(`Are you sure you want to ${action} this project?`, {
        type: status === 'approved' ? 'info' : 'warning',
        confirmText: status === 'approved' ? 'Approve' : 'Reject'
    });

    if (!confirmed) return;

    try {
        const response = await fetch(`/api/v1/projects/${projectId}/review`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });

        if (response.ok) {
            await Modal.success(`Project ${action}d successfully`);
            loadPendingProjects();
        } else {
            const data = await response.json();
            await Modal.error(data.error || `Failed to ${action} project`);
        }
    } catch (e) {
        console.error(e);
        await Modal.error(`Failed to ${action} project`);
    }
}

// Load hour records
async function loadHourRecords() {
    try {
        const response = await fetch('/api/v1/records?status=pending');
        if (!response.ok) throw new Error('Failed to load records');

        const records = await response.json();
        renderHourRecords(records);
    } catch (e) {
        console.error(e);
    }
}

function renderHourRecords(records) {
    const tbody = document.querySelector('#hours-review-tab tbody');
    if (!tbody) return;

    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center py-4 text-gray-500">No pending records</td></tr>';
        const batchBtn = document.getElementById('batch-approve-btn');
        if (batchBtn) batchBtn.textContent = 'Batch Approve (0)';
        return;
    }

    tbody.innerHTML = records.map(record => `
        <tr>
            <td><input type="checkbox" class="record-checkbox" value="${record.id}" style="width: 1rem; height: 1rem;"></td>
            <td>${record.participant?.name || 'N/A'}</td>
            <td>${record.project?.title || 'N/A'}</td>
            <td class="text-sm text-gray-600">${record.organization?.name || 'N/A'}</td>
            <td><span class="badge badge-secondary">${record.hours}h</span></td>
            <td><span class="badge badge-blue">${record.points} pts</span></td>
            <td class="text-sm text-gray-600">${record.completed_at || record.date || ''}</td>
            <td>
                <div class="flex gap-2">
                    <button class="btn btn-outline btn-sm" style="color: var(--primary-green);" onclick="reviewRecord(${record.id}, 'approved')">Approve</button>
                    <button class="btn btn-outline btn-sm" style="color: #ef4444;" onclick="reviewRecord(${record.id}, 'rejected')">Reject</button>
                </div>
            </td>
        </tr>
    `).join('');

    updateBatchCount();

    document.querySelectorAll('.record-checkbox').forEach(cb => {
        cb.addEventListener('change', updateBatchCount);
    });
}

function updateBatchCount() {
    const checked = document.querySelectorAll('.record-checkbox:checked').length;
    const btn = document.getElementById('batch-approve-btn');
    if (btn) btn.textContent = `Batch Approve (${checked})`;
}

async function reviewRecord(recordId, status) {
    try {
        const response = await fetch(`/api/v1/records/${recordId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });

        if (response.ok) {
            loadHourRecords();
        } else {
            const data = await response.json();
            await Modal.error(data.error || 'Failed to update record');
        }
    } catch (e) {
        console.error(e);
        await Modal.error('Failed to update record');
    }
}

async function batchApproveRecords() {
    const checkboxes = document.querySelectorAll('.record-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => cb.value);

    if (ids.length === 0) {
        await Modal.info('Please select records to approve');
        return;
    }

    const confirmed = await Modal.confirm(`Approve ${ids.length} records?`);
    if (!confirmed) return;

    try {
        const response = await fetch('/api/v1/records/batch', {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ record_ids: ids, status: 'approved' })
        });

        if (response.ok) {
            const data = await response.json();
            await Modal.success(`Batch approval successful (${data.updated_count || ids.length})`);
            loadHourRecords();
        } else {
            const data = await response.json();
            await Modal.error(data.error || 'Batch approval failed');
        }
    } catch (e) {
        console.error(e);
        await Modal.error('Batch approval failed');
    }
}

// User Management
async function loadUsers() {
    try {
        // FIXED: Correct API endpoint
        const response = await fetch('/api/v1/users');
        if (!response.ok) return;
        const users = await response.json();

        const tbody = document.querySelector('#user-management-tab tbody');
        if (!tbody) return;

        tbody.innerHTML = users.map(user => `
            <tr>
                <td>${user.username}</td>
                <td><span class="badge badge-secondary">${user.role || user.user_type}</span></td>
                <td class="text-sm text-gray-600">${user.email}</td>
                <td><span class="badge ${user.is_active ? 'badge-success' : 'badge-secondary'}">${user.is_active ? 'Active' : 'Disabled'}</span></td>
                <td class="text-sm text-gray-600">${user.created_at || '-'}</td>
                <td>
                    <div class="flex gap-2">
                        <button class="btn btn-outline btn-sm" onclick="viewUser(${user.id})">View</button>
                        <button class="btn btn-outline btn-sm" onclick="toggleUserStatus(${user.id}, ${!user.is_active})">
                            ${user.is_active ? 'Disable' : 'Enable'}
                        </button>
                        ${user.is_active ? `<button class="btn btn-outline btn-sm" style="color: #ef4444;" onclick="banUser(${user.id})">Ban</button>` : ''}
                        <button class="btn btn-outline btn-sm" style="color: #ef4444; border-color: #ef4444;" onclick="deleteUser(${user.id})">Delete</button>
                    </div>
                </td>
            </tr>
        `).join('');

    } catch (e) {
        console.error(e);
    }
}

async function viewUser(userId) {
    // Basic view implementation for now
    try {
        const response = await fetch(`/api/v1/users/${userId}`);
        const user = await response.json();
        if (user.error) throw new Error(user.error);

        await Modal.alert(
            `User Details:\n\nUsername: ${user.username}\nEmail: ${user.email}\nType: ${user.user_type}\nJoin Date: ${user.created_at}`,
            { title: user.display_name || user.username }
        );
    } catch (e) {
        await Modal.error('Failed to load user details');
    }
}

async function toggleUserStatus(userId, isActive) {
    const action = isActive ? 'enable' : 'disable';
    const confirmed = await Modal.confirm(`Are you sure you want to ${action} this user?`);
    if (!confirmed) return;

    try {
        // FIXED: Correct endpoint and method
        const response = await fetch(`/api/v1/users/${userId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });

        if (response.ok) {
            await Modal.success(`User ${action}d successfully`);
            loadUsers();
        } else {
            await Modal.error(`Failed to ${action} user`);
        }
    } catch (e) {
        console.error(e);
        await Modal.error(`Failed to ${action} user`);
    }
}

async function banUser(userId) {
    const hoursStr = await Modal.prompt('Enter ban duration in hours (e.g., 24 for 1 day):', { defaultValue: '24' });
    if (!hoursStr) return;

    const hours = parseInt(hoursStr);
    if (isNaN(hours) || hours <= 0) {
        await Modal.error('Invalid duration');
        return;
    }

    const reason = await Modal.prompt('Enter reason for ban:', { placeholder: 'Violation of terms...' });
    if (!reason) return;

    try {
        // FIXED: Correct endpoint and method
        const response = await fetch(`/api/v1/users/${userId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                is_active: false,
                ban_hours: hours,
                ban_reason: reason
            })
        });

        if (response.ok) {
            await Modal.success(`User banned for ${hours} hours`);
            loadUsers();
        } else {
            const data = await response.json();
            await Modal.error(data.error || 'Failed to ban user');
        }
    } catch (e) {
        console.error(e);
        await Modal.error('Failed to ban user');
    }
}

async function deleteUser(userId) {
    const confirmed = await Modal.confirm('Are you sure you want to DELETE this user? This cannot be undone.', { type: 'warning', confirmText: 'Delete User' });
    if (!confirmed) return;

    try {
        const response = await fetch(`/api/v1/users/${userId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            await Modal.success('User deleted successfully');
            loadUsers();
        } else {
            const data = await response.json();
            await Modal.error(data.error || 'Failed to delete user');
        }
    } catch (e) {
        console.error(e);
        await Modal.error('Failed to delete user');
    }
}

// Settings
document.getElementById('save-points-settings-btn')?.addEventListener('click', async () => {
    // Placeholder logic 
    const points = document.getElementById('points-per-hour-input').value;
    await Modal.success(`Points settings saved: ${points} points/hour`);
});

document.getElementById('save-review-settings-btn')?.addEventListener('click', async () => {
    await Modal.success('Review settings saved');
});

// Admin creation
document.getElementById('create-admin-btn')?.addEventListener('click', async () => {
    // Simple prompt-based creation for now to avoid building a full modal form
    // In a real app, a proper form modal would be better

    const username = await Modal.prompt("New Admin Username:", { placeholder: "Username" });
    if (!username) return;

    const email = await Modal.prompt("New Admin Email:", { placeholder: "EMAIL" });
    if (!email) return;

    const password = await Modal.prompt("New Admin Password:", { placeholder: "Password", inputType: "password" });
    if (!password) return;

    try {
        const response = await fetch('/api/v1/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });

        if (response.ok) {
            await Modal.success("New admin created successfully!");
        } else {
            const data = await response.json();
            await Modal.error(data.error || "Failed to create admin");
        }
    } catch (e) {
        await Modal.error("Error creating admin");
    }
});

// Load system logs
async function loadLogs() {
    const container = document.getElementById('logs-container');
    const levelFilter = document.getElementById('log-level-filter')?.value || '';

    if (!container) return;

    container.textContent = 'Loading logs...';

    try {
        const url = `/api/v1/admin/logs?lines=200${levelFilter ? `&level=${levelFilter}` : ''}`;
        const response = await fetch(url);

        if (!response.ok) {
            container.textContent = 'Failed to load logs';
            return;
        }

        const data = await response.json();

        if (data.logs && data.logs.length > 0) {
            container.textContent = data.logs.join('');
        } else {
            container.textContent = data.message || 'No logs available.';
        }
    } catch (e) {
        console.error(e);
        container.textContent = 'Error loading logs.';
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadPendingProjects();
});
