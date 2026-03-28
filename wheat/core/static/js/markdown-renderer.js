import DOMPurify from "./vendor/dompurify.esm.js";
import { marked } from "./vendor/marked.esm.js";
import { rewriteRenderedMarkdownHtml } from "./markdown-same-origin.js";

function decodeHtml(html) {
    const el = document.createElement("div");
    el.innerHTML = html;
    return el.textContent;
}

function getAllowlistedOrigins() {
    const node = document.getElementById("media-origin-config");
    if (!node) return [];

    try {
        const parsed = JSON.parse(node.textContent || "[]");
        return Array.isArray(parsed) ? parsed : [];
    } catch (_) {
        return [];
    }
}

function run() {
    const list = document.getElementsByClassName("content");
    const allowlistedOrigins = getAllowlistedOrigins();
    for (let i = 0; i < list.length; i++) {
        const div = list[i];
        if (!div.classList.contains("markdown-source")) continue;
        const raw = decodeHtml(div.innerHTML);
        const html = marked.parse(raw);
        const sanitized = DOMPurify.sanitize(html);
        div.classList.remove("markdown-source");
        div.innerHTML = rewriteRenderedMarkdownHtml(sanitized, {
            pageOrigin: window.location.origin,
            allowlistedOrigins,
        });
    }
}

window.renderMarkdownContent = run;

if (document.readyState === "loading") {
    window.addEventListener("load", run);
} else {
    run();
}
