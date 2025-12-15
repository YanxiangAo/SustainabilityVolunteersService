/**
 * participant.js - Participant Dashboard Script
 * Handles functionality for volunteer participant users:
 * - Tab navigation between overview, browse projects, and registrations
 * - Dashboard stats loading from API
 * - Project browsing and registration
 * - Volunteer Journey gamification milestones (A-level innovation)
 */

// ============================================================
// Tab Navigation
// Switches between dashboard sections
// ============================================================
document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
    item.addEventListener('click', function () {
        const tabName = this.getAttribute('data-tab');

        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

        this.classList.add('active');
        document.getElementById(tabName + '-tab').classList.add('active');
    });
});

// ============================================================
// A-LEVEL INNOVATION: Gamification Milestone Journey
// Updates milestone cards and progress based on volunteer hours
// ============================================================
function updateMilestoneJourney(totalHours) {
    const milestones = [
        { id: 1, hours: 1, name: 'First Step' },
        { id: 2, hours: 10, name: 'Rising Star' },
        { id: 3, hours: 25, name: 'Eco Warrior' },
        { id: 4, hours: 50, name: 'Hero' },
        { id: 5, hours: 100, name: 'Legend' }
    ];

    let completedCount = 0;
    let currentMilestone = milestones[0];
    let nextMilestone = milestones[0];

    milestones.forEach(m => {
        const card = document.getElementById(`milestone-${m.id}`);
        if (!card) return;

        if (totalHours >= m.hours) {
            // Milestone achieved
            card.style.border = '2px solid #22c55e';
            card.style.opacity = '1';
            completedCount++;
            currentMilestone = m;
        } else {
            // Reset card style for unachieved milestones
            card.style.border = '';
            card.style.opacity = '0.5';
        }
    });

    // Find the next milestone to achieve
    if (completedCount < milestones.length) {
        nextMilestone = milestones[completedCount];
        // Highlight the next milestone
        const nextCard = document.getElementById(`milestone-${nextMilestone.id}`);
        if (nextCard) {
            nextCard.style.border = '2px solid var(--secondary-blue)';
            nextCard.style.opacity = '0.8';
        }
    }

    // Update level badge
    const levelBadge = document.getElementById('volunteer-level');
    if (levelBadge) {
        levelBadge.textContent = `Level ${completedCount + 1}`;
    }

    // Update progress bar (progress toward next milestone)
    const progressBar = document.getElementById('journey-progress');
    const journeyText = document.getElementById('journey-text');

    if (progressBar && journeyText) {
        if (completedCount >= milestones.length) {
            progressBar.style.width = '100%';
            journeyText.textContent = '🎉 Congratulations! You have achieved Legend status!';
        } else {
            const hoursToNext = nextMilestone.hours;
            const progress = Math.min((totalHours / hoursToNext) * 100, 100);
            progressBar.style.width = `${progress}%`;
            journeyText.textContent = `${totalHours.toFixed(1)}/${hoursToNext}h to unlock ${nextMilestone.name}`;
        }
    }
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

function renderProjectCard(project) {
    return `
        <div class="card project-card" onclick="window.location.href='/project/${project.id}'">
            <div class="card-header">
                <div class="flex justify-between items-center mb-2">
                    <h3 style="margin: 0; font-size: 1rem;">${project.title}</h3>
                    ${renderRating(project.rating)}
                </div>
                <p class="text-sm text-gray-600">${project.organization_name ?? ''}</p>
            </div>
            <div class="card-content">
                <div class="project-info-list">
                    <div class="project-info-item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                        </svg>
                        ${project.date}
                    </div>
                    <div class="project-info-item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                            <circle cx="12" cy="10" r="3"/>
                        </svg>
                        ${project.location}
                    </div>
                    <div class="project-info-item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                            <circle cx="9" cy="7" r="4"/>
                        </svg>
                        ${project.current_participants}/${project.max_participants} registered
                    </div>
                </div>
                <button class="btn btn-primary btn-full">Register Now</button>
            </div>
        </div>
    `;
}

function renderRegistrations(registrations) {
    const container = document.getElementById('my-registrations');
    if (!container) return;

    if (!registrations.length) {
        container.innerHTML = '<p class="text-gray-500 text-center py-6">You have not registered for any projects yet.</p>';
        return;
    }

    container.innerHTML = registrations.map(reg => {
        const activeStatuses = ["In Progress", "Approved", "Registered"];
        const cancellableStatuses = ["Registered", "Approved"];
        const isActive = activeStatuses.includes(reg.status);
        const canCancel = cancellableStatuses.includes(reg.status);
        const statusColor = isActive ? "var(--primary-green)" : "var(--gray-500)";
        const badgeBackground = isActive ? "#dcfce7" : "#f3f4f6";

        const cancelButton = canCancel ? `
            <button class="btn btn-outline" style="color: var(--accent-orange); border-color: var(--accent-orange);" 
                onclick="cancelRegistration(${reg.registration_id}, '${reg.title.replace(/'/g, "\\'")}')">
                Cancel Registration
            </button>
        ` : '';

        return `
            <div class="card mb-4">
                <div class="card-content">
                    <div class="flex items-start justify-between">
                        <div style="flex: 1;">
                            <div class="flex items-center gap-3 mb-2">
                                <h3 style="margin: 0;">${reg.title}</h3>
                                <span class="badge" style="background-color: ${badgeBackground}; color: ${statusColor};">${reg.status}</span>
                            </div>
                            <p class="text-sm text-gray-600 mb-4">${reg.organization_name ?? ''}</p>
                            <div class="flex items-center gap-2 text-sm text-gray-600 mb-4">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                                    <line x1="16" y1="2" x2="16" y2="6"/>
                                    <line x1="8" y1="2" x2="8" y2="6"/>
                                </svg>
                                ${reg.date}
                            </div>
                            <div>
                                <div class="flex justify-between text-sm mb-2">
                                    <span>Progress</span>
                                    <span>${reg.progress !== undefined ? reg.progress : 0}%</span>
                                </div>
                                <div class="progress-bar">
                                    <div class="progress-fill" style="width: ${reg.progress !== undefined ? reg.progress : 0}%;"></div>
                                </div>
                            </div>
                        </div>
                        <div style="display: flex; gap: 0.5rem; flex-direction: column; align-items: flex-end;">
                            <button class="btn btn-outline" onclick="window.location.href='/project/${reg.id}'">View Details</button>
                            ${cancelButton}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Cancel registration function
async function cancelRegistration(registrationId, projectTitle) {
    const confirmed = await Modal.confirm(
        `Are you sure you want to cancel your registration for "${projectTitle}"? This action cannot be undone.`,
        { title: 'Cancel Registration', type: 'warning', confirmText: 'Yes, Cancel', cancelText: 'Keep Registration' }
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/registrations/${registrationId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            await Modal.success('Registration cancelled successfully.');
            // Reload dashboard data
            location.reload();
        } else {
            const error = await response.json();
            await Modal.error(error.error || 'Failed to cancel registration.');
        }
    } catch (error) {
        console.error('Error cancelling registration:', error);
        await Modal.error('Failed to cancel registration. Please try again.');
    }
}

async function fetchDashboardData() {
    try {
        const response = await fetch('/api/v1/users/me/dashboard');
        if (response.status === 401) {
            return { error: 'Please log in as a participant to view dashboard data.' };
        }
        if (!response.ok) {
            throw new Error('Failed to load participant data');
        }
        return await response.json();
    } catch (error) {
        console.error(error);
        return { error: 'Unable to load participant data. Please try again later.' };
    }
}

async function loadAvailableProjects() {
    const browseContainer = document.getElementById('browse-projects');
    if (!browseContainer) return;

    try {
        const response = await fetch('/api/v1/projects?available=true');
        if (response.status === 401) {
            browseContainer.innerHTML = '<p class="text-gray-500 text-center py-6">Please log in to view available projects.</p>';
            return;
        }
        if (!response.ok) {
            throw new Error('Failed to load available projects');
        }
        const projects = await response.json();
        // Transform response to match expected format
        const transformedProjects = projects.map(p => ({
            ...p,
            organization_name: p.organization?.name || p.organization_name
        }));
        browseContainer.innerHTML = transformedProjects.length
            ? transformedProjects.map(project => renderProjectCard(project)).join('')
            : '<p class="text-gray-500 text-center py-6">No projects available to browse.</p>';
    } catch (error) {
        console.error(error);
        browseContainer.innerHTML = '<p class="text-gray-500 text-center py-6">Failed to load available projects. Please try again later.</p>';
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

                showMessage('Display name updated successfully!', 'success');

                // Update sidebar display
                const sidebarUsername = document.getElementById('sidebar-username');
                if (sidebarUsername) {
                    sidebarUsername.textContent = newDisplayName || document.querySelector('#display-name-input').placeholder;
                }
            } else {
                const error = await response.json();
                showMessage(error.error || 'Failed to update display name', 'error');
                saveBtn.disabled = false;
                saveBtn.textContent = 'Save';
            }
        } catch (error) {
            console.error('Error updating display name:', error);
            showMessage('Failed to update display name. Please try again.', 'error');
            saveBtn.disabled = false;
            saveBtn.textContent = 'Save';
        }
    });

    function showMessage(text, type) {
        const messageEl = document.getElementById('display-name-message');
        if (!messageEl) return;

        messageEl.textContent = text;
        messageEl.style.display = 'block';
        messageEl.style.color = type === 'success' ? 'var(--primary-green)' : 'var(--accent-orange)';

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

document.addEventListener('DOMContentLoaded', function () {
    // Initialize display name editor
    initDisplayNameEditor();

    // Initialize delete account button
    initDeleteAccountButton();

    fetchDashboardData().then(data => {
        if (data.error) {
            const dashboardContainers = [
                document.getElementById('browse-projects'),
                document.getElementById('my-registrations')
            ];
            dashboardContainers.forEach(container => {
                if (container) {
                    container.innerHTML = `<p class="text-gray-500 text-center py-6">${data.error}</p>`;
                }
            });
            return;
        }

        // Update statistics
        if (data.statistics) {
            const stats = data.statistics;
            const totalHoursEl = document.getElementById('stat-total-hours');
            const totalPointsEl = document.getElementById('stat-total-points');
            const completedEl = document.getElementById('stat-completed');
            const upcomingEl = document.getElementById('stat-upcoming');

            if (totalHoursEl) totalHoursEl.textContent = `${stats.total_hours || 0}h`;
            if (totalPointsEl) totalPointsEl.textContent = stats.total_points || 0;
            if (completedEl) completedEl.textContent = stats.completed || 0;
            if (upcomingEl) upcomingEl.textContent = stats.upcoming || 0;

            // A-LEVEL INNOVATION: Update gamification milestones
            updateMilestoneJourney(stats.total_hours || 0);
        }

        // Load available projects for the browse tab
        loadAvailableProjects();

        renderRegistrations(data.registrations || []);
    });
});

// Delete account functionality
function initDeleteAccountButton() {
    const deleteBtn = document.getElementById('delete-account-btn');
    if (!deleteBtn) return;

    deleteBtn.addEventListener('click', async function () {
        const confirmText = 'DELETE';

        const userInput = await Modal.prompt(
            `WARNING: This action is irreversible!\n\nDeleting your account will permanently remove:\n• All your registrations\n• All your volunteer records\n• All your comments\n\nType "${confirmText}" to confirm deletion:`,
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

