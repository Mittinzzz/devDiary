<script setup lang="ts">
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const props = defineProps<{
  content: string
}>()

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
  highlight(str: string, lang: string): string {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs-pre"><code class="hljs language-${lang}">${
          hljs.highlight(str, { language: lang, ignoreIllegals: true }).value
        }</code></pre>`
      } catch (_) {}
    }
    return `<pre class="hljs-pre"><code class="hljs">${md.utils.escapeHtml(str)}</code></pre>`
  },
})

const renderedHtml = computed(() => md.render(props.content))
</script>

<template>
  <div class="markdown-body" v-html="renderedHtml" />
</template>

<style>
.markdown-body {
  color: #CBD5E1;
  line-height: 1.8;
  font-size: 1rem;
}

.markdown-body h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #F8FAFC;
  margin-top: 2rem;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.markdown-body h2 {
  font-size: 1.4rem;
  font-weight: 600;
  color: #F8FAFC;
  margin-top: 1.8rem;
  margin-bottom: 0.8rem;
  padding-bottom: 0.3rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.markdown-body h3 {
  font-size: 1.2rem;
  font-weight: 600;
  color: #A78BFA;
  margin-top: 1.5rem;
  margin-bottom: 0.6rem;
}

.markdown-body h4 {
  font-size: 1.05rem;
  font-weight: 600;
  color: #8B5CF6;
  margin-top: 1.2rem;
  margin-bottom: 0.5rem;
}

.markdown-body p {
  margin-bottom: 1rem;
}

.markdown-body a {
  color: #6366F1;
  text-decoration: none;
  border-bottom: 1px solid rgba(99, 102, 241, 0.3);
  transition: all 0.2s;
}

.markdown-body a:hover {
  color: #A78BFA;
  border-bottom-color: #A78BFA;
}

.markdown-body ul, .markdown-body ol {
  margin-bottom: 1rem;
  padding-left: 1.5rem;
}

.markdown-body li {
  margin-bottom: 0.3rem;
}

.markdown-body li::marker {
  color: #6366F1;
}

.markdown-body blockquote {
  border-left: 3px solid #6366F1;
  padding: 0.5rem 1rem;
  margin: 1.5rem 0;
  background: rgba(99, 102, 241, 0.05);
  border-radius: 0 8px 8px 0;
  color: #94A3B8;
}

.markdown-body code {
  background: rgba(255, 255, 255, 0.06);
  padding: 0.15em 0.4em;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9em;
  color: #A78BFA;
}

.markdown-body .hljs-pre {
  background: #1E293B;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 1.2rem;
  overflow-x: auto;
  margin-bottom: 1.5rem;
}

.markdown-body .hljs-pre code {
  background: none;
  padding: 0;
  color: #F8FAFC;
  font-size: 0.85em;
  line-height: 1.6;
}

.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1.5rem;
}

.markdown-body th, .markdown-body td {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.markdown-body th {
  background: rgba(99, 102, 241, 0.1);
  color: #A78BFA;
  font-weight: 600;
}

.markdown-body hr {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  margin: 2rem 0;
}

.markdown-body img {
  max-width: 100%;
  border-radius: 8px;
}

.markdown-body strong {
  color: #F8FAFC;
  font-weight: 600;
}

.markdown-body em {
  color: #94A3B8;
}
</style>
