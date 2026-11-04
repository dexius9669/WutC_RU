(function () {
    "use strict";

    var nav = document.getElementById("wutcNav");
    if (!nav) {
        return;
    }

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
})();
