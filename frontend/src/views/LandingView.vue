<template>
  <div class="landing-page min-h-screen bg-white">
    <!-- Navbar -->
    <nav class="landing-nav">
      <div class="landing-nav-inner">
        <router-link to="/" class="landing-brand"><span class="landing-brand-mark">S</span><span>Support<span>AI</span></span></router-link>
        <div class="landing-nav-links">
          <a href="#how-it-works">How it works</a>
          <a href="#features">Platform</a>
          <router-link to="/login" class="landing-sign-in">Sign in</router-link>
          <router-link to="/register" class="landing-nav-cta">Create workspace <span aria-hidden="true">↗</span></router-link>
        </div>
      </div>
    </nav>

    <!-- Product-first hero -->
    <section class="landing-hero">
      <div class="landing-hero-copy">
        <div class="landing-pill"><span></span> AI support that learns from every question</div>
        <h2>Support that gets<br /><em>smarter over time.</em></h2>
        <p>Turn your knowledge into a thoughtful support agent. Resolve routine questions instantly, surface what your docs are missing, and keep your team in control.</p>
        <div class="landing-hero-actions">
          <router-link to="/register" class="landing-primary-cta">Build your agent <span aria-hidden="true">→</span></router-link>
          <a href="#how-it-works" class="landing-text-cta">Explore the platform <span aria-hidden="true">↓</span></a>
        </div>
        <div class="landing-proof"><span class="landing-proof-dot"></span> Private by design <span class="landing-proof-divider">/</span> Bring your own model key <span class="landing-proof-divider">/</span> One-line install</div>
      </div>

      <div class="landing-demo-wrap">
        <div class="landing-demo-glow" aria-hidden="true"></div>
        <div class="landing-demo-window">
          <div class="landing-demo-toolbar"><div class="landing-window-dots"><i></i><i></i><i></i></div><span>store.example.com</span><span class="landing-demo-live"><i></i> LIVE PREVIEW</span></div>
          <div class="landing-demo-content">
            <div class="landing-demo-site-head"><span>MONO / GOODS</span><span>SHOP&nbsp;&nbsp; ABOUT&nbsp;&nbsp; JOURNAL</span></div>
            <div class="landing-demo-site-copy"><span>OBJECTS FOR SLOW LIVING</span><strong>Made for the<br />everyday ritual.</strong><i></i><i></i></div>
            <div class="landing-demo-chat">
              <div class="landing-demo-chat-head"><span class="landing-demo-avatar">S</span><span><b>Studio assistant</b><small><i></i> Here to help</small></span><span class="landing-demo-menu">•••</span></div>
              <div class="landing-demo-chat-body"><small>EXAMPLE CONVERSATION</small><div class="landing-demo-bubble">Hi there. Looking for a little more information?</div><div class="landing-demo-user-bubble">How long does shipping take?</div><div class="landing-demo-bubble">Most orders arrive in 3–5 business days. I can help you track yours, too.</div><div class="landing-demo-source"><span>✦</span> Answer grounded in Shipping guide</div></div>
              <div class="landing-demo-input">Ask anything <span>↑</span></div>
            </div>
          </div>
        </div>
        <div class="landing-float-card"><span class="landing-float-icon">✦</span><span><b>Knowledge, connected</b><small>Answers with real sources</small></span><span class="landing-float-check">✓</span></div>
      </div>
    </section>

    <!-- How It Works -->
    <section id="how-it-works" class="landing-process bg-gray-50 py-20">
      <div class="max-w-6xl mx-auto px-6">
        <h3 class="text-2xl font-bold text-gray-900 text-center mb-12">How It Works</h3>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="bg-white rounded-xl p-6 border border-gray-200 text-center">
            <div class="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <div class="absolute -bottom-6 -left-4 hidden rounded-xl border border-white/10 bg-stone-900/90 px-4 py-3 text-xs text-white shadow-xl sm:block"><span class="mr-2 text-emerald-400">●</span>Knowledge gaps help you improve</div>
          </div>
        </div>
      </section>

      <section id="how-it-works" class="bg-white py-20 sm:py-24">
        <div class="mx-auto max-w-7xl px-5 sm:px-8">
          <div class="mx-auto max-w-2xl text-center"><p class="text-sm font-semibold uppercase tracking-[0.16em] text-blue-600">Simple setup</p><h2 class="mt-3 text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl">From documents to helpful support</h2><p class="mt-4 text-base leading-7 text-stone-500">Give your assistant useful information, review how it responds, and add it to your website.</p></div>
          <div class="mt-12 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <article v-for="(step, index) in steps" :key="step.title" class="relative rounded-2xl border border-stone-200 bg-white p-6 transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg hover:shadow-blue-950/5">
              <div class="flex items-center justify-between"><span class="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24" aria-hidden="true"><path v-if="index === 0" stroke-linecap="round" stroke-linejoin="round" d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/><path v-else-if="index === 1" stroke-linecap="round" stroke-linejoin="round" d="M12 3v3m0 12v3m9-9h-3M6 12H3m15.36-6.36-2.12 2.12M7.76 16.24l-2.12 2.12m12.72 0-2.12-2.12M7.76 7.76 5.64 5.64M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/><path v-else-if="index === 2" stroke-linecap="round" stroke-linejoin="round" d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6Zm0 0v6h6M8 14h8m-8 4h8"/><path v-else stroke-linecap="round" stroke-linejoin="round" d="M5 12h14m-6-6 6 6-6 6"/></svg></span><span class="text-xs font-bold tracking-[0.14em] text-stone-300">0{{ index + 1 }}</span></div>
              <h3 class="mt-5 text-base font-semibold text-stone-900">{{ step.title }}</h3><p class="mt-2 text-sm leading-6 text-stone-500">{{ step.desc }}</p>
            </article>
          </div>
        </div>
      </section>

    <!-- Features -->
    <section id="features" class="landing-features bg-gray-50 py-20">
      <div class="max-w-6xl mx-auto px-6">
        <p class="landing-section-kicker">THE SUPPORTAI PLATFORM</p>
        <h3 class="text-2xl font-bold text-gray-900 mb-12">Everything your support loop needs.</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div v-for="feature in features" :key="feature.title" class="bg-white p-5 rounded-xl border border-gray-200">
            <h4 class="font-semibold text-gray-800 mb-1">{{ feature.title }}</h4>
            <p class="text-sm text-gray-500">{{ feature.desc }}</p>
          </div>
        </div>
      </section>

      <section class="px-5 py-20 sm:px-8 sm:py-24">
        <div class="mx-auto max-w-5xl overflow-hidden rounded-3xl border border-blue-100 bg-gradient-to-br from-blue-50 via-white to-blue-100 px-6 py-12 text-center text-stone-900 shadow-lg shadow-blue-950/5 sm:px-12 sm:py-16"><p class="text-sm font-semibold text-blue-700">Start building today</p><h2 class="mx-auto mt-3 max-w-2xl text-3xl font-bold tracking-tight sm:text-4xl">Give customers answers, and your team a clearer next step.</h2><p class="mx-auto mt-4 max-w-xl text-sm leading-6 text-stone-600 sm:text-base">Set up a workspace, add your support content, and try the assistant with your own questions.</p><router-link to="/register" class="mt-8 inline-flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700">Get started <span aria-hidden="true">→</span></router-link></div>
      </section>
    </main>

    <footer class="border-t border-stone-200 bg-white">
      <div class="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-7 text-sm text-stone-500 sm:flex-row sm:items-center sm:justify-between sm:px-8"><router-link to="/" class="font-semibold text-stone-800">Support<span class="text-blue-600">AI</span></router-link><span>AI support built around your knowledge.</span><span>© {{ new Date().getFullYear() }} SupportAI</span></div>
    </footer>
  </div>
