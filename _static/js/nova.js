(function () {
  "use strict";

  var root = document.documentElement;

  // ---- Theme toggle ----
  var toggleBtn = document.getElementById("nova-theme-toggle");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", function () {
      var current = root.getAttribute("data-theme") === "dark" ? "dark" : "light";
      var next = current === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {
        localStorage.setItem("nova-theme", next);
      } catch (e) {
        /* localStorage unavailable, ignore */
      }
    });
  }

  // ---- Mobile nav toggle ----
  var navToggle = document.getElementById("nova-nav-toggle");
  var backdrop = document.getElementById("nova-sidebar-backdrop");

  function setSidebarOpen(open) {
    root.setAttribute("data-sidebar-open", open ? "true" : "false");
    if (navToggle) navToggle.setAttribute("aria-expanded", open ? "true" : "false");
  }

  if (navToggle) {
    navToggle.addEventListener("click", function () {
      var isOpen = root.getAttribute("data-sidebar-open") === "true";
      setSidebarOpen(!isOpen);
    });
  }
  if (backdrop) {
    backdrop.addEventListener("click", function () {
      setSidebarOpen(false);
    });
  }

  // Close mobile nav on Escape
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") setSidebarOpen(false);
  });

  // ---- Highlight current TOC section on scroll (simple scrollspy) ----
  var tocLinks = document.querySelectorAll(".nova-page-toc a");
  if (tocLinks.length) {
    var headings = [];
    tocLinks.forEach(function (link) {
      var hash = link.getAttribute("href").split("#")[1];
      if (hash) {
        var el = document.getElementById(hash);
        if (el) headings.push({ el: el, link: link });
      }
    });

    if (headings.length) {
      var onScroll = function () {
        var scrollPos = window.scrollY + 100;
        var activeIndex = 0;
        for (var i = 0; i < headings.length; i++) {
          if (headings[i].el.offsetTop <= scrollPos) activeIndex = i;
        }
        tocLinks.forEach(function (l) { l.style.borderLeftColor = "transparent"; });
        headings[activeIndex].link.style.borderLeftColor = "var(--nova-accent)";
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }
  }
})();
