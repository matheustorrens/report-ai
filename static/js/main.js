/**
 * ReportAI Landing Page - Main JavaScript
 * Motion Design Pro Implementation with GSAP
 */

// ==========================================================================
// GSAP Configuration & Registration
// ==========================================================================

gsap.registerPlugin(ScrollTrigger);

// ==========================================================================
// Navigation Scroll Effect
// ==========================================================================

const nav = document.getElementById('nav');
let lastScrollY = window.scrollY;

function handleNavScroll() {
    const currentScrollY = window.scrollY;
    
    if (currentScrollY > 50) {
        nav.classList.add('is-scrolled');
    } else {
        nav.classList.remove('is-scrolled');
    }
    
    lastScrollY = currentScrollY;
}

window.addEventListener('scroll', handleNavScroll, { passive: true });

// ==========================================================================
// Typewriter Effect - Plataformas
// ==========================================================================

function initTypewriter() {
    const typewriterEl = document.getElementById('typewriter');
    if (!typewriterEl) return;
    
    const platforms = ['Google Ads', 'Meta Ads', 'Google Analytics'];
    let platformIndex = 0;
    let charIndex = 0;
    let isDeleting = false;
    let isPaused = false;
    
    const typeSpeed = 80;      // Velocidad de escritura
    const deleteSpeed = 50;    // Velocidad de borrado
    const pauseDuration = 2000; // Pausa entre palabras
    
    function type() {
        const currentPlatform = platforms[platformIndex];
        
        if (isPaused) {
            isPaused = false;
            isDeleting = true;
            setTimeout(type, 500);
            return;
        }
        
        if (isDeleting) {
            // Borrar caracteres
            typewriterEl.textContent = currentPlatform.substring(0, charIndex - 1);
            charIndex--;
            
            if (charIndex === 0) {
                isDeleting = false;
                platformIndex = (platformIndex + 1) % platforms.length;
            }
            
            setTimeout(type, deleteSpeed);
        } else {
            // Escribir caracteres
            typewriterEl.textContent = currentPlatform.substring(0, charIndex + 1);
            charIndex++;
            
            if (charIndex === currentPlatform.length) {
                isPaused = true;
                setTimeout(type, pauseDuration);
                return;
            }
            
            setTimeout(type, typeSpeed);
        }
    }
    
    // Iniciar después de la animación del hero
    setTimeout(type, 1500);
}

// ==========================================================================
// Scroll Animations - Motion Design Pro
// ==========================================================================

function initScrollAnimations() {
    // Select all elements with data-animate attribute
    const animatedElements = document.querySelectorAll('[data-animate]');
    
    animatedElements.forEach(el => {
        // Create ScrollTrigger for each element
        ScrollTrigger.create({
            trigger: el,
            start: 'top 85%',
            onEnter: () => {
                el.classList.add('is-visible');
            },
            once: true
        });
    });
}

// ==========================================================================
// Hero Animation Sequence - Coreography
// ==========================================================================

function animateHero() {
    const tl = gsap.timeline({ 
        defaults: { 
            ease: 'expo.out',
            duration: 1 
        }
    });
    
    tl
        // 1. Badge enters with subtle slide
        .from('.hero__badge', {
            y: 20,
            opacity: 0,
            duration: 0.7
        })
        
        // 2. Title 
        .from('.hero__title', {
            y: 60,
            opacity: 0,
            duration: 0.9
        }, '-=0.4')
        
        // 3. Subtitle
        .from('.hero__subtitle', {
            y: 30,
            opacity: 0,
            duration: 0.8
        }, '-=0.5')
        
        // 4. CTA Box con botón y barra de progreso
        .from('.hero__cta-box', {
            y: 30,
            opacity: 0,
            duration: 0.8
        }, '-=0.4')
        
        // 5. Platforms section
        .from('.hero__platforms', {
            y: 20,
            opacity: 0,
            duration: 0.7
        }, '-=0.3')
        
        // 6. Mockup visual (desktop)
        .from('.hero__visual', {
            x: 60,
            opacity: 0,
            duration: 1.2,
        }, '-=0.8');
    
    return tl;
}

// ==========================================================================
// Counter Animation
// ==========================================================================

function animateCounter(el) {
    const target = parseInt(el.dataset.count, 10);
    
    gsap.to(el, {
        innerText: target,
        duration: 2,
        ease: 'power3.out',
        snap: { innerText: 1 },
        scrollTrigger: {
            trigger: el,
            start: 'top 80%',
            once: true
        }
    });
}

function initCounters() {
    const counters = document.querySelectorAll('[data-count]');
    counters.forEach(counter => {
        animateCounter(counter);
    });
}

// ==========================================================================
// Progress Bar Animation
// ==========================================================================

function animateProgressBar() {
    const progressFill = document.querySelector('.hero__cta-progress-fill');
    const heroCounter = document.getElementById('hero-counter');
    
    if (progressFill) {
        // Animar a barra de progresso
        gsap.fromTo(progressFill,
            { width: '0%' },
            {
                width: '97%',
                duration: 2,
                ease: 'power3.out',
                delay: 1.8
            }
        );
    }
    
    if (heroCounter) {
        // Animar contador de 0 a 97
        gsap.to(heroCounter, {
            innerText: 97,
            duration: 2,
            ease: 'power3.out',
            snap: { innerText: 1 },
            delay: 1.8
        });
    }
}

