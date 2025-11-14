// Tab switching
document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
    item.addEventListener('click', function() {
        const tabName = this.getAttribute('data-tab');
        
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        this.classList.add('active');
        document.getElementById(tabName + '-tab').classList.add('active');
        
        // Load data when switching to specific tabs
        if (tabName === 'manage') {
            loadProjects();
        } else if (tabName === 'registrations') {
            loadRegistrations();
        }
    });
});

let currentRegistrationsProjectId = null;

function getRegistrationStatusMeta(status) {
    const normalized = (status || 'registered').toLowerCase();
    const map = {
        'registered': { label: 'Pending', badge: 'badge-orange' },
        'approved': { label: 'Approved', badge: 'badge-success' },
        'cancelled': { label: 'Declined', badge: 'badge-secondary' },
        'completed': { label: 'Completed', badge: 'badge-primary' }
    };
    if (map[normalized]) {
        return map[normalized];
    }
    const fallbackLabel = normalized.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    return { label: fallbackLabel, badge: 'badge-secondary' };
}

async function fetchDashboardData() {
    try {
        const response = await fetch('/api/organization/dashboard-data');
        if (response.status === 401) {
            return { error: 'Please log in as an organization to view dashboard data.' };
        }
        if (!response.ok) {
            throw new Error('Failed to load organization data');
        }
        return await response.json();
    } catch (error) {
        console.error(error);
        return { error: 'Unable to load organization data. Please try again later.' };
    }
}

function updateStatistics(stats) {
    const activeEl = document.getElementById('org-stat-active');
    const participantsEl = document.getElementById('org-stat-participants');
    const completedEl = document.getElementById('org-stat-completed');
    const pendingEl = document.getElementById('org-stat-pending');
    
    if (activeEl) activeEl.textContent = stats.active_projects || 0;
    if (participantsEl) participantsEl.textContent = stats.total_participants || 0;
    if (completedEl) completedEl.textContent = stats.completed || 0;
    if (pendingEl) pendingEl.textContent = stats.pending || 0;
}

