/**
 * ReportAI Auth JavaScript
 * ================================
 * Authentication page functionality
 */

// =============================================================================
// PASSWORD VISIBILITY TOGGLE
// =============================================================================

function initPasswordToggle() {
    document.querySelectorAll('.password-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const input = toggle.parentElement.querySelector('input');
            const icon = toggle.querySelector('.toggle-icon');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                        <line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                `;
            } else {
                input.type = 'password';
                icon.innerHTML = `
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                    </svg>
                `;
            }
        });
    });
}

// =============================================================================
// FORM VALIDATION
// =============================================================================

function initFormValidation() {
    const forms = document.querySelectorAll('.auth-form');
    
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            // Basic validation
            let isValid = true;
            const errors = {};
            
            // Email validation
            if (data.email && !isValidEmail(data.email)) {
                errors.email = 'Por favor, introduce un email válido';
                isValid = false;
            }
            
            // Password validation (for register)
            if (data.password && data.password.length < 8) {
                errors.password = 'La contraseña debe tener al menos 8 caracteres';
                isValid = false;
            }
            
            // Password confirmation
            if (data.password_confirm && data.password !== data.password_confirm) {
                errors.password_confirm = 'Las contraseñas no coinciden';
                isValid = false;
            }
            
            // Agency name validation (for register)
            if (data.agency_name && data.agency_name.length < 2) {
                errors.agency_name = 'El nombre de la agencia es requerido';
                isValid = false;
            }
            
            // Show/clear errors
            clearFormErrors(form);
            if (!isValid) {
                showFormErrors(form, errors);
                return;
            }
            
            // Simulate form submission (mock)
            handleAuthSubmit(form, data);
        });
    });
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function clearFormErrors(form) {
    form.querySelectorAll('.form-error').forEach(el => el.remove());
    form.querySelectorAll('.form-input').forEach(input => {
        input.style.borderColor = '';
    });
}

function showFormErrors(form, errors) {
    Object.entries(errors).forEach(([field, message]) => {
        const input = form.querySelector(`[name="${field}"]`);
        if (input) {
            input.style.borderColor = 'var(--color-error)';
            const error = document.createElement('p');
            error.className = 'form-error';
            error.textContent = message;
            input.parentElement.appendChild(error);
        }
    });
}

// =============================================================================
// AUTH SUBMISSION (MOCK)
// =============================================================================

async function handleAuthSubmit(form, data) {
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    
    // Show loading state
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" class="animate-spin">
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="40 60" stroke-linecap="round"/>
        </svg>
        Procesando...
    `;
    
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Mock success - redirect based on form type
    const isRegister = form.classList.contains('register-form');
    
    if (isRegister) {
        // Redirect to onboarding integrations
        window.location.href = '/app/onboarding/integrations/';
    } else {
        // Redirect to dashboard
        window.location.href = '/app/';
    }
}

// =============================================================================
// ONBOARDING INTEGRATIONS
// =============================================================================

function initOnboardingIntegrations() {
    const integrationCards = document.querySelectorAll('.onboarding-integration-card');
    
    integrationCards.forEach(card => {
        card.addEventListener('click', async () => {
            // If already connected, do nothing
            if (card.classList.contains('connected')) return;
            
            // Simulate OAuth flow
            const platform = card.dataset.platform;
            await simulateOAuthConnect(card, platform);
        });
    });
}

async function simulateOAuthConnect(card, platform) {
    // Show connecting state
    const statusEl = card.querySelector('.onboarding-integration-status');
    const originalStatus = statusEl.textContent;
    statusEl.textContent = 'Conectando...';
    
    // Simulate OAuth delay
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Mark as connected
    card.classList.add('connected');
    statusEl.textContent = 'Conectado';
    
    // Update continue button if at least one is connected
    updateOnboardingContinueButton();
}

function updateOnboardingContinueButton() {
    const connectedCount = document.querySelectorAll('.onboarding-integration-card.connected').length;
    const continueBtn = document.querySelector('.onboarding-continue-btn');
    
    if (continueBtn) {
        if (connectedCount > 0) {
            continueBtn.classList.remove('btn-secondary');
            continueBtn.classList.add('btn-primary');
            continueBtn.textContent = `Continuar (${connectedCount} conectado${connectedCount > 1 ? 's' : ''})`;
        }
    }
}

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initPasswordToggle();
    initFormValidation();
    
    // Initialize onboarding if on that page
    if (document.querySelector('.onboarding-layout')) {
        initOnboardingIntegrations();
    }
});

// Add spin animation to CSS dynamically
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .animate-spin {
        animation: spin 1s linear infinite;
    }
`;
document.head.appendChild(style);