</template>

<script setup>
const steps = [
  { title: 'Add your knowledge', desc: 'Upload PDF or DOCX files, or add URLs for your assistant to use.' },
  { title: 'Try real questions', desc: 'Test the assistant and see whether its answers are useful to your customers.' },
  { title: 'Review what is missing', desc: 'Use conversations and knowledge gaps to spot topics that need better coverage.' },
  { title: 'Add it to your website', desc: 'Copy the embed code and place the chat widget on your site.' },
]

const features = [
  { title: 'Grounded answers', desc: 'Retrieval-Augmented Generation keeps answers tied to your uploaded source material and flags when information is missing.' },
  { title: 'Multi-Provider LLM Support', desc: 'Choose between Google Gemini, OpenAI, or Anthropic. Bring your own API key.' },
  { title: 'Knowledge Gap Detection', desc: 'AI identifies what your docs don\'t cover and suggests exactly what content to add.' },
  { title: 'Auto-FAQ Generator', desc: 'AI reads your documents and auto-generates FAQ pairs. Review and accept with one click.' },
  { title: 'Multi-Format Upload', desc: 'Supports PDF, DOCX, TXT files, and website URLs as knowledge sources.' },
  { title: 'Intent-aware handoff', desc: 'Respect explicit requests for a person without turning every low-confidence answer into a false escalation.' },
  { title: 'Embeddable Widget', desc: 'Add a chat widget to any website with a single script tag. Fully customizable.' },
  { title: 'Team Collaboration', desc: 'Invite agents and viewers with role-based access to manage support together.' },
  { title: 'Analytics Dashboard', desc: 'Track conversations, confidence scores, escalations, and document status at a glance.' },
]
</script>
