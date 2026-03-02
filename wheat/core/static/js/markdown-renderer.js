(function() {
    function decodeHtml(html) {
        var el = document.createElement("div");
        el.innerHTML = html;
        return el.textContent;
    }
    function run() {
        if (typeof marked === "undefined") return;
        var list = document.getElementsByClassName("content");
        for (var i = 0; i < list.length; i++) {
            var div = list[i];
            if (!div.classList.contains("markdown-source")) continue;
            var raw = decodeHtml(div.innerHTML);
            var html = typeof marked.parse === "function" ? marked.parse(raw) : marked(raw);
            div.classList.remove("markdown-source");
            div.innerHTML = html;
        }
    }
    if (document.readyState === "loading") {
        window.addEventListener("load", run);
    } else {
        run();
    }
})();
