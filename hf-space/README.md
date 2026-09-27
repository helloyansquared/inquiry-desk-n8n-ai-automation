---
title: Inquiry Desk
emoji: 📬
colorFrom: green
colorTo: yellow
sdk: static
app_file: index.html
pinned: false
short_description: Customer inquiry extraction and reply drafts in your browser
models:
  - onnx-community/Qwen2.5-0.5B-Instruct
tags:
  - automation
  - transformers.js
  - webgpu
  - portfolio
---

# Inquiry Desk — browser demo

A free static companion to the [n8n + Python portfolio](https://github.com/yesyesyanyan/inquiry-desk-n8n-ai-automation).

**Two clearly separated modes:**

- **Recorded examples:** instant, predefined example fields. No model inference is claimed.
- **Browser AI:** real Qwen2.5-0.5B extraction through Transformers.js 3.8.1 in a Web Worker. Model weights download on first use (approximately 500–550 MB). WebGPU is preferred, with a slower single-threaded WASM CPU fallback.

Inference happens on the visitor's device; this app does not send inquiry text to a server. Model/runtime files are fetched from Hugging Face and jsDelivr. Records exist only in the current page's memory, up to 50 rows. Reloading clears them. Replies use templates and require human review.

This Space does **not** run n8n, Python, or the author's local backend. The complete workflow, SQLite persistence, and server-side implementation are available in the linked GitHub repository. Small-model extraction may be incomplete or wrong; the app rejects fields not found in the source text, but that is not a semantic correctness guarantee. Please use fictional information for testing.

## Files

`index.html`, `app.js`, `core.mjs`, and `worker.js` form the static demo. No API keys, paid inference providers, or shared customer database are used.
