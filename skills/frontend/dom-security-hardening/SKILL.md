---
name: dom-security-hardening
description: When hardening a web application against Cross-Site Scripting (XSS) and injection attacks by restricting DOM APIs and enforcing strict content policies.
version: 1.0.0
tags: [frontend, security, xss, csp]
---

# DOM Security Hardening

## When to use
- Setting up the initial `index.html` or document root of a web application.
- Refactoring legacy code that relies on direct DOM manipulation.
- Auditing a frontend codebase for XSS (Cross-Site Scripting) vulnerabilities.
- Processing rich text or markdown input from an untrusted user.

## What it does
Hardens the application's attack surface by enforcing a strict Content Security Policy (CSP), neutralizing unsafe dynamic DOM insertions, and stripping execution vectors like inline scripts, styles, and event handlers.

## Workflow
1. **Enforce CSP**: Add a strict Content Security Policy using a `<meta http-equiv="Content-Security-Policy">` tag in the HTML `<head>` (or via server HTTP headers) to block unauthorized execution.
2. **Externalize Assets**: Extract all inline `<script>` blocks and `<style>` blocks into dedicated `.js` and `.css` files.
3. **Remove Inline Events**: Find all inline event handlers (e.g., `onclick="doSomething()"`) and replace them with standard JavaScript `addEventListener` bindings.
4. **Sanitize DOM Insertions**: Replace all instances of `innerHTML`, `outerHTML`, or framework equivalents (`dangerouslySetInnerHTML`, `v-html`) with `textContent` or `innerText`. 
5. **Implement a Sanitizer**: If rendering HTML strings is strictly required (e.g., for a rich text editor), pipe the untrusted string through a robust sanitizer library (like DOMPurify) *before* insertion.

## Rules
- No inline CSS (`style="..."`) or JS (`<script>...</script>`) is permitted under any circumstances.
- `eval()`, `setTimeout(string)`, and `new Function(string)` must never be used.
- All dynamic text insertions must use safe APIs (`textContent` / `innerText`).

## Anti-patterns
- **`innerHTML` Assignment**: Directly assigning user input to the DOM (e.g., `element.innerHTML = userInput;`), which allows immediate script execution.
- **`javascript:` URIs**: Using `href="javascript:void(0)"` or `href="javascript:alert(1)"` in anchor tags, creating hidden execution vectors.
- **Unsafe CSP Flags**: Using `'unsafe-inline'` or `'unsafe-eval'` in the Content Security Policy, which completely defeats the purpose of the policy.

## Output format
A cleaned HTML document containing a `<meta http-equiv="Content-Security-Policy">` tag, referencing only external `.js` and `.css` files, alongside JavaScript that strictly uses `textContent` or sanitized DOM insertions.

## Example (optional)

**❌ Anti-pattern (Unsafe):**
```html
<!-- No CSP -->
<a href="javascript:void(0)" onclick="submitForm()">Click me</a>
<div id="user-bio"></div>

<script>
  // Unsafe DOM insertion
  document.getElementById('user-bio').innerHTML = getUserInput();
  // Unsafe inline style
  document.getElementById('user-bio').setAttribute('style', 'color: red;');
</script>
```

**✅ Hardened Pattern (Safe):**
```html
<!-- Strict CSP enforced -->
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none';">

<a href="#" id="submit-btn">Click me</a>
<div id="user-bio"></div>

<!-- Externalized script -->
<script src="/js/app.js"></script>
```

```javascript
// app.js

// 1. Safe event listener
document.getElementById('submit-btn').addEventListener('click', (e) => {
  e.preventDefault();
  submitForm();
});

// 2. Safe text insertion (escapes HTML by default)
document.getElementById('user-bio').textContent = getUserInput();

// 3. Safe styling via classes, not inline styles
document.getElementById('user-bio').classList.add('text-red');

// OR: If HTML rendering is absolutely required, use DOMPurify
// document.getElementById('user-bio').innerHTML = DOMPurify.sanitize(getUserInput());
```
