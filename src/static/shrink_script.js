const header = document.querySelector("header");

let lastScrollY = window.scrollY;
let ticking = false;

window.addEventListener("scroll", () => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      if (window.scrollY > 50) {
        header.classList.add("shrink");
      } else {
        header.classList.remove("shrink");
      }
      ticking = false;
    });
    ticking = true;
  }
});
