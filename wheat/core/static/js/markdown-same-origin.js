function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function parseImgAttributes(tag) {
    const body = tag.replace(/^<img\b/i, "").replace(/\/?>$/i, "");
    const attrs = {};
    const attrRe = /([^\s=\/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g;
    let match;

    while ((match = attrRe.exec(body)) !== null) {
        const [, name, dq, sq, bare] = match;
        attrs[name.toLowerCase()] = dq ?? sq ?? bare ?? "";
    }

    return attrs;
}

export function buildProxyImageUrl(src, proxyPath = "/api/media/image-proxy/") {
    return `${proxyPath}?url=${encodeURIComponent(src)}`;
}

function normalizeOrigin(urlLike) {
    if (!urlLike) return null;

    try {
        return new URL(urlLike).origin;
    } catch (_) {
        return null;
    }
}

export function rewriteImageSrc(src, { pageOrigin, allowlistedOrigins = [], proxyPath = "/api/media/image-proxy/" } = {}) {
    if (!src) return null;

    const normalizedPageOrigin = normalizeOrigin(pageOrigin);
    const normalizedAllowlistedOrigins = allowlistedOrigins
        .map((origin) => normalizeOrigin(origin) || origin)
        .filter(Boolean);

    try {
        const resolved = pageOrigin ? new URL(src, pageOrigin) : new URL(src);
        if (normalizedPageOrigin && resolved.origin === normalizedPageOrigin) {
            return src;
        }
        if (normalizedAllowlistedOrigins.includes(resolved.origin)) {
            return buildProxyImageUrl(resolved.href, proxyPath);
        }
        return resolved.href;
    } catch (_) {
        return null;
    }

    return null;
}

function buildReplacementTag(tag, src, options) {
    const attrs = parseImgAttributes(tag);
    const rewrittenSrc = rewriteImageSrc(src, options);
    if (rewrittenSrc) {
        const alt = attrs.alt ? ` alt="${escapeHtml(attrs.alt)}"` : ' alt=""';
        const title = attrs.title ? ` title="${escapeHtml(attrs.title)}"` : "";
        return `<img src="${escapeHtml(rewrittenSrc)}"${alt}${title}>`;
    }

    const label = attrs.alt || "image link";
    return `<a href="${escapeHtml(src)}" rel="nofollow noopener noreferrer" target="_blank">${escapeHtml(label)}</a>`;
}

export function rewriteRenderedMarkdownHtml(html, options = {}) {
    return String(html).replace(/<img\b[^>]*\bsrc=(?:"([^"]*)"|'([^']*)'|([^\s>]+))[^>]*>/gi, (tag, dq, sq, bare) => {
        const src = dq ?? sq ?? bare ?? "";
        return buildReplacementTag(tag, src, options);
    });
}
