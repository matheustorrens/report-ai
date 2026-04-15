/**
 * ReportAI App - Main JavaScript
 * ================================
 * Core functionality and mock data management
 */

// =============================================================================
// MOCK DATA CONFIGURATION
// =============================================================================

/**
 * Mock Data Toggle
 * Set to false when integrating with real APIs
 */
const REPORTAI_CONFIG = {
    useMockData: true,  // Toggle this to switch between mock and real data
    mockDelay: 500,     // Simulated API delay in milliseconds
    debug: true         // Enable console logging
};

// Export config for other modules
window.REPORTAI_CONFIG = REPORTAI_CONFIG;

// =============================================================================
// MOCK DATA STORE
// =============================================================================

const MockData = {
    // Agency Information
    agency: {
        id: 1,
        name: "Digital Growth Agency",
        email: "admin@digitalgrowth.com",
        createdAt: "2025-01-15"
    },

    // Dashboard KPIs
    kpis: {
        totalReports: 248,
        totalReportsTrend: 12.5,
        timeSaved: 186,  // hours
        timeSavedTrend: 23.4,
        activeClients: 24,
        activeClientsTrend: 8.3,
        deliveryEfficiency: 94.2,  // percentage
        deliveryEfficiencyTrend: 5.1
    },

    // Chart Data - Manual vs ReportAI comparison by week
    chartData: {
        labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4', 'Sem 5', 'Sem 6', 'Sem 7', 'Sem 8'],
        manual: [45, 52, 48, 61, 55, 58, 62, 70],  // hours
        reportai: [12, 14, 13, 16, 15, 15, 17, 18]  // hours
    },

    // Reports pending review
    pendingReviews: [
        {
            id: 1,
            clientName: "TechStartup Inc",
            preview: "Resumen mensual de campañas de Google Ads con incremento del 23% en conversiones...",
            generatedAt: "Hace 2 horas"
        },
        {
            id: 2,
            clientName: "Fashion Brand Co",
            preview: "Análisis de rendimiento Meta Ads Q1 2026 con comparativa YoY mostrando...",
            generatedAt: "Hace 5 horas"
        },
        {
            id: 3,
            clientName: "Local Restaurant",
            preview: "Reporte semanal de métricas GA4 con análisis de comportamiento de usuarios...",
            generatedAt: "Hace 1 día"
        }
    ],

    // Clients
    clients: [
        {
            id: 1,
            name: "TechStartup Inc",
            email: "marketing@techstartup.com",
            whatsapp: "+34 612 345 678",
            industry: "Tecnología",
            language: "es",
            technicalLevel: "avanzado",
            integrations: {
                googleAds: true,
                metaAds: true,
                ga4: true,
                linkedinAds: false
            },
            lastReport: "2026-04-12",
            status: "active"
        },
        {
            id: 2,
            name: "Fashion Brand Co",
            email: "digital@fashionbrand.com",
            whatsapp: "+34 623 456 789",
            industry: "Moda",
            language: "es",
            technicalLevel: "básico",
            integrations: {
                googleAds: false,
                metaAds: true,
                ga4: true,
                linkedinAds: false
            },
            lastReport: "2026-04-10",
            status: "active"
        },
        {
            id: 3,
            name: "Local Restaurant",
            email: "owner@localrestaurant.com",
            whatsapp: "+34 634 567 890",
            industry: "Hostelería",
            language: "es",
            technicalLevel: "básico",
            integrations: {
                googleAds: true,
                metaAds: true,
                ga4: false,
                linkedinAds: false
            },
            lastReport: "2026-04-08",
            status: "active"
        },
        {
            id: 4,
            name: "B2B Solutions Ltd",
            email: "marketing@b2bsolutions.com",
            whatsapp: "+34 645 678 901",
            industry: "B2B / SaaS",
            language: "en",
            technicalLevel: "avanzado",
            integrations: {
                googleAds: true,
                metaAds: false,
                ga4: true,
                linkedinAds: true
            },
            lastReport: "2026-04-05",
            status: "active"
        },
        {
            id: 5,
            name: "E-commerce Plus",
            email: "growth@ecommerceplus.com",
            whatsapp: "+34 656 789 012",
            industry: "E-commerce",
            language: "es",
            technicalLevel: "avanzado",
            integrations: {
                googleAds: true,
                metaAds: true,
                ga4: true,
                linkedinAds: false
            },
            lastReport: "2026-04-01",
            status: "active"
        }
    ],

    // Reports History
    reports: [
        {
            id: 1,
            name: "Reporte Mensual - Abril 2026",
            clientId: 1,
            clientName: "TechStartup Inc",
            date: "2026-04-12 14:30",
            channel: "email",
            status: "delivered",
            viewed: true
        },
        {
            id: 2,
            name: "Análisis Q1 2026",
            clientId: 2,
            clientName: "Fashion Brand Co",
            date: "2026-04-10 10:15",
            channel: "whatsapp",
            status: "delivered",
            viewed: true
        },
        {
            id: 3,
            name: "Reporte Semanal - Sem 15",
            clientId: 3,
            clientName: "Local Restaurant",
            date: "2026-04-08 16:45",
            channel: "both",
            status: "delivered",
            viewed: false
        },
        {
            id: 4,
            name: "Performance Review",
            clientId: 4,
            clientName: "B2B Solutions Ltd",
            date: "2026-04-05 09:00",
            channel: "email",
            status: "failed",
            viewed: false
        },
        {
            id: 5,
            name: "Reporte Mensual - Marzo 2026",
            clientId: 5,
            clientName: "E-commerce Plus",
            date: "2026-04-01 11:30",
            channel: "whatsapp",
            status: "delivered",
            viewed: true
        }
    ],

    // Integrations
    integrations: {
        googleAds: {
            name: "Google Ads",
            status: "connected",
            accountId: "123-456-7890",
            lastSync: "2026-04-14 08:00"
        },
        metaAds: {
            name: "Meta Ads",
            status: "connected",
            accountId: "act_1234567890",
            lastSync: "2026-04-14 08:15"
        },
        ga4: {
            name: "Google Analytics 4",
            status: "action_required",
            accountId: null,
            lastSync: null
        },
        linkedinAds: {
            name: "LinkedIn Ads",
            status: "disconnected",
            accountId: null,
            lastSync: null
        }
    }
};

