/**
 * ReportAI Dashboard JavaScript
 * ================================
 * Dashboard-specific functionality and charts
 */

// =============================================================================
// DASHBOARD INITIALIZATION
// =============================================================================

async function initDashboard() {
    await Promise.all([
        loadKPIs(),
        loadChart(),
        loadPendingReviews()
    ]);
}

// =============================================================================
// KPIs LOADING
// =============================================================================

async function loadKPIs() {
    const kpis = await DataService.get('kpis');
    if (!kpis) return;

    // Update KPI values with animation
    animateValue('kpi-reports', 0, kpis.totalReports, 1000);
    animateValue('kpi-time', 0, kpis.timeSaved, 1000, 'h');
    animateValue('kpi-clients', 0, kpis.activeClients, 1000);
    animateValue('kpi-efficiency', 0, kpis.deliveryEfficiency, 1000, '%');

    // Update trends
    updateTrend('trend-reports', kpis.totalReportsTrend);
    updateTrend('trend-time', kpis.timeSavedTrend);
    updateTrend('trend-clients', kpis.activeClientsTrend);
    updateTrend('trend-efficiency', kpis.deliveryEfficiencyTrend);
}

function animateValue(elementId, start, end, duration, suffix = '') {
    const element = document.getElementById(elementId);
    if (!element) return;

    const startTime = performance.now();
    const update = (currentTime) => {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease-out)
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.floor(start + (end - start) * easeOut);
        
        element.textContent = UI.formatNumber(current) + suffix;
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    };
    requestAnimationFrame(update);
}

function updateTrend(elementId, value) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const isPositive = value >= 0;
    element.className = `kpi-trend ${isPositive ? 'positive' : 'negative'}`;
    element.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="${isPositive ? 'M18 15l-6-6-6 6' : 'M6 9l6 6 6-6'}"/>
        </svg>
        ${Math.abs(value).toFixed(1)}%
    `;
}

// =============================================================================
// CHART RENDERING
// =============================================================================

async function loadChart() {
    const chartData = await DataService.get('chart-data');
    if (!chartData) return;

    renderChart(chartData);
}

function renderChart(data) {
    const canvas = document.getElementById('comparison-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;
    
    // Set canvas size
    const dpr = window.devicePixelRatio || 1;
    const rect = container.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    ctx.scale(dpr, dpr);

    const width = rect.width;
    const height = rect.height;
    const padding = { top: 20, right: 20, bottom: 40, left: 50 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Find max value for scaling
    const maxValue = Math.max(...data.manual, ...data.reportai);
    const scale = chartHeight / (maxValue * 1.1);

    // Draw grid lines
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartHeight / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();

        // Y-axis labels
        const value = Math.round(maxValue * 1.1 * (1 - i / 5));
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(value + 'h', padding.left - 10, y + 4);
    }

    // Calculate bar positions
    const barGroupWidth = chartWidth / data.labels.length;
    const barWidth = barGroupWidth * 0.3;
    const barGap = barGroupWidth * 0.1;

    // Draw bars with animation
    data.labels.forEach((label, i) => {
        const groupX = padding.left + barGroupWidth * i + barGroupWidth / 2;

        // Manual bar (red)
        const manualHeight = data.manual[i] * scale;
        ctx.fillStyle = '#ef4444';
        ctx.beginPath();
        ctx.roundRect(
            groupX - barWidth - barGap / 2,
            padding.top + chartHeight - manualHeight,
            barWidth,
            manualHeight,
            [4, 4, 0, 0]
        );
        ctx.fill();

        // ReportAI bar (blue)
        const reportaiHeight = data.reportai[i] * scale;
        ctx.fillStyle = '#0075ff';
        ctx.beginPath();
        ctx.roundRect(
            groupX + barGap / 2,
            padding.top + chartHeight - reportaiHeight,
            barWidth,
            reportaiHeight,
            [4, 4, 0, 0]
        );
        ctx.fill();

        // X-axis labels
        ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(label, groupX, height - padding.bottom + 20);
    });
}

// Handle window resize
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(async () => {
        const chartData = await DataService.get('chart-data');
        if (chartData) renderChart(chartData);
    }, 250);
});

// =============================================================================
// PENDING REVIEWS
// =============================================================================

async function loadPendingReviews() {
    const reviews = await DataService.get('pending-reviews');
    if (!reviews) return;

    const container = document.getElementById('pending-reviews-list');
    if (!container) return;

    container.innerHTML = reviews.map(review => `
        <a href="/app/reports/generate/?client=${review.id}" class="review-item">
            <div class="review-item-header">
                <span class="review-item-client">${review.clientName}</span>
                <span class="review-item-time">${review.generatedAt}</span>
            </div>
            <p class="review-item-preview">${review.preview}</p>
        </a>
    `).join('');
}

// =============================================================================
// INITIALIZE ON LOAD
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.dashboard-page')) {
        initDashboard();
    }
});
