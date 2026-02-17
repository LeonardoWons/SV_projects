const video = document.getElementById("scrollVideo");

video.addEventListener("loadedmetadata", () => {
    const scrollHeight = document.body.scrollHeight - window.innerHeight;

    window.addEventListener("scroll", () => {
        const scrollTop = window.scrollY;
        const scrollFraction = scrollTop / scrollHeight;

        const videoTime = scrollFraction * video.duration;
        video.currentTime = videoTime;
    });
});
