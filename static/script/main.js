document.addEventListener("DOMContentLoaded", () => {
    // Intersection Observer for scroll animations
    const fadeElements = document.querySelectorAll('.fade-up');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Optional: Stop observing once it's visible
                // observer.unobserve(entry.target); 
            }
        });
    }, {
        threshold: 0.1, // Trigger when 10% of the element is visible
        rootMargin: "0px 0px -50px 0px" // Trigger slightly before it comes into view
    });

    fadeElements.forEach(el => {
        observer.observe(el);
    });
});
