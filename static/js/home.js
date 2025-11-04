// Sample project data
const projects = [
    {
        id: 1,
        title: "Community Waste Sorting Campaign",
        organization: "Green Earth Environmental",
        date: "2025-11-15",
        location: "Sunshine Community",
        participants: 15,
        maxParticipants: 20,
        rating: 4.8,
        category: "Environmental"
    },
    {
        id: 2,
        title: "Digital Skills Training for Seniors",
        organization: "Silver Age Mutual Aid",
        date: "2025-11-20",
        location: "City Library",
        participants: 8,
        maxParticipants: 10,
        rating: 4.5,
        category: "Education"
    },
    {
        id: 3,
        title: "Urban Greening Planting Project",
        organization: "Youth Volunteer Association",
        date: "2025-11-25",
        location: "City Park",
        participants: 25,
        maxParticipants: 30,
        rating: 4.9,
        category: "Environmental"
    },
    {
        id: 4,
        title: "Companion Program for Left-behind Children",
        organization: "Love Bridge Foundation",
        date: "2025-12-01",
        location: "Hope Elementary School",
        participants: 12,
        maxParticipants: 15,
        rating: 4.7,
        category: "Care"
    }
];

// Render sustainability rating
function renderRating(rating) {
    const colorClass = rating < 3 ? 'rating-low' : rating < 4 ? 'rating-medium' : 'rating-high';
    const bgColor = rating < 3 ? '#f3f4f6' : rating < 4 ? '#fef3c7' : '#dcfce7';
    
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
    
    return `
        <div class="sustainability-rating ${colorClass}">
            ${starsHTML}
            <span class="rating-badge" style="background-color: ${bgColor};">${rating.toFixed(1)}</span>
        </div>
    `;
}

// Render project card
function renderProjectCard(project) {
    return `
        <div class="card project-card" onclick="window.location.href='/project/${project.id}'">
            <div class="card-header">
                <div class="flex justify-between items-center mb-2">
                    <span class="badge badge-primary">${project.category}</span>
                    ${renderRating(project.rating)}
                </div>
                <h3 style="margin-bottom: 0.5rem;">${project.title}</h3>
                <p class="text-sm text-gray-600">${project.organization}</p>
            </div>
            <div class="card-content">
                <div style="display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1rem; font-size: 0.875rem; color: var(--gray-600);">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                            <line x1="3" y1="10" x2="21" y2="10"/>
                        </svg>
                        ${project.date}
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                            <circle cx="12" cy="10" r="3"/>
                        </svg>
                        ${project.location}
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>
                            <circle cx="9" cy="7" r="4"/>
                            <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
                        </svg>
                        ${project.participants}/${project.maxParticipants} registered
                    </div>
                </div>
                <button class="btn btn-primary" style="width: 100%;">View Details</button>
            </div>
        </div>
    `;
}

// Load projects on page load
document.addEventListener('DOMContentLoaded', function() {
    const projectsGrid = document.getElementById('projects-grid');
    if (projectsGrid) {
        projectsGrid.innerHTML = projects.map(project => renderProjectCard(project)).join('');
    }
});
