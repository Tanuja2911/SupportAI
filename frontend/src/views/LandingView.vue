<template>
  <div class="min-h-screen overflow-hidden bg-white text-stone-900">
    <nav class="relative z-10 border-b border-white/10 bg-stone-950 text-white">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
        <router-link to="/" class="flex items-center gap-2.5" aria-label="SupportAI home">
          <span class="flex h-9 w-9 items-center justify-center rounded-xl bg-pink-500 shadow-lg shadow-pink-500/25">
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.5a2.25 2.25 0 0 0-2.25-2.25H6A2.25 2.25 0 0 0 3.75 8.5v7A2.25 2.25 0 0 0 6 17.75h2.25L12 21l3.75-3.25H18A2.25 2.25 0 0 0 20.25 15.5v-7Z"/><path stroke-linecap="round" d="M8 10h8M8 13.5h5"/></svg>
          </span>
          <span class="text-lg font-bold tracking-tight">Support<span class="text-pink-300">AI</span></span>
        </router-link>
        <div class="flex items-center gap-3 sm:gap-6">
          <a href="#how-it-works" class="hidden text-sm text-stone-300 transition hover:text-white sm:inline">How it works</a>
          <router-link to="/login" class="text-sm font-medium text-stone-300 transition hover:text-white">Sign in</router-link>
          <router-link to="/register" class="rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-stone-950 transition hover:bg-pink-50">Get started <span aria-hidden="true">→</span></router-link>
        </div>
      </div>
    </nav>

    <main>
      <section class="relative isolate overflow-hidden bg-stone-950 text-white">
        <div class="pointer-events-none absolute -left-40 top-8 h-96 w-96 rounded-full bg-pink-600/20 blur-3xl"></div>
        <div class="pointer-events-none absolute -right-32 top-32 h-96 w-96 rounded-full bg-pink-500/15 blur-3xl"></div>
        <div class="relative mx-auto grid max-w-7xl items-center gap-14 px-5 py-16 sm:px-8 sm:py-24 lg:grid-cols-[1.02fr_.98fr] lg:gap-10 lg:py-28">
          <div class="max-w-2xl">
            <div class="inline-flex items-center gap-2 rounded-full border border-pink-300/20 bg-pink-300/10 px-3.5 py-1.5 text-xs font-medium text-pink-100">
              <span class="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
              Support that learns from your knowledge
            </div>
            <h1 class="mt-7 text-4xl font-bold leading-[1.08] tracking-tight sm:text-5xl lg:text-6xl">Helpful answers, from the knowledge <span class="bg-gradient-to-r from-pink-300 to-pink-300 bg-clip-text text-transparent">you already have.</span></h1>
            <p class="mt-6 max-w-xl text-base leading-7 text-stone-300 sm:text-lg">Turn your documents into a support assistant. Find unanswered questions, improve your knowledge base, and add a chat widget to your website.</p>
            <div class="mt-8 flex flex-col gap-3 sm:flex-row">
              <router-link to="/register" class="inline-flex items-center justify-center gap-2 rounded-xl bg-pink-500 px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-pink-500/25 transition hover:bg-pink-400">Create your workspace <span aria-hidden="true">→</span></router-link>
              <a href="#how-it-works" class="inline-flex items-center justify-center rounded-xl border border-white/15 px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-white/5">See how it works</a>
            </div>
            <div class="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-xs text-stone-400">
              <span class="inline-flex items-center gap-2"><span class="text-pink-400">✓</span> Use your own support content</span>
              <span class="inline-flex items-center gap-2"><span class="text-pink-400">✓</span> Add to your site with an embed code</span>
            </div>
          </div>

          <div class="relative mx-auto w-full max-w-xl">
            <div class="absolute -inset-4 rounded-[2rem] bg-gradient-to-br from-pink-500/20 to-pink-500/10 blur-2xl"></div>
            <div class="relative overflow-hidden rounded-2xl border border-white/10 bg-white text-stone-900 shadow-2xl shadow-black/30">
              <div class="flex items-center justify-between border-b border-stone-100 px-5 py-4">
                <div class="flex items-center gap-3"><span class="flex h-9 w-9 items-center justify-center rounded-xl bg-pink-50 text-pink-600"><svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.5a2.25 2.25 0 0 0-2.25-2.25H6A2.25 2.25 0 0 0 3.75 8.5v7A2.25 2.25 0 0 0 6 17.75h2.25L12 21l3.75-3.25H18a2.25 2.25 0 0 0 2.25-2.25v-7Z"/></svg></span><div><p class="text-sm font-semibold">Support Assistant</p><p class="text-xs text-stone-400">Your knowledge, ready to help</p></div></div>
                <span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700"><span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Online</span>
              </div>
              <div class="space-y-5 bg-pink-50 px-5 py-6 sm:px-7 sm:py-8">
                <div class="max-w-[85%] rounded-2xl rounded-tl-md border border-stone-100 bg-white p-4 shadow-sm"><p class="text-xs font-medium text-pink-600">Support Assistant</p><p class="mt-2 text-sm leading-6 text-stone-700">Hi! Ask me about your product, policies, or getting started. I’ll look for the answer in the support information provided.</p></div>
                <div class="ml-auto max-w-[78%] rounded-2xl rounded-tr-md bg-pink-600 p-4 text-white shadow-sm"><p class="text-xs text-pink-100">You</p><p class="mt-2 text-sm leading-6">How can I reset my password?</p></div>
                <div class="max-w-[85%] rounded-2xl rounded-tl-md border border-stone-100 bg-white p-4 shadow-sm"><p class="text-xs font-medium text-pink-600">Support Assistant</p><p class="mt-2 text-sm leading-6 text-stone-700">Open account settings, choose <strong>Security</strong>, then select <strong>Reset password</strong>. A reset link will be sent to your email.</p><div class="mt-3 flex items-center gap-1.5 text-[11px] text-stone-400"><span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span> Based on your support content</div></div>
              </div>
              <div class="border-t border-stone-100 bg-white p-4"><div class="flex items-center justify-between rounded-xl border border-stone-200 px-4 py-3 text-sm text-stone-400"><span>Type your question...</span><span class="flex h-8 w-8 items-center justify-center rounded-lg bg-pink-600 text-white"><svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m5 12 14-7-4 14-3.5-5L5 12Zm6.5 2L19 5"/></svg></span></div></div>
            </div>
            <div class="absolute -bottom-6 -left-4 hidden rounded-xl border border-white/10 bg-stone-900/90 px-4 py-3 text-xs text-white shadow-xl sm:block"><span class="mr-2 text-emerald-400">●</span>Knowledge gaps help you improve</div>
          </div>
        </div>
      </section>

      <section id="how-it-works" class="bg-white py-20 sm:py-24">
        <div class="mx-auto max-w-7xl px-5 sm:px-8">
          <div class="mx-auto max-w-2xl text-center"><p class="text-sm font-semibold uppercase tracking-[0.16em] text-pink-600">Simple setup</p><h2 class="mt-3 text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl">From documents to helpful support</h2><p class="mt-4 text-base leading-7 text-stone-500">Give your assistant useful information, review how it responds, and add it to your website.</p></div>
          <div class="mt-12 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            <article v-for="(step, index) in steps" :key="step.title" class="relative rounded-2xl border border-stone-200 bg-white p-6 transition hover:-translate-y-1 hover:border-pink-200 hover:shadow-lg hover:shadow-pink-950/5">
              <div class="flex items-center justify-between"><span class="flex h-11 w-11 items-center justify-center rounded-xl bg-pink-50 text-pink-600"><svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24" aria-hidden="true"><path v-if="index === 0" stroke-linecap="round" stroke-linejoin="round" d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M4 15v4a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-4"/><path v-else-if="index === 1" stroke-linecap="round" stroke-linejoin="round" d="M12 3v3m0 12v3m9-9h-3M6 12H3m15.36-6.36-2.12 2.12M7.76 16.24l-2.12 2.12m12.72 0-2.12-2.12M7.76 7.76 5.64 5.64M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/><path v-else-if="index === 2" stroke-linecap="round" stroke-linejoin="round" d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-6-6Zm0 0v6h6M8 14h8m-8 4h8"/><path v-else stroke-linecap="round" stroke-linejoin="round" d="M5 12h14m-6-6 6 6-6 6"/></svg></span><span class="text-xs font-bold tracking-[0.14em] text-stone-300">0{{ index + 1 }}</span></div>
              <h3 class="mt-5 text-base font-semibold text-stone-900">{{ step.title }}</h3><p class="mt-2 text-sm leading-6 text-stone-500">{{ step.desc }}</p>
            </article>
          </div>
        </div>
      </section>

      <section class="bg-pink-50 py-20 sm:py-24">
        <div class="mx-auto max-w-7xl px-5 sm:px-8">
          <div class="grid items-start gap-12 lg:grid-cols-[.8fr_1.2fr]">
            <div class="lg:sticky lg:top-12"><p class="text-sm font-semibold uppercase tracking-[0.16em] text-pink-600">Built for better answers</p><h2 class="mt-3 text-3xl font-bold tracking-tight text-stone-900 sm:text-4xl">A support assistant you can keep improving.</h2><p class="mt-5 text-base leading-7 text-stone-500">SupportAI combines your knowledge base with tools that help your team see what customers need next.</p><router-link to="/register" class="mt-7 inline-flex items-center gap-2 text-sm font-semibold text-pink-700 hover:text-pink-900">Explore SupportAI <span aria-hidden="true">→</span></router-link></div>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <article v-for="feature in features" :key="feature.title" class="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm"><span class="flex h-9 w-9 items-center justify-center rounded-xl bg-pink-50 text-pink-600"><svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="m5 12 4 4L19 6"/></svg></span><h3 class="mt-4 text-sm font-semibold text-stone-900">{{ feature.title }}</h3><p class="mt-2 text-sm leading-6 text-stone-500">{{ feature.desc }}</p></article>
            </div>
          </div>
        </div>
      </section>

      <section class="px-5 py-20 sm:px-8 sm:py-24">
        <div class="mx-auto max-w-5xl overflow-hidden rounded-3xl bg-gradient-to-br from-pink-600 via-pink-700 to-pink-800 px-6 py-12 text-center text-white shadow-xl shadow-pink-950/15 sm:px-12 sm:py-16"><p class="text-sm font-semibold text-pink-100">Start building today</p><h2 class="mx-auto mt-3 max-w-2xl text-3xl font-bold tracking-tight sm:text-4xl">Give customers answers, and your team a clearer next step.</h2><p class="mx-auto mt-4 max-w-xl text-sm leading-6 text-pink-100 sm:text-base">Set up a workspace, add your support content, and try the assistant with your own questions.</p><router-link to="/register" class="mt-8 inline-flex items-center justify-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-semibold text-pink-700 transition hover:bg-pink-50">Get started <span aria-hidden="true">→</span></router-link></div>
      </section>
    </main>

    <footer class="border-t border-stone-200 bg-white">
      <div class="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-7 text-sm text-stone-500 sm:flex-row sm:items-center sm:justify-between sm:px-8"><router-link to="/" class="font-semibold text-stone-800">Support<span class="text-pink-600">AI</span></router-link><span>AI support built around your knowledge.</span><span>© {{ new Date().getFullYear() }} SupportAI</span></div>
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
  { title: 'Answers grounded in your content', desc: 'Use retrieval-augmented generation to find relevant knowledge for each support question.' },
  { title: 'PDF and document processing', desc: 'Bring product guides, policies, FAQs, and other support material into one knowledge base.' },
  { title: 'Knowledge gap insights', desc: 'Review questions your current content does not answer well and decide what to add.' },
  { title: 'FAQ suggestions', desc: 'Generate FAQ drafts from uploaded information, then review them before they go live.' },
  { title: 'Human escalation', desc: 'Surface low-confidence conversations so a person can follow up when needed.' },
  { title: 'Widget and team settings', desc: 'Customize the website widget and give teammates the access they need.' },
]
</script>
