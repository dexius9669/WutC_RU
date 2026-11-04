(function () {
    "use strict";

    var STORAGE_KEY = "wutc-theme";
    var root = document.documentElement;

    function preferredTheme() {
        var saved = null;
        try {
            saved = window.localStorage.getItem(STORAGE_KEY);
        } catch (e) {
            saved = null;
        }
        if (saved === "light" || saved === "dark") {
            return saved;
        }
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    function applyTheme(theme) {
        root.setAttribute("data-bs-theme", theme);
        try {
            window.localStorage.setItem(STORAGE_KEY, theme);
        } catch (e) {
            /* localStorage может быть отключён — тема просто не запомнится */
        }
    }

    applyTheme(preferredTheme());

    var toggle = document.getElementById("themeToggle");
    if (toggle) {
        var current = function () {
            return root.getAttribute("data-bs-theme") === "dark" ? "dark" : "light";
        };
        toggle.addEventListener("click", function () {
            applyTheme(current() === "dark" ? "light" : "dark");
        });
    }

    // Свернуть мобильное меню после перехода по ссылке.
    var nav = document.getElementById("wutcNav");
    if (nav) {
        nav.addEventListener("click", function (event) {
            var link = event.target.closest("a");
            if (!link || !nav.classList.contains("show")) {
                return;
            }
            var collapse = window.bootstrap && window.bootstrap.Collapse.getInstance(nav);
            if (collapse) {
                collapse.hide();
            }
        });
    }
})();
