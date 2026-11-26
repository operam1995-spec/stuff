/* Adds a site.svg icon link in the header, right next to the Search (Ctrl+K) button. */
(function () {
  // ====== EDIT THESE TWO LINES ======
  var LINK  = "https://sites.google.com/view/index0110/";   // where the icon should go
  var TITLE = "My GoogleSite";                  // tooltip text
  // ==================================

  // Work out the site root from this script's own address (works on every page)
  var script = document.currentScript;
  var root = new URL("../", script.src);
  var ICON = new URL("assets/site.svg", root).href;   // put the file in docs/assets/site.svg

  function addSiteLink() {
    if (document.querySelector(".md-header__site-link")) return;       // already added
    var search = document.querySelector(".md-header__inner .md-search");
    if (!search) return;

    var a = document.createElement("a");
    a.className = "md-header__button md-header__site-link";
    a.href = LINK;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.title = TITLE;
    a.setAttribute("aria-label", TITLE);

    var img = document.createElement("img");
    img.src = ICON;
    img.alt = "";
    a.appendChild(img);

    search.insertAdjacentElement("afterend", a);                        // right after the search box
  }

  addSiteLink();
  if (window.document$) { document$.subscribe(addSiteLink); }           // keep it after page changes
})();
