document.querySelectorAll("[data-menu-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    const menu = document.querySelector("[data-menu]");
    if (!menu) return;
    const isOpen = menu.classList.toggle("open");
    button.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });
});
