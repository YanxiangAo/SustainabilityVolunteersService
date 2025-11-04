// Tab switching
document.querySelectorAll('.nav-item[data-tab]').forEach(item => {
    item.addEventListener('click', function() {
        const tabName = this.getAttribute('data-tab');
        
        // Remove active class from all nav items and tab contents
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Add active class to clicked item and corresponding content
        this.classList.add('active');
        document.getElementById(tabName + '-tab').classList.add('active');
    });
});

// Badge data
const badges = [
    { type: 'rising-star', name: 'Rising Star', earned: true, description: 'Complete first volunteer service' },
    { type: 'eco-pioneer', name: 'Eco Pioneer', earned: true, description: 'Complete 50 hours of environmental service' },
    { type: 'compassion', name: 'Compassion Ambassador', earned: false, description: 'Volunteer for 6 consecutive months' },
    { type: 'public-welfare', name: 'Public Welfare Expert', earned: false, description: 'Complete 100 hours of service' },
    { type: 'team-leader', name: 'Team Leader', earned: false, description: 'Organize 10 volunteer activities' }
];

// Render badges
function renderBadges() {
    const container = document.getElementById('badges-container');
    if (!container) return;
    
    container.innerHTML = badges.map(badge => {
        const earnedClass = badge.earned ? 'badge-earned' : 'badge-locked';
        const bgColor = badge.earned ? 
            (badge.type === 'eco-pioneer' ? '#dcfce7' : badge.type === 'rising-star' ? '#fef3c7' : '#f3f4f6') :
            '#f3f4f6';
        const color = badge.earned ?
            (badge.type === 'eco-pioneer' ? 'var(--primary-green)' : badge.type === 'rising-star' ? 'var(--accent-yellow)' : 'var(--gray-500)') :
            'var(--gray-400)';
        
        return `
            <div class="volunteer-badge ${earnedClass}" style="background-color: ${bgColor}; border-color: ${color}; color: ${color};">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    ${badge.type === 'eco-pioneer' ? '<path d="M12 2v20M2 12h20"/>' :
                      badge.type === 'rising-star' ? '<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>' :
                      '<circle cx="12" cy="8" r="7"/><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"/>'}
                </svg>
                <div style="text-align: center;">
                    <div style="font-weight: 500;">${badge.name}</div>
                    <div style="font-size: 0.75rem; margin-top: 0.25rem; opacity: 0.75;">${badge.description}</div>
                </div>
                ${!badge.earned ? '<div style="position: absolute; top: 0.5rem; right: 0.5rem; background-color: var(--gray-500); color: white; font-size: 0.75rem; padding: 0.125rem 0.5rem; border-radius: var(--border-radius);">Locked</div>' : ''}
            </div>
        `;
    }).join('');
}

// Sample project data
const projects = [
    {
        id: 5,
        title: "Beach Cleanup Action",
        organization: "Blue Ocean Protection",
        date: "2025-11-18",
        location: "Golden Coast",
        rating: 4.6,
        participants: 18,
        maxParticipants: 25
    },
    {
        id: 6,
        title: "Community Book Donation",
        organization: "Book Community Foundation",
        date: "2025-11-22",
        location: "Civic Center",
        rating: 4.3,
        participants: 6,
        maxParticipants: 12
    }
];

// Render rating
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

// Render project card
function renderProjectCard(project) {
    return `
        <div class="card project-card" onclick="window.location.href='/project/${project.id}'">
            <div class="card-header">
                <div class="flex justify-between items-center mb-2">
                    <h3 style="margin: 0; font-size: 1rem;">${project.title}</h3>
                    ${renderRating(project.rating)}
                </div>
                <p class="text-sm text-gray-600">${project.organization}</p>
            </div>
            <div class="card-content">
                <div style="display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem; font-size: 0.875rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; color: var(--gray-600);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                        </svg>
                        ${project.date}
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
                        ${project.participants}/${project.maxParticipants} registered
                    </div>
                </div>
                <button class="btn btn-primary" style="width: 100%;">Register Now</button>
            </div>
        </div>
    `;
}

// Render registrations
function renderRegistrations() {
    const container = document.getElementById('my-registrations');
    if (!container) return;
    
    const registrations = [
        { id: 1, title: "Community Waste Sorting Campaign", organization: "Green Earth Environmental", date: "2025-11-15", status: "Upcoming", progress: 0 },
        { id: 2, title: "Digital Skills Training for Seniors", organization: "Silver Age Mutual Aid", date: "2025-11-20", status: "In Progress", progress: 40 }
    ];
    
    container.innerHTML = registrations.map(reg => {
        const statusColor = reg.status === "In Progress" ? "var(--primary-green)" : "var(--gray-500)";
        return `
            <div class="card mb-4">
                <div class="card-content">
                    <div class="flex items-start justify-between">
                        <div style="flex: 1;">
                            <div class="flex items-center gap-3 mb-2">
                                <h3 style="margin: 0;">${reg.title}</h3>
                                <span class="badge" style="background-color: ${reg.status === "In Progress" ? "#dcfce7" : "#f3f4f6"}; color: ${statusColor};">${reg.status}</span>
                            </div>
                            <p class="text-sm text-gray-600 mb-4">${reg.organization}</p>
                            <div class="flex items-center gap-2 text-sm text-gray-600 mb-4">
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                                    <line x1="16" y1="2" x2="16" y2="6"/>
                                    <line x1="8" y1="2" x2="8" y2="6"/>
                                </svg>
                                ${reg.date}
                            </div>
                            ${reg.status === "In Progress" ? `
                                <div>
                                    <div class="flex justify-between text-sm mb-2">
                                        <span>Progress</span>
                                        <span>${reg.progress}%</span>
                                    </div>
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: ${reg.progress}%;"></div>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                        <button class="btn btn-outline" onclick="window.location.href='/project/${reg.id}'">View Details</button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// Load data on page load
document.addEventListener('DOMContentLoaded', function() {
    renderBadges();
    
    const recommendedContainer = document.getElementById('recommended-projects');
    if (recommendedContainer) {
        recommendedContainer.innerHTML = projects.map(project => renderProjectCard(project)).join('');
    }
    
    const browseContainer = document.getElementById('browse-projects');
    if (browseContainer) {
        browseContainer.innerHTML = projects.map(project => renderProjectCard(project)).join('');
    }
    
    renderRegistrations();
});
