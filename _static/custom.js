document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.querySelector(".bd-sidebar-secondary");
  if (!sidebar) return;

  const btn = document.createElement("button");
  btn.id = "toggle-right-sidebar";
  btn.innerText = "▶";
  btn.title = "Toggle Sidebar";

  btn.addEventListener("click", function () {
    sidebar.classList.toggle("collapsed-sidebar");
    btn.innerText = sidebar.classList.contains("collapsed-sidebar") ? "◀" : "▶";
  });

  document.body.appendChild(btn);
});