function renderProjects(projects) {
    const container = document.getElementById('projects-list');
    if (!container) return;
    
    if (!projects.length) {
        container.innerHTML = '<p class="text-gray-500 text-center py-6">You have not created any projects yet.</p>';
        return;
    }
    
    container.innerHTML = projects.map(project => {
        const statusBadge = project.status === 'approved' ? 
            '<span class="badge badge-success">Approved</span>' :
            project.status === 'pending' ?
            '<span class="badge badge-orange">Pending</span>' :
            '<span class="badge badge-secondary">' + project.status + '</span>';
        
        return `
            <div class="card mb-4">
                <div class="card-content">
                    <div class="flex items-start justify-between">
                        <div style="flex: 1;">
                            <div class="flex items-center gap-3 mb-2">
                                <h3 style="margin: 0;">${project.title}</h3>
                                ${statusBadge}
                            </div>
                            <p class="text-sm text-gray-600 mb-2">${project.location} · ${project.date || 'TBD'}</p>
                            <p class="text-sm text-gray-600">${project.current_participants}/${project.max_participants} participants</p>
                        </div>
                        <div class="flex gap-2">
                            <button class="btn btn-outline" onclick="window.location.href='/project/${project.id}'">View</button>
                            <button class="btn btn-outline" onclick="loadProjectRegistrations(${project.id})">Registrations</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

async function loadProjects() {
    const data = await fetchDashboardData();
    if (data.error) {
        const container = document.getElementById('projects-list');
        if (container) {
            container.innerHTML = `<p class="text-gray-500 text-center py-6">${data.error}</p>`;
        }
        return;
    }
    renderProjects(data.projects || []);
}

async function loadRegistrations() {
    // Load registrations for the first project or show message
    const data = await fetchDashboardData();
    if (data.error || !data.projects || data.projects.length === 0) {
        const container = document.querySelector('#registrations-tab .card');
        if (container) {
            container.innerHTML = '<div class="card-content"><p class="text-gray-500 text-center py-6">No projects available.</p></div>';
        }
        return;
    }
    
    // Load registrations for the first project
    loadProjectRegistrations(data.projects[0].id);
}

async function loadProjectRegistrations(projectId) {
    currentRegistrationsProjectId = projectId;
    try {
        const response = await fetch(`/api/organization/registrations/${projectId}`);
        if (!response.ok) {
            throw new Error('Failed to load registrations');
        }
        const data = await response.json();
        
        const container = document.querySelector('#registrations-tab .card');
        if (!container) return;
        const rowsHtml = data.registrations.map(reg => {
            const meta = getRegistrationStatusMeta(reg.status);
            let actions = '<span class="text-sm text-gray-400">No actions</span>';
            
            if (reg.status === 'registered') {
                // 待审核状态：可以批准或拒绝
                actions = `
                    <div class="flex gap-2">
                        <button class="btn btn-outline btn-sm" onclick="updateRegistrationStatus(${reg.id}, 'approved')">Approve</button>
                        <button class="btn btn-outline btn-sm" style="color: #ef4444;" onclick="updateRegistrationStatus(${reg.id}, 'cancelled')">Decline</button>
                    </div>
                `;
            } else if (reg.status === 'approved') {
                // 已批准状态：可以确认完成
                actions = `
                    <div class="flex gap-2">
                        <button class="btn btn-primary btn-sm" onclick="confirmCompletion(${reg.id})">Confirm Completion</button>
                    </div>
                `;
            }
            
            return `
                <tr>
                    <td>${reg.participant_name}</td>
                    <td>${reg.participant_email}</td>
                    <td>${reg.registration_date || 'N/A'}</td>
                    <td><span class="badge ${meta.badge}">${meta.label}</span></td>
                    <td>${actions}</td>
                </tr>
            `;
        }).join('');
        
        container.innerHTML = `
            <div class="card-header">
                <h3 style="margin: 0;">${data.project_title} - Registration List</h3>
                <p class="text-sm text-gray-600 mt-1">${data.registrations.length} people registered</p>
            </div>
            <div class="card-content">
                ${data.registrations.length > 0 ? `
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Email</th>
                                <th>Registration Date</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHtml}
                        </tbody>
                    </table>
                ` : '<p class="text-gray-500 text-center py-6">No registrations yet.</p>'}
            </div>
        `;
        
        // Switch to registrations tab
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelector('.nav-item[data-tab="registrations"]').classList.add('active');
        document.getElementById('registrations-tab').classList.add('active');
    } catch (error) {
        console.error(error);
    }
}

async function updateRegistrationStatus(registrationId, status) {
    if (!currentRegistrationsProjectId) {
        return;
    }
    const actionLabel = status === 'approved' ? 'approve' : status === 'cancelled' ? 'decline' : 'update';
    try {
        const response = await fetch(`/api/organization/registration/${registrationId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.error || `Unable to ${actionLabel} registration.`);
        }
        loadProjectRegistrations(currentRegistrationsProjectId);
        loadProjects();
    } catch (error) {
        console.error(error);
        alert(error.message || 'Unable to update registration status.');
    }
}

async function confirmCompletion(registrationId) {
    if (!confirm('Confirm that this participant has completed the project? This will create a volunteer record for admin review.')) {
        return;
    }
    
    if (!currentRegistrationsProjectId) {
        return;
    }
    
    try {
        const response = await fetch(`/api/organization/registration/${registrationId}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'completed' })
        });
        const result = await response.json();
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Unable to confirm completion.');
        }
        alert('Participant completion confirmed! A volunteer record has been created and sent to admin for review.');
        loadProjectRegistrations(currentRegistrationsProjectId);
        loadProjects();
    } catch (error) {
        console.error(error);
        alert(error.message || 'Unable to confirm completion.');
    }
}

// Handle project creation form
document.addEventListener('DOMContentLoaded', function() {
    // Load dashboard data
    fetchDashboardData().then(data => {
        if (!data.error && data.statistics) {
            updateStatistics(data.statistics);
        }
    });
    
    // Handle project creation form
    const createForm = document.querySelector('form[action="/api/create-project"]');
    if (createForm) {
        createForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            try {
                const response = await fetch('/api/organization/create-project', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                if (result.success) {
                    alert('Project submitted successfully! It will be reviewed by an administrator.');
                    this.reset();
                    loadProjects();
                } else {
                    alert('Error: ' + (result.error || 'Failed to create project'));
                }
            } catch (error) {
                console.error(error);
                alert('Error creating project. Please try again.');
            }
        });
    }
});

