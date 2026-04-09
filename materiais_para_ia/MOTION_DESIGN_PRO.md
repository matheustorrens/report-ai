# 🎬 Motion Design de Alto Nível — O que Separa o Amador do Profissional

> **Versão:** 2.0.0 — Edição Pro · Licença MIT  
> Este guia não ensina *o que usar*. Ensina *como pensar* como um motion designer de nível Awwwards.

---

## ⚠️ Por que suas animações parecem amadoras

Antes de qualquer código, entenda o diagnóstico. Animações amadoras geralmente falham em **um ou mais** destes pontos:

| Problema Amador | Solução Profissional |
|---|---|
| Tudo usa `fadeIn + translateY(20px)` | Cada elemento tem sua própria identidade de movimento |
| Duração igual para tudo (`0.3s`) | Duração proporcional à distância e hierarquia visual |
| `ease-in-out` padrão em tudo | Curvas customizadas por contexto (entrada ≠ saída ≠ hover) |
| Animações isoladas, sem relação | Coreografia orquestrada com relações de tempo |
| Elementos aparecem, não *revelam* | Clip-path, mask, overflow hidden para revelar com direção |
| Sem atmosfera visual | Grain, blur, blend-mode, noise para profundidade |
| Hover genérico (`scale(1.05)`) | Hover que comunica a intenção do elemento |
| Scroll trigger em tudo, sem ritmo | Hierarquia de revelação que guia o olhar |

---

## 📋 Índice

