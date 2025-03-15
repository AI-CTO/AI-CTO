const header = document.querySelector("header");
const logo = document.querySelector(".logo");

const shrinkThreshold = 50; // The main threshold
const minHeight = 50; // Minimum height of the header
const maxHeight = 150; // Increased initial height of the header

// Calculate the initial ratio of the logo to the header
const initialLogoHeight = logo.offsetHeight;
const initialHeaderHeight = header.offsetHeight;
const logoToHeaderRatio = initialLogoHeight / initialHeaderHeight; // Preserve this ratio

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

      // Dynamically adjust the logo size based on the preserved ratio
      const logoHeight = newHeight * logoToHeaderRatio; // Maintain the initial ratio
      logo.style.height = `${logoHeight}px`;

      ticking = false;
    });
    ticking = true;
  }
});
