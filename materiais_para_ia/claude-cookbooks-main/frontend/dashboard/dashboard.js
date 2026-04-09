/* ============================================
   NeuralForge — Command Center Interactions
   ============================================ */

// ===========================
// Utilities
// ===========================
const $ = (sel, ctx = document) => ctx.querySelector(sel);
const $$ = (sel, ctx = document) => [...ctx.querySelectorAll(sel)];
const random = (min, max) => Math.random() * (max - min) + min;

// ===========================
// 1. Clock
// ===========================
function initClock() {
    const el = $('#topbarTime');
    if (!el) return;
    const tick = () => {
        const now = new Date();
        el.textContent = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    };
    tick();
    setInterval(tick, 10000);
}

// ===========================
// 2. Greeting based on time
// ===========================
function initGreeting() {
    const h = new Date().getHours();
    const el = $('#greetingText');
    if (!el) return;
    if (h < 12) el.textContent = 'Bom dia, Matheus';
    else if (h < 18) el.textContent = 'Boa tarde, Matheus';
    else el.textContent = 'Boa noite, Matheus';
}

// ===========================
// 3. Counter Animation
// ===========================
function initCounters() {
    const els = $$('[data-counter]');
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (!entry.isIntersecting) return;
            animateCounter(entry.target);
            observer.unobserve(entry.target);
        });
    }, { threshold: 0.5 });

    els.forEach(el => observer.observe(el));
}

function animateCounter(el) {
    const target = parseFloat(el.dataset.counter);
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    const format = el.dataset.format;
    const decimals = parseInt(el.dataset.decimals) || 0;
    const duration = 1800;
    const start = performance.now();

    function update(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 4);
        const current = target * eased;
        
        let display;
        if (format === 'abbr') {
            if (current >= 1_000_000) display = (current / 1_000_000).toFixed(1) + 'M';
            else if (current >= 1_000) display = (current / 1_000).toFixed(1) + 'K';
            else display = Math.floor(current).toString();
        } else if (decimals > 0) {
            display = current.toFixed(decimals);
        } else {
            display = Math.floor(current).toLocaleString('pt-BR');
        }

        el.textContent = prefix + display + suffix;
        if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
}

// ===========================
// 4. Chart
// ===========================
function initChart() {
    const container = $('#chartBars');
    const xAxis = $('#chartXAxis');
    if (!container) return;

    const days = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom'];
    const values = [32400, 41200, 38700, 48100, 45300, 28900, 22600];
    const maxVal = Math.max(...values);

    container.innerHTML = '';
    xAxis.innerHTML = '';

    values.forEach((val, i) => {
        const pct = (val / 50000) * 100;
        const group = document.createElement('div');
        group.className = 'chart-bar-group';

        const bar = document.createElement('div');
        bar.className = 'chart-bar';
        bar.style.height = pct + '%';
        bar.style.setProperty('--delay', (i * 0.08) + 's');
        
        const tooltip = document.createElement('div');
        tooltip.className = 'bar-tooltip';
        tooltip.textContent = (val / 1000).toFixed(1) + 'K';
        bar.appendChild(tooltip);

        // Subtle color variation per day
        const hue = i === 3 ? '0' : '0'; // Keep consistent brand color
        const lightness = val === maxVal ? '1.1' : '1';
        if (val === maxVal) bar.style.background = 'linear-gradient(180deg, var(--accent-hover), rgba(232,168,56,0.4))';

        group.appendChild(bar);
        container.appendChild(group);

        const label = document.createElement('span');
        label.textContent = days[i];
        if (val === maxVal) label.style.color = 'var(--accent)';
        xAxis.appendChild(label);
    });

    // Draw a subtle trend line overlay
    drawTrendLine(values, 50000);
}