1. [A Mentalidade Profissional](#1-a-mentalidade-profissional)
2. [Coreografia — O Segredo Real](#2-coreografia--o-segredo-real)
3. [Revelar vs. Aparecer — Clip-path e Masks](#3-revelar-vs-aparecer--clip-path-e-masks)
4. [Tipografia em Movimento](#4-tipografia-em-movimento)
5. [Física de Animação — Springs e Lerp](#5-física-de-animação--springs-e-lerp)
6. [Atmosfera Visual — Grain, Noise e Blend Modes](#6-atmosfera-visual--grain-noise-e-blend-modes)
7. [Loader e Page Transition](#7-loader-e-page-transition)
8. [Cursor Customizado de Nível Pro](#8-cursor-customizado-de-nível-pro)
9. [Scroll Storytelling](#9-scroll-storytelling)
10. [Microinterações que Impressionam](#10-microinterações-que-impressionam)
11. [Easing Avançado — A Curva Certa](#11-easing-avançado--a-curva-certa)
12. [Paletas e Tipografia que Elevam](#12-paletas-e-tipografia-que-elevam)
13. [Prompts Pro para o Claude](#13-prompts-pro-para-o-claude)
14. [Checklist Awwwards](#14-checklist-awwwards)

---

## 1. A Mentalidade Profissional

### Anime Intenção, não Elementos

A pergunta não é *"como animo este div?"*, mas *"o que este movimento comunica?"*

```
AMADOR: "Vou adicionar uma animação aqui para ficar bonito."

PROFISSIONAL: "Este elemento entra pelo lado esquerdo porque
               vem de um contexto anterior. Ele desacelera
               ao parar porque tem peso. O delay é de 80ms
               porque vem depois do título, que é mais importante."
```

### Os 3 Eixos do Motion Profissional

```
1. TEMPO    → duração, delay, ritmo, pausa
2. ESPAÇO   → distância, direção, transformação, escala
3. ENERGIA  → easing, friction, elasticidade, impacto
```

### Hierarquia de Movimento

Cada página tem uma **história de movimento**. O olhar do usuário deve ser guiado:

```
[1] Elemento mais importante → entra primeiro, mais expressivo
[2] Contexto/Suporte         → entra em seguida, mais sutil
[3] Detalhes                 → stagger leve, quase imperceptível
[4] Background/Decorativo    → último, muito sutil ou parallax
```

---

## 2. Coreografia — O Segredo Real

Coreografia é a **relação entre as animações**, não as animações em si.

### Operadores de Tempo do GSAP (Fundamental)

```javascript
const tl = gsap.timeline();

// ─── Posicionamento no timeline ───
tl.from('.a', { y: 40, opacity: 0, duration: 0.6 })

  // SEQUENCIAL: começa após o anterior terminar
  .from('.b', { y: 40, opacity: 0 })

  // OVERLAP: começa 0.3s ANTES do anterior terminar
  .from('.c', { y: 20, opacity: 0 }, '-=0.3')

  // JUNTOS: começa NO MESMO MOMENTO que o anterior
  .from('.d', { opacity: 0 }, '<')

  // JUNTO COM OFFSET: começa 0.1s APÓS o início do anterior
  .from('.e', { opacity: 0 }, '<0.1')

  // ABSOLUTO: começa no segundo 1.5 do timeline
  .from('.f', { opacity: 0 }, 1.5)

  // RELATIVO AO FIM: começa 0.5s após o fim do timeline
  .from('.g', { opacity: 0 }, '+=0.5');
```

### Padrão de Hero Orquestrado (Profissional)

```javascript
// Este é o padrão que você vê em sites Awwwards.
// Nota: cada elemento tem sua própria personalidade de movimento.

function animateHeroEntrance() {
  gsap.set('.hero-eyebrow, .hero-title .line-inner, .hero-body, .hero-cta, .hero-media', {
    visibility: 'visible' // evita FOUC
  });

  const tl = gsap.timeline({ defaults: { ease: 'expo.out' } });

  tl
    // 1. Eyebrow (tag pequena) — desliza da esquerda, sutil
    .from('.hero-eyebrow', {
      x: -24, opacity: 0, duration: 0.7
    })

    // 2. Título — cada linha sobe de baixo do overflow (não fade!)
    .to('.hero-title .line-inner', {
      y: 0,
      duration: 1.1,
      stagger: 0.1,
    }, '-=0.4')

    // 3. Corpo do texto — fade simples, bem sutil
    .from('.hero-body', {
      opacity: 0, y: 16, duration: 0.7
    }, '-=0.6')

    // 4. CTA — escala + y, mais expressivo pois precisa de atenção
    .from('.hero-cta', {
      opacity: 0, y: 20, scale: 0.94, duration: 0.7,
      ease: 'back.out(1.5)'
    }, '-=0.5')

    // 5. Mídia/imagem — entra por último, mais lento
    .from('.hero-media', {
      opacity: 0, scale: 1.06, duration: 1.2,
    }, '-=0.9')

    // 6. Background decorativo — quase imperceptível
    .from('.hero-bg-element', {
      opacity: 0, scale: 0.9, duration: 1.5,
    }, '-=1.2');

  return tl;
}
```

### Stagger com Personalidade

```javascript
// Stagger básico (amador)
gsap.from('.item', { opacity: 0, y: 20, stagger: 0.1 });

// Stagger com personalidade (profissional)
gsap.from('.item', {
  opacity: 0,
  y: 40,
  duration: 0.7,
  ease: 'expo.out',
  stagger: {
    amount: 0.6,      // duração total do stagger
    from: 'start',    // direção: 'start', 'end', 'center', 'random', 'edges'
    ease: 'power2.in' // easing DO stagger (não da animação!)
    // ease: 'power2.in' = os primeiros elementos chegam mais rápido
    // ease: 'power2.out' = o ritmo desacelera no final
  }
});

// Grid stagger (para layouts em grade)
gsap.from('.grid-item', {
  opacity: 0, scale: 0.9,
  stagger: {
    amount: 0.8,
    grid: 'auto',          // detecta colunas automaticamente
    from: 'center',        // parte do centro do grid para as bordas
    ease: 'power1.inOut'
  }
});
```

---

## 3. Revelar vs. Aparecer — Clip-path e Masks

**Esta é a diferença mais visível entre animações amadoras e profissionais.**

`opacity: 0 → 1` = aparece. Sem direção, sem intenção.  
`clip-path reveal` = *revela*. Tem direção, tem origem, tem peso.

### Técnica de Reveal com Clip-path

```css
/* CSS necessário para o wrapper */
.reveal-wrapper {
  overflow: hidden; /* <- essencial para line reveals */
}

.reveal-content {
  /* Estado inicial definido via JS */
}
```

```javascript
// ─── Revelar de baixo para cima (mais comum) ───
gsap.from('.hero-line', {
  y: '110%',        // sai para baixo do overflow
  duration: 1,
  ease: 'expo.out',
  stagger: 0.12,
});

// ─── Wipe horizontal (clip-path) ───
gsap.from('.image', {
  clipPath: 'inset(0 100% 0 0)',  // de: fechado pela direita
  duration: 1.2,
  ease: 'expo.inOut',
});
// para: clipPath: 'inset(0 0% 0 0)' (default quando não especificado)

// ─── Reveal diagonal ───
gsap.from('.card', {
  clipPath: 'inset(100% 0 0 0)',  // de: fechado por baixo
  duration: 0.9,
  ease: 'expo.out',
  stagger: 0.08,
});

// ─── Máscara de texto com gradiente ───
// Aplica "ink reveal" ao texto
.masked-text {
  background: linear-gradient(90deg, var(--accent) 0%, var(--white) 40%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-size: 200% 100%;
  background-position: 100% 0; /* começa invisível */
  transition: background-position 0.8s cubic-bezier(0.19, 1, 0.22, 1);
}
.masked-text.is-visible {
  background-position: 0% 0; /* revela */
}

// ─── Scale reveal com máscara (muito profissional) ───
// Técnica: o wrapper corta, o inner compensa com scale inverso
// Resultado: o conteúdo parece "crescer para fora" sem distorcer

.clip-reveal-wrapper {
  overflow: hidden;
  transform: scaleY(0);
  transform-origin: top center;
}
.clip-reveal-inner {
  transform: scaleY(2); /* compensa o scale do pai */
  transform-origin: top center;
}

gsap.to('.clip-reveal-wrapper', {
  scaleY: 1,
  duration: 0.9,
  ease: 'expo.out',
});
gsap.to('.clip-reveal-inner', {
  scaleY: 1,
  duration: 0.9,
  ease: 'expo.out',
});
```

### Transição de Página com Clip-path

```javascript
// Curtain reveal — padrão Awwwards para page transitions
function pageTransition(newUrl) {
  const curtain = document.createElement('div');
  curtain.style.cssText = `
    position: fixed; inset: 0; z-index: 9999;
    background: #080808;
    clip-path: inset(100% 0 0 0);
    pointer-events: all;
  `;
  document.body.appendChild(curtain);

  const tl = gsap.timeline();

  tl
    // Fechar: curtain sobe cobrindo a página
    .to(curtain, {
      clipPath: 'inset(0% 0 0 0)',
      duration: 0.7,
      ease: 'expo.inOut',
    })
    // Navegar no meio da transição
    .call(() => { window.location.href = newUrl; })
    // Abrir: curtain desce revelando nova página
    .to(curtain, {
      clipPath: 'inset(0 0 100% 0)',
      duration: 0.7,
      ease: 'expo.inOut',
      delay: 0.3,
    });
}
```

---

## 4. Tipografia em Movimento

Texto animado profissionalmente é **a marca mais visível** de um site de alto nível.

### Split Text sem Plugin

```javascript
// Função para quebrar texto em spans (alternativa ao SplitText)
function splitTextIntoLines(selector) {
  document.querySelectorAll(selector).forEach(el => {
    const text = el.textContent;
    const words = text.split(' ');

    el.innerHTML = words.map(word =>
      `<span class="word"><span class="word-inner">${word}</span></span>`
    ).join(' ');
  });
}

function splitTextIntoChars(selector) {
  document.querySelectorAll(selector).forEach(el => {
    const chars = el.textContent.split('');
    el.innerHTML = chars.map((char, i) =>
      char === ' '
        ? ' '
        : `<span class="char" style="--i:${i}">${char}</span>`
    ).join('');
  });
}
```

```css
/* CSS para o container dos splits */
.word {
  display: inline-block;
  overflow: hidden;
  vertical-align: bottom;
  line-height: 1.15; /* evitar corte */
}
.word-inner {
  display: inline-block;
  /* Estado inicial via JS */
}
```

```javascript
// Animação de revelação palavra por palavra
splitTextIntoLines('.hero-title');

gsap.to('.hero-title .word-inner', {
  scrollTrigger: { trigger: '.hero-title', start: 'top 80%' },
  y: 0,
  opacity: 1,
  duration: 0.8,
  stagger: 0.05,
  ease: 'expo.out',
});

// Animação por caractere (mais dramática)
splitTextIntoChars('.big-number');

gsap.from('.big-number .char', {
  y: 100,
  opacity: 0,
  rotation: 15,
  duration: 0.6,
  stagger: 0.02,
  ease: 'back.out(1.7)',
  delay: 0.3,
});
```

### Text Scramble (Efeito Hacker)

```javascript
class TextScramble {
  constructor(el) {
    this.el = el;
    this.chars = '!<>-_\\/[]{}—=+*^?#@0123456789';
    this.update = this.update.bind(this);
  }

  setText(newText) {
    const length = Math.max(this.el.innerText.length, newText.length);
    const promise = new Promise(resolve => (this.resolve = resolve));
    this.queue = Array.from({ length }, (_, i) => ({
      from: this.el.innerText[i] || '',
      to: newText[i] || '',
      start: Math.floor(Math.random() * 15),
      end: Math.floor(Math.random() * 15) + 15,
    }));
    cancelAnimationFrame(this.frameRequest);
    this.frame = 0;
    this.update();
    return promise;
  }

  update() {
    let output = '';
    let complete = 0;

    this.queue.forEach(({ from, to, start, end }) => {
      if (this.frame >= end) { complete++; output += to; }
      else if (this.frame >= start) {
        output += `<span style="color:var(--accent);opacity:0.7">${this.randomChar()}</span>`;
      } else { output += from; }
    });

    this.el.innerHTML = output;
    if (complete === this.queue.length) this.resolve();
    else { this.frameRequest = requestAnimationFrame(this.update); this.frame++; }
  }

  randomChar() { return this.chars[Math.floor(Math.random() * this.chars.length)]; }
}

// Cycling de frases com scramble
const el = document.querySelector('.scramble');
const fx = new TextScramble(el);
const phrases = ['Crafted with intent.', 'Animated with purpose.', 'Designed to move.'];
let i = 0;

const next = () => fx.setText(phrases[i++ % phrases.length]).then(() => setTimeout(next, 2500));
next();
```

### Contador Animado Profissional

```javascript
// Contador com formatação e easing preciso
function animateCounter(el) {
  const target = parseFloat(el.dataset.count);
  const prefix = el.dataset.prefix || '';
  const suffix = el.dataset.suffix || '';
  const decimals = el.dataset.decimals ? parseInt(el.dataset.decimals) : 0;

  gsap.to({ val: 0 }, {
    scrollTrigger: { trigger: el, start: 'top 80%' },
    val: target,
    duration: 2,
    ease: 'power3.out',
    onUpdate() {
      const formatted = this.targets()[0].val.toFixed(decimals)
        .replace('.', ',')
        .replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      el.textContent = `${prefix}${formatted}${suffix}`;
    }
  });
}

// HTML: <span data-count="4.8" data-prefix="" data-suffix="/5" data-decimals="1">0</span>
document.querySelectorAll('[data-count]').forEach(animateCounter);
```

---

## 5. Física de Animação — Springs e Lerp

A diferença entre uma UI que *parece real* e uma que *parece feita em computador* está aqui.

### LERP — Linear Interpolation

```javascript
// A fórmula: valor_atual += (valor_destino - valor_atual) * fator
// Quanto menor o fator, mais "suave" e com mais inércia

class SmoothFollower {
  constructor(factor = 0.08) {
    this.x = 0; this.y = 0;
    this.targetX = 0; this.targetY = 0;
    this.factor = factor;
    this.callbacks = [];
    this.animate();
  }

  setTarget(x, y) {
    this.targetX = x;
    this.targetY = y;
  }

  onUpdate(fn) { this.callbacks.push(fn); return this; }

  animate() {
    this.x += (this.targetX - this.x) * this.factor;
    this.y += (this.targetY - this.y) * this.factor;
    this.callbacks.forEach(fn => fn(this.x, this.y));
    requestAnimationFrame(() => this.animate());
  }
}

// Cursor com LERP (a base do cursor profissional)
const follower = new SmoothFollower(0.07);

document.addEventListener('mousemove', (e) => {
  follower.setTarget(e.clientX, e.clientY);
});

follower.onUpdate((x, y) => {
  cursorFollowerEl.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
});
```

### Springs com GSAP

```javascript
// Spring physics no GSAP
gsap.to('.ball', {
  x: 300,
  duration: 1,
  ease: 'elastic.out(1, 0.3)',
  // parâmetros: (amplitude, period)
  // amplitude alto = overshoot mais forte
  // period baixo = oscila mais rápido
});

// Spring customizado para hover de botão
const btn = document.querySelector('.btn');

btn.addEventListener('mouseenter', () => {
  gsap.to(btn, {
    scale: 1.06,
    duration: 0.4,
    ease: 'back.out(2)',
  });
});

btn.addEventListener('mouseleave', () => {
  gsap.to(btn, {
    scale: 1,
    duration: 0.6,
    ease: 'elastic.out(1, 0.4)', // retorno com bounce natural
  });
});
```

### Scroll Suavizado com LERP

```javascript
// Smooth scroll que segue o mouse — usado em sites como Linear.app
class SmoothScroll {
  constructor() {
    this.current = 0;
    this.target = 0;
    this.ease = 0.075;

    // Wrapper precisa ter height: 100vh; overflow: hidden no body
    document.body.style.overflow = 'hidden';
    this.wrapper = document.querySelector('.smooth-wrapper');
    this.wrapper.style.position = 'fixed';
    this.wrapper.style.top = '0';
    this.wrapper.style.left = '0';
    this.wrapper.style.width = '100%';

    this.setBodyHeight();
    window.addEventListener('scroll', () => this.onScroll());
    window.addEventListener('resize', () => this.setBodyHeight());
    this.animate();
  }

  setBodyHeight() {
    document.body.style.height = `${this.wrapper.offsetHeight}px`;
  }

  onScroll() { this.target = window.scrollY; }

  animate() {
    this.current += (this.target - this.current) * this.ease;
    this.wrapper.style.transform = `translateY(-${this.current}px)`;

    // Atualizar ScrollTrigger do GSAP
    ScrollTrigger.update();

    requestAnimationFrame(() => this.animate());
  }
}

// Nota: use a biblioteca Lenis para uma implementação mais robusta
// npm install @studio-freight/lenis
```

---

## 6. Atmosfera Visual — Grain, Noise e Blend Modes

Sem isso, qualquer página parece plana, independentemente das animações.

### Grain Overlay (Essencial)

```html
<!-- Adicionar como primeiro filho do body -->
<div class="grain-overlay" aria-hidden="true"></div>
```

```css
/* Método 1: SVG inline (mais leve) */
.grain-overlay {
  position: fixed;
  inset: -200%;
  width: 400%;
  height: 400%;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='1'/%3E%3C/svg%3E");
  opacity: 0.04; /* ajuste entre 0.03 e 0.08 */
  pointer-events: none;
  z-index: 9999;
  animation: grain-move 0.5s steps(3) infinite;
}

@keyframes grain-move {
  0%   { transform: translate(0, 0); }
  33%  { transform: translate(-2%, -1%); }
  66%  { transform: translate(1%, 2%); }
  100% { transform: translate(0, 0); }
}

/* Método 2: Canvas (mais controle) */
```

```javascript
// Grain animado via Canvas (controle total)
function createGrainCanvas() {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');

  canvas.style.cssText = `
    position: fixed; inset: 0;
    width: 100%; height: 100%;
    pointer-events: none;
    z-index: 9999;
    opacity: 0.06;
    mix-blend-mode: overlay;
  `;

  document.body.appendChild(canvas);

  function drawGrain() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const imageData = ctx.createImageData(canvas.width, canvas.height);
    const data = imageData.data;

    for (let i = 0; i < data.length; i += 4) {
      const val = Math.random() * 255;
      data[i] = data[i+1] = data[i+2] = val;
      data[i+3] = 40; // alpha
    }

    ctx.putImageData(imageData, 0, 0);
  }

  function animate() {
    drawGrain();
    requestAnimationFrame(animate);
  }

  animate();
  window.addEventListener('resize', drawGrain);
}

createGrainCanvas();
```

### Blend Modes para Profundidade

```css
/* Texto que se mistura com o fundo */
.blend-text {
  mix-blend-mode: difference; /* branco em dark, escuro em light */
  color: white;
}

/* Cursor que inverte as cores do background */
.cursor {
  mix-blend-mode: difference;
  background: white;
}

/* Overlay de cor que adiciona profundidade */
.color-overlay {
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 30% 40%, rgba(200,245,59,0.15), transparent 60%);
  mix-blend-mode: screen;
  pointer-events: none;
}

/* Texto translúcido de background */
.bg-text {
  color: transparent;
  -webkit-text-stroke: 1px rgba(255,255,255,0.05);
  /* ou: */
  background: linear-gradient(180deg, rgba(255,255,255,0.08), transparent);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Gradiente Mesh (Fundo Moderno)

```css
/* Fundo com gradiente animado */
.mesh-gradient {
  background:
    radial-gradient(at 40% 20%, hsla(220, 80%, 60%, 0.3) 0px, transparent 50%),
    radial-gradient(at 80% 0%, hsla(189, 80%, 70%, 0.2) 0px, transparent 50%),
    radial-gradient(at 0% 50%, hsla(355, 80%, 60%, 0.2) 0px, transparent 50%),
    radial-gradient(at 80% 50%, hsla(340, 80%, 70%, 0.15) 0px, transparent 50%),
    radial-gradient(at 0% 100%, hsla(22, 80%, 60%, 0.2) 0px, transparent 50%);
  background-color: #080808;
  animation: mesh-shift 10s ease infinite alternate;
}

@keyframes mesh-shift {
  0%   { filter: hue-rotate(0deg); }
  100% { filter: hue-rotate(30deg); }
}
```

---

## 7. Loader e Page Transition

O loader **define o tom** de toda a experiência.

### Loader Profissional (Padrão de Agência)

```html
<div id="page-loader">
  <div class="loader-number" id="loaderNum">0</div>
  <div class="loader-progress">
    <div class="loader-bar" id="loaderBar"></div>
  </div>
</div>
```

```css
#page-loader {
  position: fixed; inset: 0;
  background: var(--color-bg);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-end;
  padding: 48px;
  clip-path: inset(0 0 0% 0); /* inicia fechado */
}

.loader-number {
  font-size: clamp(4rem, 15vw, 12rem);
  font-weight: 800;
  letter-spacing: -0.05em;
  line-height: 1;
  color: var(--color-text);
}

.loader-progress {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 2px;
  background: rgba(255,255,255,0.08);
}

.loader-bar {
  height: 100%;
  background: var(--color-accent);
  width: 0%;
  transition: width 0.1s linear;
}
```

```javascript
class PageLoader {
  constructor(onComplete) {
    this.onComplete = onComplete;
    this.progress = 0;
    this.numEl = document.getElementById('loaderNum');
    this.barEl = document.getElementById('loaderBar');
    this.loaderEl = document.getElementById('page-loader');
    this.run();
  }

  run() {
    // Simula carregamento de assets
    const increment = () => {
      // Velocidade variável para parecer real
      const remaining = 100 - this.progress;
      const step = Math.random() * (remaining > 50 ? 8 : remaining > 20 ? 4 : 2);
      this.progress = Math.min(this.progress + step, 98);

      this.numEl.textContent = Math.floor(this.progress);
      this.barEl.style.width = this.progress + '%';

      if (this.progress < 98) {
        setTimeout(increment, 80 + Math.random() * 60);
      } else {
        // Finalizar em 100%
        setTimeout(() => this.finish(), 200);
      }
    };
    increment();
  }

  finish() {
    // Ir a 100 e então sair
    this.progress = 100;
    this.numEl.textContent = '100';
    this.barEl.style.width = '100%';

    setTimeout(() => {
      gsap.to(this.loaderEl, {
        clipPath: 'inset(0 0 100% 0)',
        duration: 1,
        ease: 'expo.inOut',
        onComplete: () => {
          this.loaderEl.remove();
          this.onComplete();
        }
      });
    }, 400);
  }
}

const loader = new PageLoader(() => {
  // Página revelada — animar elementos
  animatePageEntrance();
});
```

---

## 8. Cursor Customizado de Nível Pro

```javascript
class ProCursor {
  constructor() {
    this.dot = this.create('cursor-dot');
    this.ring = this.create('cursor-ring');

    this.x = -100; this.y = -100;
    this.ringX = -100; this.ringY = -100;

    this.bindEvents();
    this.animate();
    this.setupHoverTargets();
  }

  create(className) {
    const el = document.createElement('div');
    el.className = className;
    document.body.appendChild(el);
    return el;
  }

  bindEvents() {
    document.addEventListener('mousemove', (e) => {
      this.x = e.clientX;
      this.y = e.clientY;
      gsap.to(this.dot, {
        x: this.x, y: this.y,
        duration: 0.05,
        ease: 'none'
      });
    });

    // Esconder quando sair da janela
    document.addEventListener('mouseleave', () => {
      gsap.to([this.dot, this.ring], { opacity: 0, duration: 0.3 });
    });
    document.addEventListener('mouseenter', () => {
      gsap.to([this.dot, this.ring], { opacity: 1, duration: 0.3 });
    });
  }

  animate() {
    this.ringX += (this.x - this.ringX) * 0.08;
    this.ringY += (this.y - this.ringY) * 0.08;
    gsap.set(this.ring, { x: this.ringX, y: this.ringY });
    requestAnimationFrame(() => this.animate());
  }

  setupHoverTargets() {
    // Links e botões — expandir o ring
    document.querySelectorAll('a, button, [data-cursor="hover"]').forEach(el => {
      el.addEventListener('mouseenter', () => {
        gsap.to(this.ring, {
          width: 60, height: 60,
          borderColor: 'var(--accent)',
          duration: 0.3, ease: 'back.out'
        });
        gsap.to(this.dot, { scale: 0, duration: 0.2 });
      });
      el.addEventListener('mouseleave', () => {
        gsap.to(this.ring, {
          width: 36, height: 36,
          borderColor: 'rgba(255,255,255,0.4)',
          duration: 0.3
        });
        gsap.to(this.dot, { scale: 1, duration: 0.3, ease: 'back.out' });
      });
    });

    // Cards — mostrar "VIEW" dentro do cursor
    document.querySelectorAll('[data-cursor="view"]').forEach(el => {
      el.addEventListener('mouseenter', () => {
        this.ring.setAttribute('data-label', 'VIEW');
        gsap.to(this.ring, {
          width: 80, height: 80,
          backgroundColor: 'var(--accent)',
          duration: 0.4, ease: 'back.out'
        });
        gsap.to(this.dot, { scale: 0, duration: 0.2 });
      });
      el.addEventListener('mouseleave', () => {
        this.ring.removeAttribute('data-label');
        gsap.to(this.ring, {
          width: 36, height: 36,
          backgroundColor: 'transparent',
          duration: 0.3
        });
        gsap.to(this.dot, { scale: 1, duration: 0.3, ease: 'back.out' });
      });
    });
  }
}
```

```css
*, *::before, *::after { cursor: none !important; }

.cursor-dot {
  width: 8px; height: 8px;
  background: var(--accent);
  border-radius: 50%;
  position: fixed;
  top: -4px; left: -4px;
  pointer-events: none;
  z-index: 10001;
  mix-blend-mode: difference;
}

.cursor-ring {
  width: 36px; height: 36px;
  border: 1.5px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  position: fixed;
  top: -18px; left: -18px;
  pointer-events: none;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Label dentro do cursor */
.cursor-ring::before {
  content: attr(data-label);
  font-family: var(--font-mono);
  font-size: 0.55rem;
  letter-spacing: 0.1em;
  color: var(--black);
  text-transform: uppercase;
  opacity: 0;
  transition: opacity 0.2s;
}
.cursor-ring[data-label]::before { opacity: 1; }
```

---

## 9. Scroll Storytelling

A diferença entre um site que conta uma história e um que apenas lista conteúdo.

### Horizontal Scroll Narrativo

```javascript
// Seção com scroll horizontal — técnica de agência
function initHorizontalSection() {
  const section = document.querySelector('.h-scroll-section');
  const track = document.querySelector('.h-scroll-track');
  const slides = gsap.utils.toArray('.h-slide');

  // Calcular largura total
  const totalWidth = slides.length * window.innerWidth;
  track.style.width = `${totalWidth}px`;

  gsap.to(track, {
    x: -(totalWidth - window.innerWidth),
    ease: 'none',
    scrollTrigger: {
      trigger: section,
      start: 'top top',
      end: `+=${totalWidth - window.innerWidth}`,
      pin: true,
      scrub: 1,
      anticipatePin: 1,
      snap: {
        snapTo: 1 / (slides.length - 1),
        duration: { min: 0.2, max: 0.5 },
        ease: 'expo.inOut',
      },
    }
  });

  // Animar conteúdo dentro de cada slide conforme entra
  slides.forEach((slide, i) => {
    if (i === 0) return;

    gsap.from(slide.querySelectorAll('.slide-content > *'), {
      y: 40,
      opacity: 0,
      duration: 0.6,
      stagger: 0.08,
      ease: 'expo.out',
      scrollTrigger: {
        trigger: slide,
        containerAnimation: track._gsap?.id, // referencia ao scroll horizontal
        start: 'left 80%',
        toggleActions: 'play none none reverse',
      }
    });
  });
}
```

### Morfismo de Texto no Scroll (Pinned)

```javascript
// Técnica: fixar a seção e animar o texto conforme scrubbing
const textPhases = [
  'Começamos com uma ideia.',
  'A ideia ganha forma.',
  'A forma ganha movimento.',
  'O movimento conta a história.',
];

let currentPhase = 0;
const textEl = document.querySelector('.morphing-text');

ScrollTrigger.create({
  trigger: '.text-morph-section',
  start: 'top top',
  end: '+=300%',
  pin: true,
  scrub: true,
  onUpdate: (self) => {
    const newPhase = Math.floor(self.progress * textPhases.length);
    const clampedPhase = Math.min(newPhase, textPhases.length - 1);

    if (clampedPhase !== currentPhase) {
      currentPhase = clampedPhase;

      gsap.fromTo(textEl,
        { opacity: 0, y: 20, filter: 'blur(8px)' },
        { opacity: 1, y: 0, filter: 'blur(0px)', duration: 0.4 }
      );

      textEl.textContent = textPhases[currentPhase];
    }
  }
});
```

### Progress Line no Scroll

```css
/* Linha de progresso que aparece conforme scroll */
.scroll-progress-line {
  position: fixed;
  top: 0; left: 0;
  height: 2px;
  background: var(--accent);
  transform-origin: left center;
  transform: scaleX(0);
  z-index: 999;
}
```

```javascript
gsap.to('.scroll-progress-line', {
  scaleX: 1,
  ease: 'none',
  scrollTrigger: {
    scrub: 0.3,
    start: 'top top',
    end: 'bottom bottom',
  }
});
```

---

## 10. Microinterações que Impressionam

### Botão com Ripple + Estado de Loading

```javascript
class ProButton {
  constructor(selector) {
    document.querySelectorAll(selector).forEach(btn => {
      btn.addEventListener('click', (e) => this.onClick(e, btn));
    });
  }

  onClick(e, btn) {
    this.createRipple(e, btn);

    if (btn.dataset.async) {
      this.setLoading(btn, true);
      setTimeout(() => {
        this.setLoading(btn, false);
        this.setSuccess(btn);
      }, 2000);
    }
  }

  createRipple(e, btn) {
    const rect = btn.getBoundingClientRect();
    const ripple = document.createElement('span');
    const size = Math.max(rect.width, rect.height) * 2;

    ripple.style.cssText = `
      position: absolute;
      width: ${size}px; height: ${size}px;
      left: ${e.clientX - rect.left - size/2}px;
      top: ${e.clientY - rect.top - size/2}px;
      border-radius: 50%;
      background: rgba(255,255,255,0.15);
      pointer-events: none;
    `;

    btn.style.position = 'relative';
    btn.style.overflow = 'hidden';
    btn.appendChild(ripple);

    gsap.fromTo(ripple,
      { scale: 0, opacity: 1 },
      {
        scale: 1, opacity: 0, duration: 0.6,
        ease: 'power2.out',
        onComplete: () => ripple.remove()
      }
    );
  }

  setLoading(btn, isLoading) {
    if (isLoading) {
      btn.dataset.originalText = btn.textContent;
      btn.textContent = '';
      btn.classList.add('is-loading');
      btn.disabled = true;
    } else {
      btn.textContent = btn.dataset.originalText;
      btn.classList.remove('is-loading');
      btn.disabled = false;
    }
  }

  setSuccess(btn) {
    btn.textContent = '✓ Done';
    btn.classList.add('is-success');
    setTimeout(() => {
      btn.textContent = btn.dataset.originalText;
      btn.classList.remove('is-success');
    }, 2000);
  }
}
```

### Hover 3D Tilt Avançado

```javascript
class TiltEffect {
  constructor(selector, options = {}) {
    const defaults = {
      tiltStrength: 12,
      scaleOnHover: 1.02,
      glare: true,
      glareOpacity: 0.15,
      perspective: 1000,
      transitionDuration: 0.6,
    };

    this.opts = { ...defaults, ...options };
    this.elements = document.querySelectorAll(selector);
    this.init();
  }

  init() {
    this.elements.forEach(el => {
      el.style.transformStyle = 'preserve-3d';
      el.style.willChange = 'transform';

      if (this.opts.glare) {
        const glare = document.createElement('div');
        glare.className = 'tilt-glare';
        glare.style.cssText = `
          position: absolute; inset: 0;
          pointer-events: none;
          border-radius: inherit;
          overflow: hidden;
          z-index: 1;
        `;
        const glareInner = document.createElement('div');
        glareInner.style.cssText = `
          position: absolute;
          top: -50%; left: -50%;
          width: 200%; height: 200%;
          background: radial-gradient(ellipse at center, rgba(255,255,255,${this.opts.glareOpacity}) 0%, transparent 60%);
          transform: translate(-100%, -100%) rotate(0deg);
          transition: opacity 0.3s ease;
          opacity: 0;
        `;
        glare.appendChild(glareInner);
        el.style.position = 'relative';
        el.appendChild(glare);
      }

      el.addEventListener('mousemove', (e) => this.onMove(e, el));
      el.addEventListener('mouseenter', (e) => this.onEnter(e, el));
      el.addEventListener('mouseleave', (e) => this.onLeave(el));
    });
  }

  onMove(e, el) {
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;

    const tiltX = y * this.opts.tiltStrength;
    const tiltY = x * -this.opts.tiltStrength;

    gsap.to(el, {
      rotationX: tiltX,
      rotationY: tiltY,
      transformPerspective: this.opts.perspective,
      duration: 0.3,
      ease: 'power2.out',
    });

    const glareInner = el.querySelector('.tilt-glare > div');
    if (glareInner) {
      const angle = Math.atan2(y, x) * (180 / Math.PI);
      gsap.to(glareInner, {
        rotation: angle,
        x: `${x * 20}%`,
        y: `${y * 20}%`,
        opacity: 1,
        duration: 0.3,
      });
    }
  }

  onEnter(e, el) {
    gsap.to(el, { scale: this.opts.scaleOnHover, duration: 0.3, ease: 'power2.out' });
  }

  onLeave(el) {
    gsap.to(el, {
      rotationX: 0, rotationY: 0, scale: 1,
      duration: this.opts.transitionDuration,
      ease: 'elastic.out(1, 0.4)',
    });

    const glareInner = el.querySelector('.tilt-glare > div');
    if (glareInner) gsap.to(glareInner, { opacity: 0, duration: 0.4 });
  }
}

new TiltEffect('.card-3d', { tiltStrength: 10, glareOpacity: 0.12 });
```

---

## 11. Easing Avançado — A Curva Certa

A maior diferença perceptível nas animações está no easing. Nunca use o padrão.

### Mapa de Easing por Contexto

```javascript
const easingMap = {
  // ─── ENTRADAS ───
  'elemento-aparece-na-tela': 'expo.out',        // desacelera dramáticamente
  'modal-abre': 'back.out(1.5)',                 // pequeno overshoot
  'tooltip-aparece': 'power2.out',               // sutil
  'notificacao-entra': [0.34, 1.56, 0.64, 1],    // spring (cubic-bezier)

  // ─── SAÍDAS ───
  'elemento-sai-da-tela': 'expo.in',             // acelera dramáticamente
  'modal-fecha': 'power3.in',                    // rápido e direto
  'tooltip-some': 'power2.in',                   // sutil

  // ─── HOVER / INTERAÇÃO ───
  'scale-hover': 'back.out(2)',                  // overshoot assertivo
  'slide-hover': 'expo.out',                     // imediato e natural
  'rotation-hover': 'elastic.out(1, 0.4)',       // físico

  // ─── SCROLL / PINNED ───
  'scrub': 'none',                               // sempre 'none' para scrub!
  'snap-into-place': 'expo.inOut',               // suave dos dois lados
  'parallax': 'none',                            // sempre 'none'

  // ─── ATENÇÃO ───
  'pulse-atencao': 'sine.inOut',                 // orgânico em loop
  'shake-erro': 'power2.inOut',                  // assertivo

  // ─── SAÍDA DE PÁGINA ───
  'page-exit': 'expo.inOut',                     // cinematográfico
};
```

### Custom Easing com CustomEase (GSAP Club)

```javascript
import { CustomEase } from 'gsap/CustomEase';
gsap.registerPlugin(CustomEase);

// Criar easings customizados que definem sua marca
CustomEase.create('brand-in', 'M0,0 C0.06,0 0.15,0.4 0.2,0.6 0.26,0.8 0.4,1 1,1');
CustomEase.create('brand-spring', 'M0,0 C0.14,0 0.4,1.2 0.6,1.1 0.8,1.0 1,1');

// Usar como qualquer outro ease
gsap.to('.hero', { y: 0, ease: 'brand-spring', duration: 1 });
```

### Timing Guide por Peso Visual

```javascript
// Regra: duração ∝ distância percebida e importância

const timingGuide = {
  // Elementos pequenos / detalhes
  'icone-aparece': 150,          // 150ms
  'tooltip': 200,                // 200ms
  'badge': 200,                  // 200ms

  // Elementos médios / componentes
  'botao-hover': 200,            // 200ms
  'card-hover': 300,             // 300ms
  'dropdown-abre': 250,          // 250ms
  'tab-switch': 300,             // 300ms

  // Elementos grandes / seções
  'modal-abre': 400,             // 400ms
  'panel-slide': 400,            // 400ms
  'hero-entrada': 800,           // 800ms (+ stagger nos filhos)

  // Transições de página
  'page-exit': 600,              // 600ms
  'page-enter': 700,             // 700ms

  // Loops / background
  'float-loop': 4000,            // 4s
  'gradient-shift': 8000,        // 8s
  'grain-step': 500,             // 500ms (steps())
};
```

---

## 12. Paletas e Tipografia que Elevam

Design e motion são inseparáveis. Uma paleta genérica destrói qualquer animação.

### Paletas Pro (Fugir do Genérico)

```css
/* ─── TEMA 1: Agência Editorial Dark ─── */
--bg: #080808;
--text: #f2ede6;
--accent: #c8f53b;    /* verde eletrônico */
--muted: #3a3a38;

/* ─── TEMA 2: Studio Minimalista Claro ─── */
--bg: #f5f0eb;
--text: #1a1714;
--accent: #e84c30;    /* vermelho terracota */
--muted: #c8c0b8;

/* ─── TEMA 3: Tech Precisa Dark ─── */
--bg: #050510;
--text: #e8eaf6;
--accent: #4fc3f7;    /* azul elétrico */
--muted: #1a1a3e;

/* ─── TEMA 4: Luxury Neutral ─── */
--bg: #f8f5f0;
--text: #2c2520;
--accent: #c9a96e;    /* dourado envelhecido */
--muted: #e8e0d5;

/* ─── TEMA 5: Brutalist ─── */
--bg: #ffffff;
--text: #000000;
--accent: #ff3300;    /* vermelho cru */
--muted: #888888;
```

### Tipografia que Diferencia

```css
/* NÃO USE: Inter, Roboto, Arial, Space Grotesk, Outfit */

/* ─── Display (Títulos) ─── */
/* Syne — geométrica, moderna: */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&display=swap');

/* Playfair Display — editorial, luxo: */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;1,700&display=swap');

/* Bebas Neue — condensada, impactante: */
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');

/* DM Serif Display — refinado: */
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&display=swap');

/* ─── Mono (Detalhes, Tags, Código) ─── */
/* DM Mono: */
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital@0;1&display=swap');

/* JetBrains Mono: */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono&display=swap');

/* ─── Aplicação ─── */
.heading { font-family: 'Syne', sans-serif; font-weight: 800; letter-spacing: -0.04em; }
.detail  { font-family: 'DM Mono', monospace; font-size: 0.7rem; letter-spacing: 0.15em; text-transform: uppercase; }
```

---

## 13. Prompts Pro para o Claude

A qualidade do output do Claude depende da qualidade do prompt. Use estas estruturas:

### Prompt: Página Hero Completa

```
Crie uma hero section em HTML/CSS/JS puro com o seguinte nível de qualidade:

ESTÉTICA: [editorial dark / minimal claro / brutalist / luxury]
CORES: bg [#xxx], texto [#xxx], accent [#xxx]
FONTE TÍTULO: [Syne / Bebas Neue / Playfair Display]
FONTE DETALHES: [DM Mono / JetBrains Mono]

ANIMAÇÕES OBRIGATÓRIAS (nível Awwwards):
1. Loader com contador 0→100 e exit com clip-path
2. Após loader: nav desliza de cima, eyebrow da esquerda, título linha por linha
   (cada linha no overflow: hidden + transform, NÃO opacity simples),
   subtitle fade, CTA scale + y, imagem scale reverso
3. BG text com parallax no scroll (scrub)
4. Grain overlay animado (SVG noise + animation steps)
5. Cursor customizado com dot + ring LERP, que expande em hover de links

REGRAS:
- Usar GSAP 3 via CDN
- Nenhum fade simples isolado — sempre combinar opacity + transform
- Nenhuma duração genérica — cada elemento tem sua própria timing
- ease 'expo.out' para entradas, 'expo.inOut' para transitions de página
- Comentários explicando a intenção de cada bloco de animação
- Google Fonts via link no head
- Sem frameworks CSS (Tailwind, Bootstrap etc.)
```

### Prompt: Card Hover Profissional

```
Crie um componente de card em HTML/CSS/JS com hover de nível profissional.

O hover deve:
1. Tilt 3D (perspectiva + rotateX/Y proporcional à posição do mouse)
2. Glare/shine que segue o mouse dentro do card
3. Título desloca levemente no eixo Y
4. Tag/categoria muda de cor com transição
5. Botão/arrow rotaciona 45° com spring
6. Background sutil scale reverso (zoom out enquanto o card faz zoom in)
7. Box shadow progressivo com blur e cor do accent

REGRAS:
- willChange: transform apenas durante hover (adicionar no enter, remover no leave)
- Usar cubic-bezier customizado, não 'ease' padrão
- Retorno ao estado normal com elastic.out para naturalidade
- Não usar !important
- Performance: só transform e opacity, nenhum reflow
```

### Prompt: Animação de Scroll Narrativa

```
Crie uma seção com scroll storytelling profissional em HTML/CSS/GSAP.

A seção deve:
1. Ser fixada (pinned) por 4 "fases" equivalentes a 400vh de scroll
2. Em cada fase, um texto diferente aparece com blur fade (opacity + filter: blur)
3. Um elemento visual (círculo, linha, shape SVG) se transforma entre fases
4. Barra de progresso lateral que indica qual fase o usuário está
5. A transição entre fases deve ser acionada por ScrollTrigger com scrub suave

REGRAS:
- Pin via ScrollTrigger, NÃO position: sticky manual
- scrub: 1 para suavidade
- onUpdate para detectar mudança de fase
- Cada transição de fase com 0.4s expo.out
- Fase ativa destacada na barra lateral
- Funcionar bem em mobile
```

---

## 14. Checklist Awwwards

Antes de considerar o site pronto, verifique:

### Design Visual
```
□ Há uma fonte display única e marcante (não Inter/Roboto)?
□ A paleta tem dominância clara? (1 cor principal + 1 accent)
□ Há grain overlay ou textura que adiciona profundidade?
□ O layout tem assimetria ou quebra de grid intencional?
□ Os espaços em branco são generosos e respirados?
□ Blend modes ou mix-blend-mode em algum elemento?
```

### Motion
```
□ O loader existe e prepara o usuário para a experiência?
□ A hero tem uma sequência orquestrada (não tudo junto)?
□ Os títulos revelam por overflow/clip-path, não só por opacity?
□ Cada elemento tem sua própria combinação de propriedades animadas?
□ Duração e easing são customizados por contexto?
□ Há pelo menos um elemento com scrub no scroll?
□ Hoveres têm personalidade e intenção (não só scale/opacity)?
□ Cursor customizado com LERP?
□ prefers-reduced-motion implementado?
```

### Técnico
```
□ Apenas transform e opacity nas animações críticas?
□ will-change usado cirurgicamente (não em tudo)?
□ Animações pausadas fora do viewport?
□ FPS estável (verificar em CPU throttling no DevTools)?
□ Nenhum CLS (Cumulative Layout Shift) causado pelas animações?
□ GSAP/bibliotecas carregando de CDN confiável?
□ Fontes com font-display: swap para evitar FOUT?
```

### UX
```
□ Animações têm propósito (guiam, informam, encantam)?
□ Nenhuma animação bloqueia interação do usuário?
□ Loading states em ações assíncronas?
□ Feedback visual imediato em cliques (<100ms)?
□ Mobile testado? Animações reduzidas onde necessário?
```

---

## 📁 Arquivo de Referência: `demo.html`

> O repositório inclui `demo.html` — uma página funcional que demonstra todas essas técnicas em conjunto. Abra-a no browser e inspecione o código para ver os padrões em ação.

---

## 🤝 Contribuindo

PRs com exemplos de alto nível são bem-vindos. Por favor:
- Inclua sempre o `demo` funcional junto ao código explicado
- Comente a **intenção** de cada bloco, não só o "como"
- Teste em dispositivos reais antes de submeter

---

<div align="center">

**Feito com obsessão pelos detalhes — para a comunidade**  
*MIT License · Versão 2.0 Pro*

</div>
