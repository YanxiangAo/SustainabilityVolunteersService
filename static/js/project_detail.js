/**
 * project_detail.js - Project Detail Page Script
 * Handles functionality for project detail page:
 * - Project registration
 * - Comment submission and replies
 * - Loading and displaying comments
 */

// Get project metadata embedded in the HTML container (id, permissions, etc.)
function getProjectData() {
    const container = document.getElementById('project-detail-container') || document.body;
    return {
        projectId: container.dataset.projectId ? parseInt(container.dataset.projectId) : null,
        canComment: container.dataset.canComment === 'true'
    };
}

// Register the current user for a project via the JSON API
async function registerForProject(projectId) {
    const btn = document.getElementById('register-btn');
    if (!btn) return;

    btn.disabled = true;
    btn.textContent = 'Registering...';

    try {
        const response = await fetch(`/api/v1/projects/${projectId}/registrations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        // Check if user is not authenticated
        if (response.status === 401) {
            // Redirect to login page
            window.location.href = '/login';
            return;
        }
        if (response.ok || response.status === 201) {
            await Modal.success('Successfully registered for this project!');
            btn.textContent = 'Registered';
            btn.disabled = true;
            btn.style.backgroundColor = '#dcfce7';
            btn.style.color = 'var(--primary-green)';
            // Reload page to update registration count
            setTimeout(() => window.location.reload(), 1000);
        } else {
            await Modal.error('Error: ' + (result.error || 'Failed to register'));
            btn.disabled = false;
            btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 0.5rem;"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>Register Now';
        }
    } catch (error) {
        console.error(error);
        await Modal.error('Error registering for project. Please try again.');
        btn.disabled = false;
        btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 0.5rem;"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>Register Now';
    }
}

// Submit a new top-level comment or a reply to an existing comment
async function submitComment(projectId, parentId = null) {
    const textarea = parentId ? document.getElementById(`reply-text-${parentId}`) : document.getElementById('comment-text');
    const submitBtn = parentId ? document.querySelector(`#reply-box-${parentId} .btn-primary`) : document.getElementById('submit-comment-btn');
    if (!textarea || !submitBtn) return;

    const comment = textarea.value.trim();
    if (!comment) {
        await Modal.warning('Please enter a comment.');
        return;
    }

    // Disable button during submission
    submitBtn.disabled = true;
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = 'Sending...';

    try {
        const requestBody = { comment: comment };
        if (parentId) {
            requestBody.parent_id = parentId;
        }

        const response = await fetch(`/api/v1/projects/${projectId}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const result = await response.json();

        // Check if user is not authenticated
        if (response.status === 401) {
            // Redirect to login page
            window.location.href = '/login';
            return;
        }

        if (response.ok || response.status === 201) {
            // Clear textarea
            textarea.value = '';
            
            if (parentId) {
                // Hide reply box
                hideReplyBox(parentId);
                // Add reply to the replies container
                addReplyToDOM(parentId, result);
            } else {
                // Add new comment to the list
                addCommentToDOM(result);

                // Show success message briefly
                const successMsg = document.createElement('div');
                successMsg.textContent = 'Comment posted successfully!';
                successMsg.style.cssText = 'background-color: #dcfce7; color: var(--primary-green); padding: 0.5rem 1rem; border-radius: var(--border-radius); margin-bottom: 1rem; font-size: 0.875rem;';
                const container = document.getElementById('comments-container');
                if (container) {
                    container.insertBefore(successMsg, container.firstChild);
                    setTimeout(() => successMsg.remove(), 3000);
                }
            }
        } else {
            await Modal.error('Error: ' + (result.error || 'Failed to submit comment'));
        }
    } catch (error) {
        console.error(error);
        await Modal.error('Error submitting comment. Please try again.');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalText;
    }
}

// Submit reply (wrapper for submitComment)
async function submitReply(projectId, parentId) {
    await submitComment(projectId, parentId);
}

// Show reply box
function showReplyBox(commentId) {
    const replyBox = document.getElementById(`reply-box-${commentId}`);
    if (replyBox) {
        replyBox.style.display = 'block';
        const textarea = document.getElementById(`reply-text-${commentId}`);
        if (textarea) {
            textarea.focus();
        }
    }
}

// Hide reply box
function hideReplyBox(commentId) {
    const replyBox = document.getElementById(`reply-box-${commentId}`);
    const textarea = document.getElementById(`reply-text-${commentId}`);
    if (replyBox) {
        replyBox.style.display = 'none';
    }
    if (textarea) {
        textarea.value = '';
    }
}

// Add comment to DOM
function addCommentToDOM(comment) {
    const container = document.getElementById('comments-container');
    if (!container) return;

    const projectData = getProjectData();
    const canComment = projectData.canComment;

    // Remove "no comments" message if exists
    const noCommentsMsg = container.querySelector('p.text-gray-500');
    if (noCommentsMsg) {
        noCommentsMsg.remove();
    }

    // Create comment element
    const commentDiv = document.createElement('div');
    commentDiv.className = 'comment-item';
    commentDiv.setAttribute('data-comment-id', comment.id);
    commentDiv.style.cssText = 'border-left: 4px solid #dcfce7; padding-left: 1rem; padding-top: 0.5rem; padding-bottom: 0.5rem;';

    const replyButtonHtml = canComment ? `
        <button class="btn-reply" onclick="showReplyBox(${comment.id})" 
            style="background: none; border: none; color: var(--primary-green); cursor: pointer; padding: 0.25rem 0.5rem; font-size: 0.875rem; text-decoration: underline;">
            Reply
        </button>
    ` : '';

    commentDiv.innerHTML = `
        <div class="flex items-center gap-2 mb-2">
            <span style="font-weight: 500;">${escapeHtml(comment.user_name || 'Unknown')}</span>
            <span class="badge badge-secondary text-xs">${escapeHtml(comment.user_type || 'User')}</span>
            <span class="text-xs text-gray-500">${escapeHtml(comment.created_at || 'Just now')}</span>
        </div>
        <p class="text-gray-700 mb-2" style="white-space: pre-wrap;">${escapeHtml(comment.comment || '')}</p>
        ${replyButtonHtml}
        <div id="reply-box-${comment.id}" style="display: none; margin-top: 0.5rem; margin-left: 1rem;">
            <textarea id="reply-text-${comment.id}" placeholder="Write your reply..." rows="2"
                style="width: 100%; padding: 0.5rem; border: 1px solid var(--gray-300); border-radius: var(--border-radius); margin-bottom: 0.5rem; font-size: 0.875rem;"></textarea>
            <div style="display: flex; gap: 0.5rem;">
                <button class="btn btn-primary" onclick="submitReply(${projectData.projectId}, ${comment.id})"
                    style="padding: 0.25rem 0.75rem; font-size: 0.875rem;">Send</button>
                <button class="btn" onclick="hideReplyBox(${comment.id})"
                    style="padding: 0.25rem 0.75rem; font-size: 0.875rem; background-color: #f3f4f6;">Cancel</button>
            </div>
        </div>
        <div id="replies-${comment.id}" class="replies-container" style="margin-left: 1rem; margin-top: 0.5rem;"></div>
    `;

    // Insert at the top
    container.insertBefore(commentDiv, container.firstChild);
}

// Add reply to DOM
function addReplyToDOM(parentId, reply) {
    const repliesContainer = document.getElementById(`replies-${parentId}`);
    if (!repliesContainer) return;

    const replyDiv = document.createElement('div');
    replyDiv.className = 'reply-item';
    replyDiv.style.cssText = 'border-left: 2px solid #e5e7eb; padding-left: 0.75rem; padding-top: 0.5rem; padding-bottom: 0.5rem; margin-bottom: 0.5rem;';

    replyDiv.innerHTML = `
        <div class="flex items-center gap-2 mb-1">
            <span style="font-weight: 500; font-size: 0.875rem;">${escapeHtml(reply.user_name || 'Unknown')}</span>
            <span class="badge badge-secondary text-xs" style="font-size: 0.75rem;">${escapeHtml(reply.user_type || 'User')}</span>
            <span class="text-xs text-gray-500">${escapeHtml(reply.created_at || 'Just now')}</span>
        </div>
        <p class="text-gray-700" style="white-space: pre-wrap; font-size: 0.875rem;">${escapeHtml(reply.comment || '')}</p>
    `;

    repliesContainer.appendChild(replyDiv);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load comments
async function loadComments(projectId) {
    try {
        const response = await fetch(`/api/v1/projects/${projectId}/comments`);
        if (!response.ok) {
            throw new Error('Failed to load comments');
        }
        const comments = await response.json();

        const container = document.getElementById('comments-container');
        if (!container) return;

        // Clear existing comments (keep the structure)
        container.innerHTML = '';

        if (comments.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No comments yet. Be the first to ask a question!</p>';
            return;
        }

        // Render comments with replies
        comments.forEach(comment => {
            addCommentToDOM(comment);
            // Render replies if any
            if (comment.replies && comment.replies.length > 0) {
                const repliesContainer = document.getElementById(`replies-${comment.id}`);
                if (repliesContainer) {
                    comment.replies.forEach(reply => {
                        addReplyToDOM(comment.id, reply);
                    });
                }
            }
        });
    } catch (error) {
        console.error('Error loading comments:', error);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function () {
    const projectData = getProjectData();
    
    if (projectData.projectId) {
        // Load comments
        loadComments(projectData.projectId);
        
        // Set up register button click handler if it exists
        const registerBtn = document.getElementById('register-btn');
        if (registerBtn && !registerBtn.disabled && registerBtn.onclick === null) {
            registerBtn.addEventListener('click', function() {
                registerForProject(projectData.projectId);
            });
        }
    }
});

// Make functions globally available for onclick handlers in HTML
window.registerForProject = registerForProject;
window.submitComment = submitComment;
window.submitReply = submitReply;
window.showReplyBox = showReplyBox;
window.hideReplyBox = hideReplyBox;
