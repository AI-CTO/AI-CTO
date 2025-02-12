document.addEventListener("DOMContentLoaded", function () {
    const tabs = document.querySelectorAll(".tab-link");

    tabs.forEach(tab => {
        // Check if the tab's href matches the current page URL
        if (tab.href === window.location.href) {
            tab.classList.add("active");
        }
    });
});