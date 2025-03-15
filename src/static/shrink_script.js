const header = document.querySelector("header");
const logo = document.querySelector(".logo");

const shrinkThreshold = 50; // The main threshold
const minHeight = 50; // Minimum height of the header
const maxHeight = 150; // Increased initial height of the header

let ticking = false;

window.addEventListener("scroll", () => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      const currentScrollY = window.scrollY;

      // Calculate the new height based on scroll position
      const newHeight = Math.max(
        minHeight,
        maxHeight - (currentScrollY / shrinkThreshold) * (maxHeight - minHeight)
      );

      // Apply the calculated height to the header
      header.style.height = `${newHeight}px`;

      // Dynamically adjust the logo size
      const logoHeight = (newHeight / maxHeight) * 80; // Scale logo size proportionally (80% of header height)
      logo.style.height = `${logoHeight}%`;

      ticking = false;
    });
    ticking = true;
  }
});