function drawTrendLine(values, maxVal) {
    const overlay = $('#chartLine');
    if (!overlay) return;
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('viewBox', '0 0 100 100');
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.style.width = '100%';
    svg.style.height = '100%';

    const points = values.map((v, i) => {
        const x = (i / (values.length - 1)) * 100;
        const y = 100 - (v / maxVal) * 100;
        return `${x},${y}`;
    });

    // Gradient area
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const grad = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
    grad.setAttribute('id', 'lineGrad');
    grad.setAttribute('x1', '0');
    grad.setAttribute('y1', '0');
    grad.setAttribute('x2', '0');
    grad.setAttribute('y2', '1');
    
    const stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop1.setAttribute('offset', '0%');
    stop1.setAttribute('stop-color', 'rgba(232,168,56,0.12)');
    const stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
    stop2.setAttribute('offset', '100%');
    stop2.setAttribute('stop-color', 'rgba(232,168,56,0)');
    grad.appendChild(stop1);
    grad.appendChild(stop2);
    defs.appendChild(grad);
    svg.appendChild(defs);

    // Area fill
    const area = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    const areaPoints = `0,100 ${points.join(' ')} 100,100`;
    area.setAttribute('points', areaPoints);
    area.setAttribute('fill', 'url(#lineGrad)');
    svg.appendChild(area);

    // Line
    const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    polyline.setAttribute('points', points.join(' '));
    polyline.setAttribute('fill', 'none');
    polyline.setAttribute('stroke', 'rgba(232,168,56,0.5)');
    polyline.setAttribute('stroke-width', '0.8');
    polyline.setAttribute('stroke-linejoin', 'round');
    polyline.setAttribute('stroke-linecap', 'round');
    svg.appendChild(polyline);

    // Dots on points
    values.forEach((v, i) => {
        const cx = (i / (values.length - 1)) * 100;
        const cy = 100 - (v / maxVal) * 100;
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', cx);
        circle.setAttribute('cy', cy);
        circle.setAttribute('r', '1.2');
        circle.setAttribute('fill', 'var(--accent)');
        circle.setAttribute('opacity', '0.7');
        svg.appendChild(circle);
    });

    overlay.innerHTML = '';
    overlay.appendChild(svg);
}

// ===========================
// 5. Sparklines
// ===========================
function initSparklines() {
    const sparks = $$('.metric-spark');
    sparks.forEach(el => {
        const canvas = document.createElement('canvas');
        el.appendChild(canvas);
        drawSparkline(canvas, el.dataset.spark);
    });
}

function drawSparkline(canvas, type) {
    const ctx = canvas.getContext('2d');
    const rect = canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    ctx.scale(dpr, dpr);

    const W = rect.width;
    const H = rect.height;
    const points = 20;
    let data = [];

    // Generate different patterns per type
    switch (type) {
        case 'requests':
            data = Array.from({ length: points }, (_, i) => 30 + Math.sin(i * 0.4) * 15 + random(-5, 5) + i * 1.5);
            break;
        case 'tokens':
            data = Array.from({ length: points }, (_, i) => 20 + Math.cos(i * 0.3) * 10 + random(-3, 8) + i * 1.2);
            break;
        case 'latency':
            data = Array.from({ length: points }, (_, i) => 50 - Math.sin(i * 0.5) * 12 + random(-4, 4) - i * 0.8);
            break;
        case 'cost':
            data = Array.from({ length: points }, (_, i) => 30 + Math.sin(i * 0.2) * 8 + random(-2, 6));
            break;
        default:
            data = Array.from({ length: points }, () => random(20, 60));
    }

    const maxV = Math.max(...data);
    const minV = Math.min(...data);
    const range = maxV - minV || 1;

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, H);
    gradient.addColorStop(0, 'rgba(232, 168, 56, 0.15)');
    gradient.addColorStop(1, 'rgba(232, 168, 56, 0)');

    ctx.beginPath();
    ctx.moveTo(0, H);

    data.forEach((v, i) => {
        const x = (i / (points - 1)) * W;
        const y = H - ((v - minV) / range) * (H - 4) - 2;
        if (i === 0) ctx.lineTo(x, y);
        else {
            // Smooth curve
            const prevX = ((i - 1) / (points - 1)) * W;
            const prevY = H - ((data[i - 1] - minV) / range) * (H - 4) - 2;
            const cpX = (prevX + x) / 2;
            ctx.bezierCurveTo(cpX, prevY, cpX, y, x, y);
        }
    });

    ctx.lineTo(W, H);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Line
    ctx.beginPath();
    data.forEach((v, i) => {
        const x = (i / (points - 1)) * W;
        const y = H - ((v - minV) / range) * (H - 4) - 2;
        if (i === 0) ctx.moveTo(x, y);
        else {
            const prevX = ((i - 1) / (points - 1)) * W;
            const prevY = H - ((data[i - 1] - minV) / range) * (H - 4) - 2;
            const cpX = (prevX + x) / 2;
            ctx.bezierCurveTo(cpX, prevY, cpX, y, x, y);
        }
    });
    ctx.strokeStyle = 'rgba(232, 168, 56, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // End dot
    const lastX = W;
    const lastY = H - ((data[data.length - 1] - minV) / range) * (H - 4) - 2;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = 'var(--accent)';
    ctx.fill();
}

