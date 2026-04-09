/* ============================================
   NeuralForge AI — Interactive Scripts
   ============================================ */

// ===========================
// 1. PARTICLES BACKGROUND
// ===========================
class ParticleSystem {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.particles = [];
        this.connections = [];
        this.mouse = { x: null, y: null, radius: 150 };
        this.resize();
        this.init();
        this.bindEvents();
        this.animate();
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
    }

    init() {
        const count = Math.min(Math.floor((this.canvas.width * this.canvas.height) / 15000), 80);
        this.particles = [];
        for (let i = 0; i < count; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 0.5,
                opacity: Math.random() * 0.5 + 0.1
            });
        }
    }

    bindEvents() {
        window.addEventListener('resize', () => {
            this.resize();
            this.init();
        });
        window.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });
        window.addEventListener('mouseout', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        this.particles.forEach((p, i) => {
            // Move
            p.x += p.vx;
            p.y += p.vy;

            // Bounce
            if (p.x < 0 || p.x > this.canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > this.canvas.height) p.vy *= -1;

            // Mouse interaction
            if (this.mouse.x !== null) {
                const dx = this.mouse.x - p.x;
                const dy = this.mouse.y - p.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < this.mouse.radius) {
                    const force = (this.mouse.radius - dist) / this.mouse.radius;
                    p.vx -= (dx / dist) * force * 0.05;
                    p.vy -= (dy / dist) * force * 0.05;
                }
            }

            // Draw particle
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            this.ctx.fillStyle = `rgba(139, 92, 246, ${p.opacity})`;
            this.ctx.fill();

            // Draw connections
            for (let j = i + 1; j < this.particles.length; j++) {
                const other = this.particles[j];
                const dx = p.x - other.x;
                const dy = p.y - other.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    this.ctx.beginPath();
                    this.ctx.moveTo(p.x, p.y);
                    this.ctx.lineTo(other.x, other.y);
                    this.ctx.strokeStyle = `rgba(139, 92, 246, ${0.08 * (1 - dist / 120)})`;
                    this.ctx.lineWidth = 0.5;
                    this.ctx.stroke();
                }
            }
        });

        requestAnimationFrame(() => this.animate());
    }
}

// ===========================
// 2. NAVBAR SCROLL EFFECT
// ===========================
function initNavbar() {
    const navbar = document.getElementById('navbar');
    const toggle = document.getElementById('mobile-toggle');
    const links = document.getElementById('nav-links');

    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    if (toggle && links) {
        toggle.addEventListener('click', () => {
            links.classList.toggle('open');
        });

        // Close on link click
        links.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                links.classList.remove('open');
            });
        });
    }
}

// ===========================
// 3. SCROLL REVEAL
// ===========================
function initScrollReveal() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const delay = entry.target.dataset.delay || 0;
                setTimeout(() => {
                    entry.target.classList.add('revealed');
                }, parseInt(delay));
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    document.querySelectorAll('.scroll-reveal').forEach(el => {
        observer.observe(el);
    });
}

// ===========================
// 4. COUNTER ANIMATION
// ===========================
function initCounters() {
    const counters = document.querySelectorAll('.stat-number');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseFloat(el.dataset.target);
                const isDecimal = target % 1 !== 0;
                const duration = 2000;
                const start = performance.now();

                function update(now) {
                    const elapsed = now - start;
                    const progress = Math.min(elapsed / duration, 1);
                    // Ease out cubic
                    const eased = 1 - Math.pow(1 - progress, 3);
                    const current = target * eased;

                    if (isDecimal) {
                        el.textContent = current.toFixed(1);
                    } else if (target >= 1000) {
                        el.textContent = Math.floor(current).toLocaleString('pt-BR');
                    } else {
                        el.textContent = Math.floor(current);
                    }

                    if (progress < 1) {
                        requestAnimationFrame(update);
                    }
                }

                requestAnimationFrame(update);
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(c => observer.observe(c));
}

// ===========================
// 5. PRICING TOGGLE
// ===========================
function initPricingToggle() {
    const toggle = document.getElementById('pricing-switch');
    const monthlyLabel = document.getElementById('monthly-label');
    const annualLabel = document.getElementById('annual-label');
    const priceValues = document.querySelectorAll('.price-value');

    if (!toggle) return;

    toggle.addEventListener('change', () => {
        const isAnnual = toggle.checked;

        monthlyLabel.classList.toggle('active', !isAnnual);
        annualLabel.classList.toggle('active', isAnnual);

        priceValues.forEach(el => {
            const target = isAnnual ? el.dataset.annual : el.dataset.monthly;
            
            // Animate the number change
            el.style.opacity = '0';
            el.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                el.textContent = target;
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, 200);
        });
    });
}