// ==========================================================================
// Mockup Chart Animation
// ==========================================================================

function animateMockupChart() {
    const chartLine = document.querySelector('.hero__chart-line');
    const chartArea = document.querySelector('.hero__chart-area');
    
    if (chartLine) {
        const lineLength = chartLine.getTotalLength ? chartLine.getTotalLength() : 500;
        
        gsap.set(chartLine, {
            strokeDasharray: lineLength,
            strokeDashoffset: lineLength
        });
        
        gsap.to(chartLine, {
            strokeDashoffset: 0,
            duration: 2,
            ease: 'expo.out',
            delay: 2
        });
    }
    
    if (chartArea) {
        gsap.from(chartArea, {
            opacity: 0,
            duration: 1,
            ease: 'power2.out',
            delay: 3
        });
    }
}

// ==========================================================================
// Mockup Metrics Animation
// ==========================================================================

function animateMockupMetrics() {
    const metrics = document.querySelectorAll('.hero__mockup-metric');
    
    gsap.from(metrics, {
        y: 20,
        opacity: 0,
        duration: 0.6,
        stagger: 0.1,
        ease: 'back.out(1.5)',
        delay: 2.2
    });
}

// ==========================================================================
// AI Insight Animation
// ==========================================================================

function animateAIInsight() {
    const aiSection = document.querySelector('.hero__mockup-ai');
    
    if (aiSection) {
        gsap.from(aiSection, {
            y: 20,
            opacity: 0,
            duration: 0.8,
            ease: 'expo.out',
            delay: 3.2
        });
    }
}

// ==========================================================================
// Solution Steps Animation
// ==========================================================================

function animateSolutionSteps() {
    const steps = document.querySelectorAll('.solution__step');
    
    steps.forEach((step, index) => {
        gsap.from(step, {
            x: index % 2 === 0 ? -40 : 40,
            opacity: 0,
            duration: 0.8,
            ease: 'expo.out',
            scrollTrigger: {
                trigger: step,
                start: 'top 80%',
                once: true
            }
        });
    });
}

// ==========================================================================
// Benefits Cards Hover Effect
// ==========================================================================

function initBenefitsHover() {
    const cards = document.querySelectorAll('.benefits__card');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            gsap.to(card, {
                scale: 1.02,
                duration: 0.4,
                ease: 'back.out(2)'
            });
        });
        
        card.addEventListener('mouseleave', () => {
            gsap.to(card, {
                scale: 1,
                duration: 0.6,
                ease: 'elastic.out(1, 0.4)'
            });
        });
    });
}

// ==========================================================================
// FAQ Accordion
// ==========================================================================

function initFAQ() {
    const faqItems = document.querySelectorAll('.faq__item');
    
    faqItems.forEach(item => {
        item.addEventListener('toggle', () => {
            if (item.open) {
                const answer = item.querySelector('.faq__answer');
                gsap.fromTo(answer,
                    { height: 0, opacity: 0 },
                    { 
                        height: 'auto', 
                        opacity: 1, 
                        duration: 0.4, 
                        ease: 'expo.out' 
                    }
                );
            }
        });
    });
}

// ==========================================================================
// Form Handling
// ==========================================================================

function initWaitlistForm() {
    const form = document.getElementById('waitlist-form');
    
    if (!form) return;
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const button = form.querySelector('button[type="submit"]');
        const input = form.querySelector('input[name="email"]');
        const originalText = button.innerHTML;
        
        // Visual feedback - loading state
        button.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="animate-spin">
                <circle cx="10" cy="10" r="8" stroke="currentColor" stroke-width="2" stroke-dasharray="32 32" stroke-linecap="round"/>
            </svg>
            <span>Reservando...</span>
        `;
        button.disabled = true;
        
        // Submit the form to the Django backend
        form.submit();
    });
}

// ==========================================================================
// Smooth Scroll for Anchor Links
// ==========================================================================

function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const target = document.querySelector(targetId);
            if (!target) return;
            
            const navHeight = nav.offsetHeight;
            const targetPosition = target.getBoundingClientRect().top + window.scrollY - navHeight - 20;
            
            gsap.to(window, {
                scrollTo: { y: targetPosition, autoKill: false },
                duration: 1,
                ease: 'expo.inOut'
            });
        });
    });
}

// ==========================================================================
// Initialize Everything
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Core animations
    initScrollAnimations();
    
    // Hero section
    animateHero();
    animateProgressBar();
    animateMockupChart();
    animateMockupMetrics();
    animateAIInsight();
    initTypewriter();
    
    // Counters
    initCounters();
    
    // Interactive elements
    initBenefitsHover();
    initFAQ();
    initWaitlistForm();
    initSmoothScroll();
});

// Add GSAP ScrollTo plugin support (if not available, use native scrollTo)
if (!gsap.plugins.scrollTo) {
    gsap.to = (target, config) => {
        if (target === window && config.scrollTo) {
            window.scrollTo({
                top: config.scrollTo.y,
                behavior: 'smooth'
            });
        }
    };
}

// CSS for spinner animation
const style = document.createElement('style');
style.textContent = `
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    .animate-spin {
        animation: spin 1s linear infinite;
    }
`;
document.head.appendChild(style);