// ===========================
// 6. Live Activity Feed
// ===========================
const feedPool = [
    { icon: '✓', type: 'success', msg: '<strong>Research Agent</strong> completou análise de mercado — 23 fontes consultadas' },
    { icon: '⚡', type: 'info', msg: '<strong>Chief of Staff</strong> agendou 3 reuniões e notificou a equipe' },
    { icon: '!', type: 'warning', msg: '<strong>SRE Agent</strong> detectou latência elevada no endpoint /api/v2/chat' },
    { icon: '✓', type: 'success', msg: 'Batch de <strong>2.400 classificações</strong> concluído com 99.2% de precisão' },
    { icon: '◈', type: 'info', msg: '<strong>Observability Agent</strong> gerou alerta de uso de CPU > 80%' },
    { icon: '✓', type: 'success', msg: 'Prompt Cache hit rate alcançou <strong>87.3%</strong> — economia de R$12.40 na hora' },
    { icon: '!', type: 'warning', msg: 'Rate limit atingido para API Key <strong>sk-***8f2a</strong> — 429 retornado' },
    { icon: '✓', type: 'success', msg: '<strong>Research Agent</strong> gerou relatório executivo Q1 — 14 páginas' },
    { icon: '✗', type: 'error', msg: 'Falha no deploy <strong>SRE Agent v1.9.0</strong> — rollback automático executado' },
    { icon: '⚡', type: 'info', msg: 'Extended Thinking ativado — latência +2.1s, precisão <strong>+18%</strong>' },
    { icon: '✓', type: 'success', msg: '<strong>Chief of Staff</strong> resumiu 47 emails em 3 bullet-points' },
    { icon: '◈', type: 'info', msg: 'Novo modelo disponível: <strong>Claude 4 Opus (2026-03)</strong>' },
];

let feedPaused = false;
let feedInterval;

function initFeed() {
    const scroll = $('#feedScroll');
    if (!scroll) return;

    // Initial items
    for (let i = 0; i < 6; i++) {
        addFeedItem(scroll, false);
    }

    // Auto-add new items
    feedInterval = setInterval(() => {
        if (!feedPaused) addFeedItem(scroll, true);
    }, 4000 + random(0, 3000));

    // Pause button
    const pauseBtn = $('#pauseFeed');
    if (pauseBtn) {
        pauseBtn.addEventListener('click', () => {
            feedPaused = !feedPaused;
            pauseBtn.innerHTML = feedPaused
                ? '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><polygon points="5,3 13,8 5,13"/></svg>'
                : '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="4" y="3" width="3" height="10" rx="0.5"/><rect x="9" y="3" width="3" height="10" rx="0.5"/></svg>';
        });
    }
}