// ===========================
// 6. TERMINAL TYPEWRITER
// ===========================
function initTypewriter() {
    const commands = [
        { text: 'pip install neuralforge', delay: 50 },
        { text: '', type: 'wait', delay: 600 },
        { text: '✓ Instalando NeuralForge v4.2.1...', type: 'output', class: 'success' },
        { text: '✓ Dependências instaladas', type: 'output', class: 'success' },
        { text: '', type: 'wait', delay: 400 },
        { text: 'neuralforge init --project meu-saas', delay: 50 },
        { text: '', type: 'wait', delay: 800 },
        { text: '⚡ Projeto criado com sucesso!', type: 'output', class: 'info' },
        { text: '📁 Estrutura gerada:', type: 'output', class: 'info' },
        { text: '   ├── agents/', type: 'output' },
        { text: '   ├── tools/', type: 'output' },
        { text: '   ├── config.yaml', type: 'output' },
        { text: '   └── main.py', type: 'output' },
        { text: '', type: 'wait', delay: 400 },
        { text: 'neuralforge deploy --production', delay: 50 },
        { text: '', type: 'wait', delay: 1000 },
        { text: '🚀 Deploy concluído em 12s', type: 'output', class: 'success' },
        { text: '🌐 URL: https://meu-saas.neuralforge.ai', type: 'output', class: 'info' },
    ];

    const terminalBody = document.getElementById('terminal-demo');
    if (!terminalBody) return;

    let commandIndex = 0;

    function typeCommand(text, delay, callback) {
        const typewriter = document.getElementById('typewriter');
        const cursor = terminalBody.querySelector('.terminal-cursor');
        typewriter.textContent = '';
        
        if (cursor) cursor.style.display = 'inline';

        let charIndex = 0;
        const interval = setInterval(() => {
            typewriter.textContent += text[charIndex];
            charIndex++;
            if (charIndex >= text.length) {
                clearInterval(interval);
                if (cursor) cursor.style.display = 'none';
                if (callback) callback();
            }
        }, delay);
    }

    function addOutput(text, className) {
        const line = document.createElement('div');
        line.className = 'terminal-output' + (className ? ` ${className}` : '');
        line.textContent = text;
        terminalBody.appendChild(line);
        terminalBody.scrollTop = terminalBody.scrollHeight;
    }

    function addNewPrompt() {
        const line = document.createElement('div');
        line.className = 'terminal-line';
        line.innerHTML = `<span class="terminal-prompt">$</span><span class="terminal-command" id="typewriter"></span><span class="terminal-cursor">|</span>`;
        terminalBody.appendChild(line);
    }

    function processCommands() {
        if (commandIndex >= commands.length) {
            // Restart after a pause
            setTimeout(() => {
                const firstLine = terminalBody.querySelector('.terminal-line');
                terminalBody.innerHTML = '';
                terminalBody.appendChild(firstLine);
                document.getElementById('typewriter').textContent = '';
                const cursor = terminalBody.querySelector('.terminal-cursor');
                if (cursor) cursor.style.display = 'inline';
                commandIndex = 0;
                processCommands();
            }, 3000);
            return;
        }

        const cmd = commands[commandIndex];
        commandIndex++;

        if (cmd.type === 'wait') {
            setTimeout(processCommands, cmd.delay);
        } else if (cmd.type === 'output') {
            addOutput(cmd.text, cmd.class);
            setTimeout(processCommands, 80);
        } else {
            typeCommand(cmd.text, cmd.delay, () => {
                setTimeout(() => {
                    addNewPrompt();
                    processCommands();
                }, 400);
            });
        }
    }

    // Start only when visible
    const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting) {
            setTimeout(processCommands, 500);
            observer.unobserve(terminalBody);
        }
    }, { threshold: 0.3 });

    observer.observe(terminalBody);
}

// ===========================
// 7. SMOOTH SCROLL
// ===========================
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                const offset = 80;
                const top = target.getBoundingClientRect().top + window.scrollY - offset;
                window.scrollTo({ top, behavior: 'smooth' });
            }
        });
    });
}

// ===========================
// 8. BATCH BAR ANIMATION
// ===========================
function initBatchAnimation() {
    const bars = document.querySelectorAll('.batch-bar');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                bars.forEach(bar => {
                    bar.style.animation = 'none';
                    bar.offsetHeight; // trigger reflow
                    bar.style.animation = null;
                });
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });

    if (bars.length > 0) {
        observer.observe(bars[0].parentElement);
    }
}

// ===========================
// 9. PARALLAX MICRO-EFFECTS
// ===========================
function initParallax() {
    const heroGlow = document.querySelector('.hero-glow');
    
    window.addEventListener('scroll', () => {
        const scrollY = window.scrollY;
        if (heroGlow && scrollY < 1000) {
            heroGlow.style.transform = `translateX(-50%) translateY(${scrollY * 0.3}px)`;
        }
    });
}

// ===========================
// 10. CHART BAR ANIMATION
// ===========================
function initChartAnimation() {
    const chartBars = document.querySelectorAll('.chart-bar');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                chartBars.forEach((bar, i) => {
                    bar.style.animation = 'none';
                    bar.style.height = '0';
                    setTimeout(() => {
                        bar.style.transition = `height 0.6s ease ${i * 0.1}s`;
                        bar.style.height = bar.style.getPropertyValue('--height');
                    }, 100);
                });
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.3 });

    if (chartBars.length > 0) {
        observer.observe(chartBars[0].parentElement);
    }
}

// ===========================
// 11. HOVER GLOW CARDS
// ===========================
function initCardGlow() {
    document.querySelectorAll('.feature-card, .agent-card, .bento-card').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
            card.style.background = `
                radial-gradient(300px circle at ${x}px ${y}px, rgba(139, 92, 246, 0.06), transparent 60%),
                var(--bg-card)
            `;
        });
        card.addEventListener('mouseleave', () => {
            card.style.background = '';
        });
    });
}

// ===========================
// INIT
// ===========================
document.addEventListener('DOMContentLoaded', () => {
    // Particles
    const canvas = document.getElementById('particles-canvas');
    if (canvas) new ParticleSystem(canvas);

    // All initializations
    initNavbar();
    initScrollReveal();
    initCounters();
    initPricingToggle();
    initTypewriter();
    initSmoothScroll();
    initBatchAnimation();
    initParallax();
    initChartAnimation();
    initCardGlow();
});
