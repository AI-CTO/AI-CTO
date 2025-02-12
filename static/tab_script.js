document.addEventListener("DOMContentLoaded", function () {
    const tabs = document.querySelectorAll(".tab-link");
    const contents = document.querySelectorAll(".tab-content");

    // Add active class to the correct tab based on the current URL
    const currentUrl = window.location.pathname;
    tabs.forEach(tab => {
        const tabLink = tab.getAttribute("href");
        if (currentUrl === tabLink) {
            tab.classList.add("active");
        }
    });

    tabs.forEach(tab => {
        tab.addEventListener("click", function () {
            let tabId = this.getAttribute("data-tab");

            // Remove active class from all tabs and contents
            tabs.forEach(t => t.classList.remove("active"));
            contents.forEach(c => c.classList.remove("active"));

            // Add active class to clicked tab and corresponding content
            this.classList.add("active");
            document.getElementById(tabId).classList.add("active");
        });
    });
});
