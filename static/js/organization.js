// Tab switching
document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
    item.addEventListener('click', function () {
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
        'cancelled': { label: 'Cancelled', badge: 'badge-secondary' },
        'rejected': { label: 'Rejected', badge: 'badge-secondary' },
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
        const response = await fetch('/api/v1/users/me/dashboard');
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

function renderRating(rating) {
    const colorClass = rating < 3 ? 'rating-low' : rating < 4 ? 'rating-medium' : 'rating-high';
    let starsHTML = '<div class="stars">';
    for (let i = 1; i <= 5; i++) {
        const filled = i <= rating ? 'filled' : '';
        starsHTML += `
            <svg class="star ${filled} ${colorClass}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${filled ? 'currentColor' : 'none'}" stroke="currentColor" stroke-width="2">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
        `;
    }
    starsHTML += '</div>';
    return `<div class="sustainability-rating ${colorClass}">${starsHTML}</div>`;
}

function renderRecentProjectCard(project) {
    return `
        <div class="card project-card" onclick="window.location.href='/project/${project.id}'">
            <div class="card-header">
                <div class="flex justify-between items-center mb-2">
                    <h3 style="margin: 0; font-size: 1rem;">${project.title}</h3>
                    ${project.rating ? renderRating(project.rating) : ''}
                </div>
                <p class="text-sm text-gray-600">${project.organization_name ?? ''}</p>
            </div>
            <div class="card-content">
                <div style="display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem; font-size: 0.875rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--gray-600);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                        </svg>
                        ${project.date || 'TBD'}
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--gray-600);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                            <circle cx="12" cy="10" r="3"/>
                        </svg>
                        ${project.location}
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--gray-600);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                            <circle cx="9" cy="7" r="4"/>
                        </svg>
                        ${project.current_participants}/${project.max_participants} registered
                    </div>
                </div>
                <button class="btn btn-primary" style="width: 100%;">View Details</button>
            </div>
        </div>
    `;
}

function renderRecentProjects(recentProjects) {
    const container = document.getElementById('recent-projects-container');
    if (!container) return;

    if (!recentProjects || recentProjects.length === 0) {
        container.innerHTML = '<p class="text-gray-500 text-center py-6">No projects created in the last 7 days.</p>';
        return;
    }

    container.innerHTML = recentProjects.map(project => renderRecentProjectCard(project)).join('');
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
                            <button class="btn btn-outline" style="color: #ef4444; border-color: #ef4444;" onclick="deleteProject(${project.id})">Delete</button>
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
    // Load all registrations for all projects
    try {
        // First get all projects for this organization
        const dashboardData = await fetchDashboardData();
        if (dashboardData.error) {
            throw new Error(dashboardData.error);
        }

        const projects = dashboardData.projects || [];
        const projectsWithRegistrations = [];

        // Load registrations for each project
        for (const project of projects) {
            try {
                const regResponse = await fetch(`/api/v1/projects/${project.id}/registrations`);
                if (regResponse.ok) {
                    const registrations = await regResponse.json();
                    projectsWithRegistrations.push({
                        project_id: project.id,
                        project_title: project.title,
                        project_status: project.status,
                        registrations: registrations.map(reg => ({
                            id: reg.id,
                            participant_name: reg.participant?.name || 'Unknown',
                            participant_email: reg.participant?.email || '',
                            registration_date: reg.created_at ? reg.created_at.split(' ')[0] : null,
                            status: reg.status
                        })),
                        total_registrations: registrations.length
                    });
                }
            } catch (err) {
                console.error(`Failed to load registrations for project ${project.id}:`, err);
            }
        }

        const data = { projects: projectsWithRegistrations };

        const container = document.querySelector('#registrations-tab');
        if (!container) return;

        if (!data.projects || data.projects.length === 0) {
            container.innerHTML = `
                <div class="mb-8">
                    <h2>Registration List</h2>
                    <p class="text-gray-600">View and manage project registrations</p>
                </div>
                <div class="card">
                    <div class="card-content">
                        <p class="text-gray-500 text-center py-6">No projects available.</p>
                    </div>
                </div>
            `;
            return;
        }

        // Render all projects with their registrations
        let html = `
            <div class="mb-8">
                <h2>Registration List</h2>
                <p class="text-gray-600">View and manage project registrations</p>
            </div>
        `;

        for (const projectData of data.projects) {
            const rowsHtml = projectData.registrations.map(reg => {
                const meta = getRegistrationStatusMeta(reg.status);
                let actions = '<span class="text-sm text-gray-400">No actions</span>';

                if (reg.status === 'registered') {
                    actions = `
                        <div class="flex gap-2">
                            <button class="btn btn-outline btn-sm" onclick="updateRegistrationStatus(${reg.id}, 'approved', ${projectData.project_id})">Approve</button>
                            <button class="btn btn-outline btn-sm" style="color: #ef4444;" onclick="updateRegistrationStatus(${reg.id}, 'rejected', ${projectData.project_id})">Decline</button>
                        </div>
                    `;
                } else if (reg.status === 'approved') {
                    actions = `
                        <div class="flex gap-2">
                            <button class="btn btn-primary btn-sm" onclick="confirmCompletion(${reg.id}, ${projectData.project_id})">Confirm Completion</button>
                            <button class="btn btn-outline btn-sm" style="color: #ef4444;" onclick="markAsNotCompleted(${reg.id}, ${projectData.project_id})">Not Completed</button>
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

            const isCompleted = projectData.project_status === 'completed';
            const hasApprovedRegistrations = projectData.registrations.some(reg => reg.status === 'approved');
            const canComplete = !isCompleted && hasApprovedRegistrations;

            html += `
                <div class="card mb-6" id="project-registrations-${projectData.project_id}">
                    <div class="card-header">
                        <div class="flex items-center justify-between">
                            <div>
                                <h3 style="margin: 0;">${projectData.project_title}</h3>
                                <p class="text-sm text-gray-600 mt-1">${projectData.total_registrations} registration${projectData.total_registrations !== 1 ? 's' : ''}</p>
                            </div>
                            ${isCompleted ?
                    '<span class="badge badge-success">Completed</span>' :
                    canComplete ?
                        `<button class="btn btn-primary btn-sm" onclick="completeProject(${projectData.project_id})">Complete Project</button>` :
                        ''
                }
                        </div>
                    </div>
                    <div class="card-content">
                        ${projectData.registrations.length > 0 ? `
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
                </div>
            `;
        }

        container.innerHTML = html;
    } catch (error) {
        console.error(error);
        const container = document.querySelector('#registrations-tab');
        if (container) {
            container.innerHTML = `
                <div class="mb-8">
                    <h2>Registration List</h2>
                    <p class="text-gray-600">View and manage project registrations</p>
                </div>
                <div class="card">
                    <div class="card-content">
                        <p class="text-gray-500 text-center py-6">Failed to load registrations. Please try again later.</p>
                    </div>
                </div>
            `;
        }
    }
}

async function loadProjectRegistrations(projectId) {
    currentRegistrationsProjectId = projectId;

    // Switch to registrations tab first
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelector('.nav-item[data-tab="registrations"]').classList.add('active');
    document.getElementById('registrations-tab').classList.add('active');

    // Load all registrations if not already loaded
    const registrationsTab = document.getElementById('registrations-tab');
    const needsLoad = !registrationsTab ||
        registrationsTab.innerHTML.trim() === '' ||
        registrationsTab.innerHTML.includes('Content will be dynamically loaded') ||
        !document.getElementById(`project-registrations-${projectId}`);

    if (needsLoad) {
        await loadRegistrations();
    }

    // Function to scroll and highlight
    const scrollToProject = () => {
        const projectCard = document.getElementById(`project-registrations-${projectId}`);
        if (projectCard) {
            // Remove any previous highlight
            document.querySelectorAll('.card.mb-6').forEach(card => {
                card.style.border = '';
                card.style.boxShadow = '';
            });

            // Highlight the target project card
            projectCard.style.border = '2px solid var(--secondary-blue)';
            projectCard.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';

            // Scroll to the project card
            projectCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

            // Remove highlight after 3 seconds
            setTimeout(() => {
                projectCard.style.border = '';
                projectCard.style.boxShadow = '';
            }, 3000);
        }
    };

    // Wait for DOM to update if we just loaded
    if (needsLoad) {
        setTimeout(scrollToProject, 100);
    } else {
        // If already loaded, scroll immediately
        scrollToProject();
    }
}

async function updateRegistrationStatus(registrationId, status, projectId = null) {
    const actionLabel = status === 'approved' ? 'approve' : status === 'cancelled' ? 'decline' : 'update';
    try {
        const response = await fetch(`/api/v1/registrations/${registrationId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || `Unable to ${actionLabel} registration.`);
        }

        // Check if project was auto-completed
        if (result.project_auto_completed) {
            await Modal.success(result.message || 'Project has been automatically marked as completed since all participants are finalized.');
        }

        // Reload all registrations if we're on the registrations tab
        const registrationsTab = document.getElementById('registrations-tab');
        if (registrationsTab && registrationsTab.classList.contains('active')) {
            await loadRegistrations();
        } else if (projectId) {
            loadProjectRegistrations(projectId);
        }
        loadProjects();
    } catch (error) {
        console.error(error);
        await Modal.error(error.message || 'Unable to update registration status.');
    }
}

async function confirmCompletion(registrationId, projectId = null) {
    const confirmed = await Modal.confirm(
        'Confirm that this participant has completed the project? This will create a volunteer record for admin review.',
        { title: 'Confirm Completion', confirmText: 'Confirm', cancelText: 'Cancel' }
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/registrations/${registrationId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'completed' })
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Unable to confirm completion.');
        }

        // Check if project was auto-completed
        if (result.project_auto_completed) {
            await Modal.success('Participant completion confirmed! A volunteer record has been created. ' + (result.message || 'Project has been automatically marked as completed since all participants are finalized.'));
        } else {
            await Modal.success('Participant completion confirmed! A volunteer record has been created and sent to admin for review.');
        }

        // Reload all registrations if we're on the registrations tab
        const registrationsTab = document.getElementById('registrations-tab');
        if (registrationsTab && registrationsTab.classList.contains('active')) {
            await loadRegistrations();
        } else if (projectId) {
            loadProjectRegistrations(projectId);
        }
        loadProjects();
    } catch (error) {
        console.error(error);
        await Modal.error(error.message || 'Unable to confirm completion.');
    }
}

async function completeProject(projectId) {
    const confirmed = await Modal.confirm(
        'Mark this project as completed? Only participants who have been confirmed as completed will receive volunteer records. All other participants will be marked as not completed.',
        { title: 'Complete Project', type: 'warning', confirmText: 'Complete Project', cancelText: 'Cancel' }
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/projects/${projectId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'completed' })
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Unable to complete project.');
        }
        await Modal.success(result.message || 'Project marked as completed successfully.');
        // Always reload registrations to show updated status
        await loadRegistrations();
        // Also reload projects list
        loadProjects();
    } catch (error) {
        console.error(error);
        await Modal.error(error.message || 'Unable to complete project.');
    }
}

async function markAsNotCompleted(registrationId, projectId = null) {
    const confirmed = await Modal.confirm(
        'Mark this participant as not completed? They will not receive volunteer records for this project.',
        { title: 'Mark as Not Completed', type: 'warning', confirmText: 'Mark Not Completed', cancelText: 'Cancel' }
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/registrations/${registrationId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: 'cancelled' })
        });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Unable to mark as not completed.');
        }

        // Check if project was auto-completed
        if (result.project_auto_completed) {
            await Modal.success('Participant marked as not completed. ' + (result.message || 'Project has been automatically marked as completed since all participants are finalized.'));
        } else {
            await Modal.success('Participant marked as not completed.');
        }

        // Reload all registrations if we're on the registrations tab
        const registrationsTab = document.getElementById('registrations-tab');
        if (registrationsTab && registrationsTab.classList.contains('active')) {
            await loadRegistrations();
        } else if (projectId) {
            loadProjectRegistrations(projectId);
        }
        loadProjects();
    } catch (error) {
        console.error(error);
        await Modal.error(error.message || 'Unable to mark as not completed.');
    }
}

// Display name editing functionality
let originalDisplayName = '';

function initDisplayNameEditor() {
    const editBtn = document.getElementById('edit-display-name-btn');
    const saveBtn = document.getElementById('save-display-name-btn');
    const cancelBtn = document.getElementById('cancel-display-name-btn');
    const input = document.getElementById('display-name-input');
    const messageEl = document.getElementById('display-name-message');

    if (!editBtn || !saveBtn || !cancelBtn || !input) return;

    // Get current user ID from the page (we'll need to fetch it)
    let currentUserId = null;

    // Fetch current user info to get user ID
    fetch('/api/v1/users/me')
        .then(res => res.json())
        .then(user => {
            currentUserId = user.id;
            originalDisplayName = user.display_name || '';
            if (input && !input.value && originalDisplayName) {
                input.value = originalDisplayName;
            }
        })
        .catch(err => console.error('Failed to fetch user info:', err));

    editBtn.addEventListener('click', function () {
        originalDisplayName = input.value;
        input.disabled = false;
        input.style.backgroundColor = 'white';
        input.style.borderColor = 'var(--secondary-blue)';
        input.focus();
        editBtn.style.display = 'none';
        saveBtn.style.display = 'inline-flex';
        cancelBtn.style.display = 'inline-flex';
        messageEl.style.display = 'none';
    });

    cancelBtn.addEventListener('click', function () {
        input.value = originalDisplayName;
        input.disabled = true;
        input.style.backgroundColor = 'var(--gray-100)';
        input.style.borderColor = 'var(--gray-300)';
        editBtn.style.display = 'inline-flex';
        saveBtn.style.display = 'none';
        cancelBtn.style.display = 'none';
        messageEl.style.display = 'none';
    });

    saveBtn.addEventListener('click', async function () {
        const newDisplayName = input.value.trim();

        if (!currentUserId) {
            showMessage('Error: User ID not found. Please refresh the page.', 'error');
            return;
        }

        // Disable buttons during save
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        try {
            const response = await fetch(`/api/v1/users/${currentUserId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    display_name: newDisplayName || null
                })
            });

            if (response.ok) {
                const result = await response.json();
                originalDisplayName = newDisplayName;
                input.disabled = true;
                input.style.backgroundColor = 'var(--gray-100)';
                input.style.borderColor = 'var(--gray-300)';
                editBtn.style.display = 'inline-flex';
                saveBtn.style.display = 'none';
                cancelBtn.style.display = 'none';
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';

                showMessage('Organization name updated successfully!', 'success');

                // Update sidebar display
                const sidebarUsername = document.getElementById('sidebar-username');
                if (sidebarUsername) {
                    sidebarUsername.textContent = newDisplayName || document.querySelector('#display-name-input').placeholder;
                }
            } else {
                const error = await response.json();
                showMessage(error.error || 'Failed to update organization name', 'error');
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';
            }
        } catch (error) {
            console.error('Error updating organization name:', error);
            showMessage('Failed to update organization name. Please try again.', 'error');
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save';
        }
    });

    function showMessage(text, type) {
        const messageEl = document.getElementById('display-name-message');
        if (!messageEl) return;

        messageEl.textContent = text;
        messageEl.style.display = 'block';
        messageEl.style.color = type === 'success' ? 'var(--secondary-blue)' : 'var(--accent-orange)';

        if (type === 'success') {
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 3000);
        }
    }

    // Allow Enter key to save
    input.addEventListener('keypress', function (e) {
        if (e.key === 'Enter' && !input.disabled) {
            saveBtn.click();
        }
    });
}

// Description editing functionality
let originalDescription = '';

function initDescriptionEditor() {
    const editBtn = document.getElementById('edit-description-btn');
    const saveBtn = document.getElementById('save-description-btn');
    const cancelBtn = document.getElementById('cancel-description-btn');
    const textarea = document.getElementById('description-input');
    const messageEl = document.getElementById('description-message');
    const charCountEl = document.getElementById('description-char-count');

    if (!editBtn || !saveBtn || !cancelBtn || !textarea) return;

    // Get current user ID
    let currentUserId = null;

    // Fetch current user info to get user ID and description
    fetch('/api/v1/users/me')
        .then(res => res.json())
        .then(user => {
            currentUserId = user.id;
            originalDescription = user.description || '';
            if (textarea && !textarea.value && originalDescription) {
                textarea.value = originalDescription;
            }
            updateCharCount(textarea, charCountEl);
        })
        .catch(err => console.error('Failed to fetch user info:', err));

    // Update character count
    function updateCharCount(element, countEl) {
        if (countEl) {
            countEl.textContent = (element.value || '').length;
        }
    }

    // Character count update on input
    textarea.addEventListener('input', function () {
        updateCharCount(textarea, charCountEl);
    });

    editBtn.addEventListener('click', function () {
        originalDescription = textarea.value;
        textarea.disabled = false;
        textarea.style.backgroundColor = 'white';
        textarea.style.borderColor = 'var(--secondary-blue)';
        textarea.focus();
        editBtn.style.display = 'none';
        saveBtn.style.display = 'inline-flex';
        cancelBtn.style.display = 'inline-flex';
        messageEl.style.display = 'none';
    });

    cancelBtn.addEventListener('click', function () {
        textarea.value = originalDescription;
        textarea.disabled = true;
        textarea.style.backgroundColor = 'var(--gray-100)';
        textarea.style.borderColor = 'var(--gray-300)';
        editBtn.style.display = 'inline-flex';
        saveBtn.style.display = 'none';
        cancelBtn.style.display = 'none';
        messageEl.style.display = 'none';
        updateCharCount(textarea, charCountEl);
    });

    saveBtn.addEventListener('click', async function () {
        const newDescription = textarea.value.trim();

        if (!currentUserId) {
            showDescriptionMessage('Error: User ID not found. Please refresh the page.', 'error');
            return;
        }

        // Disable buttons during save
        saveBtn.disabled = true;
        saveBtn.textContent = 'Saving...';

        try {
            const response = await fetch(`/api/v1/users/${currentUserId}`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    description: newDescription || null
                })
            });

            if (response.ok) {
                const result = await response.json();
                originalDescription = newDescription;
                textarea.disabled = true;
                textarea.style.backgroundColor = 'var(--gray-100)';
                textarea.style.borderColor = 'var(--gray-300)';
                editBtn.style.display = 'inline-flex';
                saveBtn.style.display = 'none';
                cancelBtn.style.display = 'none';
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';

                showDescriptionMessage('Organization description updated successfully!', 'success');
            } else {
                const error = await response.json();
                showDescriptionMessage(error.error || 'Failed to update organization description', 'error');
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';
            }
        } catch (error) {
            console.error('Error updating organization description:', error);
            showDescriptionMessage('Failed to update organization description. Please try again.', 'error');
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save';
        }
    });

    function showDescriptionMessage(text, type) {
        if (!messageEl) return;

        messageEl.textContent = text;
        messageEl.style.display = 'block';
        messageEl.style.color = type === 'success' ? 'var(--secondary-blue)' : 'var(--accent-orange)';

        if (type === 'success') {
            setTimeout(() => {
                messageEl.style.display = 'none';
            }, 3000);
        }
    }
}

