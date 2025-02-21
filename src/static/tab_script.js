document.addEventListener("DOMContentLoaded", function () {
    const tabs = document.querySelectorAll(".tab-link");

    // Initially highlight the tab based on the current page
    tabs.forEach(tab => {
        if (window.location.pathname === tab.getAttribute("href")) {
            tab.classList.add("active");
        }
    });

    // Add click event to change active tab
    tabs.forEach(tab => {
        tab.addEventListener("click", function (event) {
            event.preventDefault(); // Prevent the default link behavior

            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove("active"));

            // Add active class to clicked tab
            this.classList.add("active");

            // Optionally, you can navigate to the link after adding the active class
            window.location.href = this.getAttribute("href");
        });
    });
});
