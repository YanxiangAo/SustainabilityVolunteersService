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
                            <button class="btn btn-outline btn-sm" style="color: #ef4444;" onclick="updateRegistrationStatus(${reg.id}, 'cancelled', ${projectData.project_id})">Decline</button>
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
            alert(result.message || 'Project has been automatically marked as completed since all participants are finalized.');
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
        alert(error.message || 'Unable to update registration status.');
    }
}

async function confirmCompletion(registrationId, projectId = null) {
    if (!confirm('Confirm that this participant has completed the project? This will create a volunteer record for admin review.')) {
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
            alert('Participant completion confirmed! A volunteer record has been created. ' + (result.message || 'Project has been automatically marked as completed since all participants are finalized.'));
        } else {
            alert('Participant completion confirmed! A volunteer record has been created and sent to admin for review.');
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
        alert(error.message || 'Unable to confirm completion.');
    }
}

async function completeProject(projectId) {
    if (!confirm('Mark this project as completed? Only participants who have been confirmed as completed will receive volunteer records. All other participants will be marked as not completed.')) {
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
        alert(result.message || 'Project marked as completed successfully.');
        // Always reload registrations to show updated status
        await loadRegistrations();
        // Also reload projects list
        loadProjects();
    } catch (error) {
        console.error(error);
        alert(error.message || 'Unable to complete project.');
    }
}

async function markAsNotCompleted(registrationId, projectId = null) {
    if (!confirm('Mark this participant as not completed? They will not receive volunteer records for this project.')) {
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
            alert('Participant marked as not completed. ' + (result.message || 'Project has been automatically marked as completed since all participants are finalized.'));
        } else {
            alert('Participant marked as not completed.');
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
        alert(error.message || 'Unable to mark as not completed.');
    }
}

// Handle project creation form
document.addEventListener('DOMContentLoaded', function() {
    // Load dashboard data
    fetchDashboardData().then(data => {
        if (!data.error && data.statistics) {
            updateStatistics(data.statistics);
        }
        if (!data.error && data.recent_projects) {
            renderRecentProjects(data.recent_projects);
        }
    });
    
    // Handle project creation form
    const createForm = document.querySelector('form[action="/api/create-project"]');
    if (createForm) {
        createForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            try {
            const response = await fetch('/api/v1/projects', {
                method: 'POST',
                body: formData
            });
                
                const result = await response.json();
                if (response.ok || response.status === 201) {
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

