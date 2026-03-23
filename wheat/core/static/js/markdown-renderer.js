import DOMPurify from "https://cdn.jsdelivr.net/npm/dompurify@3.2.6/+esm";
import { marked } from "https://cdn.jsdelivr.net/npm/marked@15.0.6/+esm";

function decodeHtml(html) {
    const el = document.createElement("div");
    el.innerHTML = html;
    return el.textContent;
}

function run() {
    const list = document.getElementsByClassName("content");
    for (let i = 0; i < list.length; i++) {
        const div = list[i];
        if (!div.classList.contains("markdown-source")) continue;
        const raw = decodeHtml(div.innerHTML);
        const html = marked.parse(raw);
        div.classList.remove("markdown-source");
        div.innerHTML = DOMPurify.sanitize(html);
    }
}

window.renderMarkdownContent = run;

if (document.readyState === "loading") {
    window.addEventListener("load", run);
} else {
    run();
}
