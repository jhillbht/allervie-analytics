/**
 * Authentication status management
 */

// Check authentication status when page loads
document.addEventListener('DOMContentLoaded', checkAuthStatus);

/**
 * Check if the user is authenticated
 */
async function checkAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        updateAuthUI(data);
        return data.authenticated;
    } catch (error) {
        console.error('Error checking auth status:', error);
        updateAuthUI({ authenticated: false, auth_url: '/auth/login' });
        return false;
    }
}

/**
 * Update the authentication UI based on status
 */
function updateAuthUI(data) {
    const container = document.getElementById('auth-status');
    
    if (data.authenticated) {
        container.innerHTML = `
            <div class="auth-status authenticated">
                <span>Authenticated ✓</span>
                <a href="/auth/logout" class="auth-button">Logout</a>
            </div>
        `;
    } else {
        container.innerHTML = `
            <div class="auth-status not-authenticated">
                <span>Not authenticated</span>
                <a href="${data.auth_url}" class="auth-button">Login with Google</a>
            </div>
        `;
    }
}