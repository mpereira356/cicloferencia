document.querySelectorAll("[data-menu-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    const menu = document.querySelector("[data-menu]");
    if (menu) menu.classList.toggle("open");
  });
});
