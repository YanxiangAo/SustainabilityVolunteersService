/**
 * home.js - Home Page Script
 * Handles the public home page functionality:
 * - Fetches and displays available volunteer projects
 * - Renders project cards with sustainability ratings
 * - Allows users to browse projects without logging in (B-level requirement)
 */

/**
 * Renders a sustainability rating display with stars
 * @param {number} rating - Rating value from 0-5
 * @returns {string} HTML string for the rating display
 */
/**
 * Renders a sustainability rating display with stars
 * @param {number} rating - Rating value from 0-5
 * @returns {string} HTML string for the rating display
 */
function renderRating(rating) {
    // Determine color class based on rating level
    const colorClass = rating < 3 ? 'rating-low' : rating < 4 ? 'rating-medium' : 'rating-high';
    // Badge class for the rating value
    const badgeClass = rating < 3 ? 'rating-badge-low' : rating < 4 ? 'rating-badge-medium' : 'rating-badge-high';

    // Generate star SVGs (filled or empty based on rating)
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
            <span class="rating-badge ${badgeClass}">${rating.toFixed(1)}</span>
        </div>
    `;
}

/**
 * Renders a project card with all project details
 * Clicking the card navigates to the project detail page
 * @param {Object} project - Project data object
 * @returns {string} HTML string for the project card
 */
function renderProjectCard(project) {
    return `
        <div class="card project-card" onclick="window.location.href='/project/${project.id}'">
            <div class="card-header">
                <div class="flex justify-between items-center mb-2">
                    <span class="badge badge-primary">${project.category}</span>
                    ${renderRating(project.rating)}
                </div>
                <h3 class="mb-2">${project.title}</h3>
                <p class="text-sm text-gray-600">${project.organization_name ?? ''}</p>
            </div>
            <div class="card-content">
                <div class="project-info-list">
                    <div class="project-info-item">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                            <line x1="16" y1="2" x2="16" y2="6"/>
                            <line x1="8" y1="2" x2="8" y2="6"/>
                            <line x1="3" y1="10" x2="21" y2="10"/>
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
                            <path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
                        </svg>
                        ${project.current_participants}/${project.max_participants} registered
                    </div>
                </div>
                <button class="btn btn-primary" style="width: 100%;">View Details</button>
            </div>
        </div>
    `;
}

async function fetchProjects() {
    try {
        const response = await fetch('/api/v1/projects?available=true');
        if (!response.ok) {
            throw new Error('Failed to load projects');
        }
        const projects = await response.json();
        // Transform response to match expected format
        return projects.map(p => ({
            ...p,
            organization_name: p.organization?.name || p.organization_name
        }));
    } catch (error) {
        console.error(error);
        return [];
    }
}

// Load projects on page load
document.addEventListener('DOMContentLoaded', function () {
    const projectsGrid = document.getElementById('projects-grid');
    if (projectsGrid) {
        fetchProjects().then(projects => {
            if (!projects.length) {
                projectsGrid.innerHTML = '<p class="text-gray-500 text-center py-8">No projects are available at the moment.</p>';
                return;
            }
            // Limit to maximum 4 featured projects
            const featuredProjects = projects.slice(0, 4);
            projectsGrid.innerHTML = featuredProjects.map(project => renderProjectCard(project)).join('');
        });
    }
});
