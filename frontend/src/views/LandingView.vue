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
            <h4 class="font-semibold text-gray-800 mb-2">1. Upload Docs</h4>
            <p class="text-sm text-gray-500">Upload PDFs, DOCX, or paste URLs. SupportAI chunks and indexes them automatically.</p>
          </div>
          <div class="bg-white rounded-xl p-6 border border-gray-200 text-center">
            <div class="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
              </svg>
            </div>
            <h4 class="font-semibold text-gray-800 mb-2">2. AI Learns</h4>
            <p class="text-sm text-gray-500">RAG pipeline embeds your content so the AI answers only from your knowledge base.</p>
          </div>
          <div class="bg-white rounded-xl p-6 border border-gray-200 text-center">
            <div class="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
              </svg>
            </div>
            <h4 class="font-semibold text-gray-800 mb-2">3. Embed</h4>
            <p class="text-sm text-gray-500">Copy one script tag into your site. Customers get instant AI support.</p>
          </div>
          <div class="bg-white rounded-xl p-6 border border-indigo-200 text-center bg-indigo-50/30">
            <div class="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center mx-auto mb-4">
              <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 0 0 1.5-.189m-1.5.189a6.01 6.01 0 0 1-1.5-.189m3.75 7.478a12.06 12.06 0 0 1-4.5 0m3.75 2.383a14.406 14.406 0 0 1-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 1 0-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
              </svg>
            </div>
            <h4 class="font-semibold text-indigo-700 mb-2">4. AI Improves</h4>
            <p class="text-sm text-indigo-600/70">Detects knowledge gaps and tells you exactly what to add. Gets smarter over time.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- What Makes Us Different -->
    <section class="py-20">
      <div class="max-w-6xl mx-auto px-6">
        <h3 class="text-2xl font-bold text-gray-900 text-center mb-4">What Makes SupportAI Different</h3>
        <p class="text-gray-500 text-center mb-12 max-w-xl mx-auto">Most chatbot builders just answer questions. SupportAI actively helps you build a better knowledge base.</p>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div class="border border-indigo-200 bg-indigo-50/30 rounded-xl p-6">
            <h4 class="font-semibold text-indigo-800 mb-2">Knowledge Gap Detection</h4>
            <p class="text-sm text-gray-600 mb-3">Inspired by active learning research. The AI analyzes low-confidence responses and escalated conversations to identify topics your docs don't cover.</p>
            <p class="text-sm text-gray-500 italic">"Customers keep asking about refund policies, but your knowledge base has no content about it."</p>
          </div>
          <div class="border border-indigo-200 bg-indigo-50/30 rounded-xl p-6">
            <h4 class="font-semibold text-indigo-800 mb-2">Auto-FAQ Generator</h4>
            <p class="text-sm text-gray-600 mb-3">AI reads your uploaded documents and automatically suggests FAQ pairs. Review, accept, or reject — no manual writing needed.</p>
            <p class="text-sm text-gray-500 italic">"Generated 8 FAQs from your product documentation. Accept the ones you want."</p>
          </div>
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
      </div>
    </section>

    <!-- CTA -->
    <section class="py-20">
      <div class="max-w-2xl mx-auto px-6 text-center">
        <h3 class="text-2xl font-bold text-gray-900 mb-4">Ready to build your AI support agent?</h3>
        <p class="text-gray-500 mb-8">Sign up, upload your docs, and go live in minutes.</p>
        <router-link to="/register" class="px-8 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition">
          Get Started
        </router-link>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-gray-200 py-8">
      <div class="max-w-6xl mx-auto px-6 text-center text-sm text-gray-400">
        SupportAI — AI Customer Support Agent Builder
      </div>
    </footer>
  </div>
</template>

<script setup>
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