function addFeedItem(container, animate) {
    const item = feedPool[Math.floor(random(0, feedPool.length))];
    const now = new Date();
    const time = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

    const el = document.createElement('div');
    el.className = 'feed-item';
    if (!animate) el.style.animation = 'none';
    el.innerHTML = `
        <span class="feed-time">${time}</span>
        <span class="feed-icon ${item.type}">${item.icon}</span>
        <span class="feed-msg">${item.msg}</span>
    `;

    container.insertBefore(el, container.firstChild);

    // Keep max 15 items
    while (container.children.length > 15) {
        container.removeChild(container.lastChild);
    }
}

// ===========================
// 7. Command Palette
// ===========================
function initCommandPalette() {
    const overlay = $('#cmdOverlay');
    const input = $('#cmdInput');
    const trigger = $('#searchTrigger');
    if (!overlay) return;

    const open = () => {
        overlay.classList.add('open');
        setTimeout(() => input.focus(), 100);
    };

    const close = () => {
        overlay.classList.remove('open');
        input.value = '';
        filterCommands('');
    };

    // Triggers
    if (trigger) trigger.addEventListener('click', open);

    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
            e.preventDefault();
            overlay.classList.contains('open') ? close() : open();
        }
        if (e.key === 'Escape' && overlay.classList.contains('open')) {
            close();
        }
    });

    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) close();
    });

    // Search filtering
    input.addEventListener('input', () => {
        filterCommands(input.value.toLowerCase());
    });

    // Item click
    $$('.cmd-item').forEach(item => {
        item.addEventListener('click', () => {
            const action = item.dataset.action;
            close();
            handleAction(action);
        });
    });

    // Keyboard navigation
    input.addEventListener('keydown', (e) => {
        const items = $$('.cmd-item:not([style*="display: none"])');
        const activeIdx = items.findIndex(i => i.classList.contains('active'));

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            items[activeIdx]?.classList.remove('active');
            items[(activeIdx + 1) % items.length]?.classList.add('active');
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            items[activeIdx]?.classList.remove('active');
            items[(activeIdx - 1 + items.length) % items.length]?.classList.add('active');
        } else if (e.key === 'Enter') {
            const active = items[activeIdx];
            if (active) {
                close();
                handleAction(active.dataset.action);
            }
        }
    });
}

function filterCommands(query) {
    $$('.cmd-item').forEach(item => {
        const text = (item.querySelector('.cmd-item-title')?.textContent || '').toLowerCase();
        const desc = (item.querySelector('.cmd-item-desc')?.textContent || '').toLowerCase();
        const match = !query || text.includes(query) || desc.includes(query);
        item.style.display = match ? '' : 'none';
    });

    // Update active
    const visible = $$('.cmd-item:not([style*="display: none"])');
    $$('.cmd-item').forEach(i => i.classList.remove('active'));
    if (visible[0]) visible[0].classList.add('active');

    // Hide empty groups
    $$('.cmd-group').forEach(group => {
        const hasVisible = group.querySelectorAll('.cmd-item:not([style*="display: none"])').length > 0;
        group.style.display = hasVisible ? '' : 'none';
    });
}

function handleAction(action) {
    const messages = {
        'new-agent': { icon: '⚡', text: 'Wizard de criação de agente aberto' },
        'deploy': { icon: '🚀', text: 'Preparando deploy para produção...' },
        'logs': { icon: '📋', text: 'Abrindo stream de logs em tempo real' },
        'analytics': { icon: '◈', text: 'Navegando para Analytics' },
        'settings': { icon: '⚙', text: 'Abrindo Configurações' },
    };

    const msg = messages[action];
    if (msg) showToast(msg.icon, msg.text);
}

