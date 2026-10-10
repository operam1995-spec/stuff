document.addEventListener("DOMContentLoaded", function () {
    // Create button element
    const button = document.createElement("button");
    button.id = "sidebar-toggle-btn";
    button.innerHTML = "↔ Full Screen";
    document.body.appendChild(button);

    // Toggle sidebars on click
    button.addEventListener("click", function () {
        document.body.classList.toggle("hide-sidebars");
        
        if (document.body.classList.contains("hide-sidebars")) {
            button.innerHTML = "🔍 Show Sidebars";
        } else {
            button.innerHTML = "↔ Full Screen";
        }
    });
});