// Export mock data for other modules
window.MockData = MockData;

// =============================================================================
// DATA SERVICE (Mock/Real API Abstraction)
// =============================================================================

class DataService {
    static async get(endpoint) {
        if (REPORTAI_CONFIG.useMockData) {
            return this._getMockData(endpoint);
        }
        // TODO: Implement real API calls
        return fetch(`/api/${endpoint}`).then(res => res.json());
    }

    static _getMockData(endpoint) {
        return new Promise((resolve) => {
            setTimeout(() => {
                const data = {
                    'kpis': MockData.kpis,
                    'chart-data': MockData.chartData,
                    'pending-reviews': MockData.pendingReviews,
                    'clients': MockData.clients,
                    'reports': MockData.reports,
                    'integrations': MockData.integrations,
                    'agency': MockData.agency
                };
                
                if (REPORTAI_CONFIG.debug) {
                    console.log(`[MockData] GET ${endpoint}:`, data[endpoint]);
                }
                
                resolve(data[endpoint] || null);
            }, REPORTAI_CONFIG.mockDelay);
        });
    }
}

window.DataService = DataService;

// =============================================================================
// UI UTILITIES
// =============================================================================

const UI = {
    // Show loading state
    showLoading(element) {
        element.classList.add('loading');
        element.innerHTML = `
            <div class="loading-spinner">
                <svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2" stroke-dasharray="40 60" stroke-linecap="round">
                        <animateTransform attributeName="transform" type="rotate" from="0 12 12" to="360 12 12" dur="1s" repeatCount="indefinite"/>
                    </circle>
                </svg>
            </div>
        `;
    },

    // Hide loading state
    hideLoading(element) {
        element.classList.remove('loading');
    },

    // Format number with thousands separator
    formatNumber(num) {
        return new Intl.NumberFormat('es-ES').format(num);
    },

    // Format percentage
    formatPercent(num) {
        return `${num.toFixed(1)}%`;
    },

    // Format date
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return new Intl.DateTimeFormat('es-ES', {
            day: '2-digit',
            month: 'short',
            year: 'numeric'
        }).format(date);
    },

    // Format datetime
    formatDateTime(dateStr) {
        const date = new Date(dateStr);
        return new Intl.DateTimeFormat('es-ES', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(date);
    },

    // Get status badge HTML
    getStatusBadge(status) {
        const statusMap = {
            'connected': { class: 'success', text: 'Conectado' },
            'disconnected': { class: 'neutral', text: 'Desconectado' },
            'action_required': { class: 'warning', text: 'Acción Necesaria' },
            'delivered': { class: 'success', text: 'Entregado' },
            'pending': { class: 'warning', text: 'Pendiente' },
            'failed': { class: 'error', text: 'Fallido' },
            'viewed': { class: 'info', text: 'Visto' },
            'active': { class: 'success', text: 'Activo' },
            'inactive': { class: 'neutral', text: 'Inactivo' }
        };
        
        const config = statusMap[status] || { class: 'neutral', text: status };
        return `<span class="status-badge ${config.class}">${config.text}</span>`;
    },

    // Show toast notification
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-message">${message}</span>
            <button class="toast-close">&times;</button>
        `;
        
        const container = document.querySelector('.toast-container') || this._createToastContainer();
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => toast.remove(), 5000);
        
        // Manual close
        toast.querySelector('.toast-close').addEventListener('click', () => toast.remove());
    },

    _createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    }
};

window.UI = UI;

// =============================================================================
// SIDEBAR NAVIGATION
// =============================================================================

function initSidebar() {
    const navItems = document.querySelectorAll('.sidebar-nav-item');
    const currentPath = window.location.pathname;
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        if (href && currentPath.includes(href) && href !== '/app/') {
            item.classList.add('active');
        } else if (href === '/app/' && currentPath === '/app/') {
            item.classList.add('active');
        }
    });
}

// =============================================================================
// MOBILE MENU TOGGLE
// =============================================================================

function initMobileMenu() {
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    const sidebar = document.querySelector('.app-sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }
}

// =============================================================================
// MODAL SYSTEM
// =============================================================================

const Modal = {
    open(modalId) {
        const overlay = document.getElementById(modalId);
        if (overlay) {
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    },
    
    close(modalId) {
        const overlay = document.getElementById(modalId);
        if (overlay) {
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    },
    
    init() {
        // Close button handlers
        document.querySelectorAll('.modal-close, [data-modal-close]').forEach(btn => {
            btn.addEventListener('click', () => {
                const modal = btn.closest('.modal-overlay');
                if (modal) {
                    modal.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
        });
        
        // Click outside to close
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    overlay.classList.remove('active');
                    document.body.style.overflow = '';
                }
            });
        });
        
        // Open modal buttons
        document.querySelectorAll('[data-modal-open]').forEach(btn => {
            btn.addEventListener('click', () => {
                const modalId = btn.getAttribute('data-modal-open');
                this.open(modalId);
            });
        });
    }
};

window.Modal = Modal;

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initMobileMenu();
    Modal.init();
    
    if (REPORTAI_CONFIG.debug) {
        console.log('[ReportAI] App initialized');
        console.log('[ReportAI] Mock data mode:', REPORTAI_CONFIG.useMockData);
    }
});