// Delete project functionality
async function deleteProject(projectId) {
    const confirmed = await Modal.confirm(
        'Are you sure you want to DELETE this project? This will permanently remove:\n• All comments and replies\n• All registrations\n• All volunteer records\n\nThis action cannot be undone.',
        { type: 'warning', confirmText: 'Delete Project', cancelText: 'Cancel' }
    );
    
    if (!confirmed) return;
    
    try {
        const response = await fetch(`/api/v1/projects/${projectId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            await Modal.success('Project deleted successfully.');
            loadProjects();
            // Reload dashboard data to update statistics
            fetchDashboardData().then(data => {
                if (!data.error && data.statistics) {
                    updateStatistics(data.statistics);
                }
            });
        } else {
            const error = await response.json();
            await Modal.error(error.error || 'Failed to delete project.');
        }
    } catch (error) {
        console.error('Error deleting project:', error);
        await Modal.error('Failed to delete project. Please try again.');
    }
}

// Delete account functionality
function initDeleteAccountButton() {
    const deleteBtn = document.getElementById('delete-account-btn');
    if (!deleteBtn) return;

    deleteBtn.addEventListener('click', async function () {
        const confirmText = 'DELETE';

        const userInput = await Modal.prompt(
            `WARNING: This action is irreversible!\n\nDeleting your account will permanently remove:\n• All your information\n\n⚠️ IMPORTANT: You must delete all your projects first before deleting your account.\n\nType "${confirmText}" to confirm deletion:`,
            { title: 'Delete Account', placeholder: 'Type DELETE to confirm' }
        );

        if (userInput !== confirmText) {
            if (userInput !== null) {
                await Modal.warning('Account deletion cancelled. Text did not match.');
            }
            return;
        }

        deleteBtn.disabled = true;
        deleteBtn.textContent = 'Deleting...';

        try {
            const response = await fetch('/api/v1/users/me', {
                method: 'DELETE'
            });

            if (response.ok) {
                await Modal.success('Your account has been deleted successfully.');
                window.location.href = '/';
            } else {
                const error = await response.json();
                await Modal.error(error.error || 'Failed to delete account.');
                deleteBtn.disabled = false;
                deleteBtn.textContent = 'Delete Account';
            }
        } catch (error) {
            console.error('Error deleting account:', error);
            await Modal.error('Failed to delete account. Please try again.');
            deleteBtn.disabled = false;
            deleteBtn.textContent = 'Delete Account';
        }
    });
}

// Handle project creation form
document.addEventListener('DOMContentLoaded', function () {
    // Initialize display name editor
    initDisplayNameEditor();
    
    // Initialize description editor
    initDescriptionEditor();
    
    // Initialize delete account button
    initDeleteAccountButton();

    // Load dashboard data
    fetchDashboardData().then(data => {
        if (!data.error && data.statistics) {
            updateStatistics(data.statistics);
        }
        if (!data.error && data.recent_projects) {
            renderRecentProjects(data.recent_projects);
        }
    });

    // Draft management functions
    const DRAFT_STORAGE_KEY = 'project_draft';

    /**
     * Save the current project publish form contents to localStorage.
     * This allows organizations to come back and restore unfinished drafts.
     */
    function saveDraft() {
        const form = document.querySelector('form[action="/api/create-project"]');
        if (!form) return;

        const draftData = {
            title: document.getElementById('project-title')?.value || '',
            category: document.getElementById('project-category')?.value || '',
            category_other: document.getElementById('project-category-other')?.value || '',
            description: document.getElementById('project-description')?.value || '',
            date: document.getElementById('project-date')?.value || '',
            location: document.getElementById('project-location')?.value || '',
            max_participants: document.getElementById('project-participants')?.value || '',
            duration: document.getElementById('project-duration')?.value || '',
            points: document.getElementById('project-points')?.value || '',
            requirements: document.getElementById('project-requirements')?.value || '',
            saved_at: new Date().toISOString()
        };

        localStorage.setItem(DRAFT_STORAGE_KEY, JSON.stringify(draftData));
        Modal.success('Draft saved successfully!');
    }

    /**
     * Load draft JSON from localStorage (if any).
     */
    function loadDraft() {
        const draftJson = localStorage.getItem(DRAFT_STORAGE_KEY);
        if (!draftJson) return null;

        try {
            return JSON.parse(draftJson);
        } catch (e) {
            console.error('Error parsing draft:', e);
            return null;
        }
    }

    function clearDraft() {
        localStorage.removeItem(DRAFT_STORAGE_KEY);
    }

    /**
     * Populate the publish form fields with previously saved draft data.
     */
    function restoreDraft(draftData) {
        if (!draftData) return;

        const titleEl = document.getElementById('project-title');
        const categoryEl = document.getElementById('project-category');
        const categoryOtherEl = document.getElementById('project-category-other');
        const descriptionEl = document.getElementById('project-description');
        const dateEl = document.getElementById('project-date');
        const locationEl = document.getElementById('project-location');
        const participantsEl = document.getElementById('project-participants');
        const durationEl = document.getElementById('project-duration');
        const pointsEl = document.getElementById('project-points');
        const requirementsEl = document.getElementById('project-requirements');

        if (titleEl) titleEl.value = draftData.title || '';
        if (descriptionEl) descriptionEl.value = draftData.description || '';
        if (dateEl) dateEl.value = draftData.date || '';
        if (locationEl) locationEl.value = draftData.location || '';
        if (participantsEl) participantsEl.value = draftData.max_participants || '';
        if (durationEl) durationEl.value = draftData.duration || '';
        if (pointsEl) pointsEl.value = draftData.points || '';
        if (requirementsEl) requirementsEl.value = draftData.requirements || '';

        // Handle category
        if (categoryEl) {
            if (draftData.category === 'other') {
                categoryEl.value = 'other';
                if (categoryOtherEl) {
                    categoryOtherEl.style.display = 'block';
                    categoryOtherEl.required = true;
                    categoryOtherEl.value = draftData.category_other || '';
                }
            } else {
                categoryEl.value = draftData.category || '';
                if (categoryOtherEl) {
                    categoryOtherEl.style.display = 'none';
                    categoryOtherEl.required = false;
                }
            }
        }
    }

    /**
     * When entering the publish tab, check if a meaningful draft exists and
     * prompt the user to restore or discard it using the custom Modal.
     */
    async function checkAndPromptDraft() {
        const draftData = loadDraft();
        if (!draftData) return;

        // Check if draft has meaningful content
        const hasContent = draftData.title || draftData.description || draftData.location;
        if (!hasContent) {
            clearDraft();
            return;
        }

        // Show prompt
        const savedDate = new Date(draftData.saved_at);
        const savedDateStr = savedDate.toLocaleString();

        const restore = await Modal.confirm(
            `You have a saved draft from ${savedDateStr}.\n\nWould you like to restore it?`,
            { title: 'Restore Draft', confirmText: 'Restore', cancelText: 'Discard' }
        );

        if (restore) {
            restoreDraft(draftData);
        } else {
            clearDraft();
        }
    }

    // Handle category "Other" option
    const categorySelect = document.getElementById('project-category');
    const categoryOtherInput = document.getElementById('project-category-other');

    if (categorySelect && categoryOtherInput) {
        // Initialize color based on current value
        if (categorySelect.value && categorySelect.value !== '') {
            categorySelect.style.color = 'var(--gray-700)';
        }

        categorySelect.addEventListener('change', function () {
            // Change color to normal when a category is selected, keep light color for hint
            if (this.value && this.value !== '') {
                this.style.color = 'var(--gray-700)';
            } else {
                this.style.color = 'var(--gray-400)';
            }

            if (this.value === 'other') {
                categoryOtherInput.style.display = 'block';
                categoryOtherInput.required = true;
            } else {
                categoryOtherInput.style.display = 'none';
                categoryOtherInput.required = false;
                categoryOtherInput.value = '';
            }
        });
    }

    // Handle Save Draft button
    const saveDraftBtn = document.getElementById('save-draft-btn');
    if (saveDraftBtn) {
        saveDraftBtn.addEventListener('click', function () {
            saveDraft();
        });
    }

    // Handle project creation form
    const createForm = document.querySelector('form[action="/api/create-project"]');
    if (createForm) {
        // helpers for field error UI
        /**
         * Remove previous field-level validation errors from the publish form.
         */
        function clearProjectFormErrors() {
            const publishTab = document.getElementById('publish-tab');
            if (!publishTab) return;
            publishTab.querySelectorAll('.form-group.input-error').forEach(g => g.classList.remove('input-error'));
            publishTab.querySelectorAll('.field-error-text').forEach(el => el.remove());
        }

        /**
         * Apply field-level validation errors returned by the backend
         * (Marshmallow `details` object) by highlighting the corresponding
         * inputs and injecting inline error text under each field.
         */
        function applyProjectFormErrors(details) {
            if (!details) return;
            const fieldIdMap = {
                title: 'project-title',
                description: 'project-description',
                category: 'project-category',
                date: 'project-date',
                location: 'project-location',
                max_participants: 'project-participants',
                duration: 'project-duration',
                points: 'project-points',
                requirements: 'project-requirements'
            };
            Object.keys(details).forEach(field => {
                const messages = details[field];
                const firstMsg = Array.isArray(messages) ? messages[0] : messages;
                const inputId = fieldIdMap[field];
                if (!inputId) return;
                const inputEl = document.getElementById(inputId);
                if (!inputEl) return;
                const group = inputEl.closest('.form-group');
                if (!group) return;
                group.classList.add('input-error');
                const msgEl = document.createElement('div');
                msgEl.className = 'field-error-text';
                msgEl.textContent = firstMsg;
                group.appendChild(msgEl);
            });
        }

        createForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            clearProjectFormErrors();

            const formData = new FormData(this);

            // If "other" is selected, use the custom input value
            const categorySelect = document.getElementById('project-category');
            const categoryOtherInput = document.getElementById('project-category-other');

            if (categorySelect && categorySelect.value === 'other' && categoryOtherInput) {
                const customCategory = categoryOtherInput.value.trim();
                if (!customCategory) {
                    await Modal.warning('Please specify the category when selecting "Other"');
                    return;
                }
                formData.set('category', customCategory);
                formData.delete('category_other');
            } else {
                formData.delete('category_other');
            }

            try {
                const response = await fetch('/api/v1/projects', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                if (response.ok || response.status === 201) {
                    // Clear draft on successful submission
                    clearDraft();
                    await Modal.success('Project submitted successfully! It will be reviewed by an administrator.');
                    this.reset();
                    // Reset category other input visibility
                    if (categoryOtherInput) {
                        categoryOtherInput.style.display = 'none';
                        categoryOtherInput.required = false;
                    }
                    loadProjects();
                } else {
                    if (result.details) {
                        applyProjectFormErrors(result.details);
                    }
                    await Modal.error('Error: ' + (result.error || 'Failed to create project'));
                }
            } catch (error) {
                console.error(error);
                await Modal.error('Error creating project. Please try again.');
            }
        });
    }

    // Check for draft when switching to publish tab
    document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
        item.addEventListener('click', function () {
            const tabName = this.getAttribute('data-tab');
            if (tabName === 'publish') {
                // Small delay to ensure form is visible
                setTimeout(() => {
                    checkAndPromptDraft();
                }, 100);
            }
        });
    });

    // Check for draft on initial page load if publish tab is active
    const publishTab = document.getElementById('publish-tab');
    if (publishTab && publishTab.classList.contains('active')) {
        setTimeout(() => {
            checkAndPromptDraft();
        }, 300);
    }
});
