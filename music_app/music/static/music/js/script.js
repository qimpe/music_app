
  const audio = document.getElementById("global-audio");
  const bottomPlayer = document.getElementById("bottom-player");
  const titleSpan = document.getElementById("player-title");
  const artistSpan = document.getElementById("player-artist");

  document.querySelectorAll(".play-button-artist").forEach(button => {
    button.addEventListener("click", () => {
      const parent = button.closest(".track-item");
      const audioUrl = parent.getAttribute("data-audio");
      const title = parent.getAttribute("data-title");
      const artist = parent.getAttribute("data-artist");

      audio.src = audioUrl;
      titleSpan.textContent = title;
      artistSpan.textContent = artist;

      bottomPlayer.style.display = "flex";
      audio.play();
    });
  });

