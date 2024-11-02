class LoginManager {
    constructor() {
        this.modal = document.getElementById('loginModal');
        this.loginButton = document.getElementById('loginButton');
        this.loginForm = document.getElementById('loginForm');
        this.cancelButton = document.getElementById('cancelLogin');
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Show modal
        this.loginButton.addEventListener('click', () => this.showModal());
        
        // Hide modal
        this.cancelButton.addEventListener('click', () => this.hideModal());
        
        // Handle click outside modal
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.hideModal();
            }
        });
        
        // Handle form submission
        this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
    }

    showModal() {
        this.modal.classList.remove('hidden');
    }

    hideModal() {
        this.modal.classList.add('hidden');
        this.loginForm.reset();
    }

    async handleLogin(e) {
        e.preventDefault();
        const email = document.getElementById('email').value;
        
        try {
            // First, create or get user
            const userResponse = await fetch('/stories/api/auth/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCookie('csrftoken')
                },
                body: JSON.stringify({ email })
            });

            if (!userResponse.ok) {
                throw new Error('Failed to authenticate');
            }

            const userData = await userResponse.json();
            
            // Update UI
            this.hideModal();
            this.updateLoginButton(email);
            
            // Trigger page refresh to update state
            window.location.reload();

        } catch (error) {
            console.error('Login error:', error);
            alert('Failed to login. Please try again.');
        }
    }

    updateLoginButton(email) {
        this.loginButton.textContent = email;
        this.loginButton.disabled = true;
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
}

// Initialize login manager
document.addEventListener('DOMContentLoaded', () => {
    new LoginManager();
});