// ===========================
// 8. Toast Notifications
// ===========================
function showToast(icon, text, duration = 4000) {
    const container = $('#toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span>${text}</span>
        <button class="toast-close" aria-label="Fechar">×</button>
    `;

    container.appendChild(toast);

    const remove = () => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    };

    toast.querySelector('.toast-close').addEventListener('click', remove);
    setTimeout(remove, duration);
}

// ===========================
// 9. Sidebar Navigation
// ===========================
function initNav() {
    const items = $$('.nav-item');
    const toggle = $('#sidebarToggle');
    const sidebar = $('#sidebar');

    items.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            items.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            const view = item.dataset.view;
            showToast('◈', `Navegando para ${item.querySelector('span:not(.nav-badge):not(.nav-dot-new)')?.textContent || view}`);

            // Mobile: close sidebar
            if (sidebar) sidebar.classList.remove('open');
        });
    });

    if (toggle && sidebar) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
        });

        // Close on outside click
        document.addEventListener('click', (e) => {
            if (sidebar.classList.contains('open') && !sidebar.contains(e.target) && e.target !== toggle) {
                sidebar.classList.remove('open');
            }
        });
    }
}

// ===========================
// 10. Tab Switching
// ===========================
function initTabs() {
    $$('.tab-group').forEach(group => {
        const tabs = $$('.tab', group);
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
            });
        });
    });
}

// ===========================
// 11. Insight Action Buttons
// ===========================
function initInsightActions() {
    $$('.insight-btn.primary').forEach(btn => {
        btn.addEventListener('click', () => {
            const text = btn.textContent.trim();
            showToast('✓', `Ação executada: ${text}`);
            
            // Visual feedback
            btn.textContent = 'Aplicado ✓';
            btn.style.opacity = '0.6';
            btn.style.pointerEvents = 'none';

            setTimeout(() => {
                btn.textContent = text;
                btn.style.opacity = '';
                btn.style.pointerEvents = '';
            }, 3000);
        });
    });
}

// ===========================
// 12. New Agent Button
// ===========================
function initNewAgent() {
    const btn = $('#newAgentBtn');
    if (!btn) return;
    btn.addEventListener('click', () => {
        showToast('⚡', 'Wizard de criação de agente aberto');
    });
}

// ===========================
// 13. Notification Button
// ===========================
function initNotifications() {
    const btn = $('#notifBtn');
    if (!btn) return;
    btn.addEventListener('click', () => {
        showToast('🔔', '3 notificações pendentes — SRE Agent requer atenção');
        const dot = btn.querySelector('.notif-dot');
        if (dot) dot.style.display = 'none';
    });
}

// ===========================
// 14. Metric Cards Hover
// ===========================
function initMetricHover() {
    $$('.metric-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.borderColor = 'rgba(232, 168, 56, 0.15)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.borderColor = '';
        });
    });
}

// ===========================
// 15. Agent Row Click
// ===========================
function initAgentRows() {
    $$('.agent-row').forEach(row => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', () => {
            const name = row.querySelector('.agent-name')?.textContent;
            showToast('◆', `Abrindo detalhes do ${name}`);
        });
    });
}

// ===========================
// 16. Deploy row click
// ===========================
function initDeployRows() {
    $$('.deploy-row').forEach(row => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', () => {
            const hash = row.querySelector('.deploy-hash')?.textContent;
            showToast('📋', `Detalhes do commit ${hash}`);
        });
    });
}

// ===========================
// 17. Initial Welcome Toast
// ===========================
function showWelcomeToast() {
    setTimeout(() => {
        showToast('◆', 'Bem-vindo ao Command Center — <kbd style="font-family:inherit;background:rgba(255,255,255,0.1);padding:1px 4px;border-radius:3px;font-size:0.8em;">⌘K</kbd> para acessar qualquer coisa', 6000);
    }, 1500);
}

// ===========================
// INIT
// ===========================
document.addEventListener('DOMContentLoaded', () => {
    initClock();
    initGreeting();
    initCounters();
    initChart();
    initSparklines();
    initFeed();
    initCommandPalette();
    initNav();
    initTabs();
    initInsightActions();
    initNewAgent();
    initNotifications();
    initMetricHover();
    initAgentRows();
    initDeployRows();
    showWelcomeToast();
});

// Resize handler for sparklines
let resizeTimeout;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(() => {
        $$('.metric-spark canvas').forEach(c => c.remove());
        initSparklines();
    }, 300);
});
