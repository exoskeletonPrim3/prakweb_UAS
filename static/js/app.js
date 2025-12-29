const audioPlayer = document.querySelectorAll(".audio-player");

if (audioPlayer) {
  audioPlayer.forEach((player) => {
    const audio = player.querySelector(".audio");
    const playBtn = player.querySelector(".playBtn");
    const progress = player.querySelector(".progress");
    const volume = player.querySelector(".volume");
    const current = player.querySelector(".current");
    const duration = player.querySelector(".duration");
    const playIcon = player.querySelector(".play-icon");

    audio.addEventListener("loadedmetadata", () => {
      duration.textContent = formatTime(audio.duration);
      progress.max = Math.floor(audio.duration);
    });

    const resetIcon = () => {
      playIcon.classList.remove("bi-pause-fill");
      playIcon.classList.add("bi-play-fill");
    };

    const setPauseIcon = () => {
      playIcon.classList.remove("bi-play-fill");
      playIcon.classList.add("bi-pause-fill");
    };

    playBtn.addEventListener("click", () => {
      if (audio.paused) {
        document.querySelectorAll(".audio").forEach((otherAudio) => {
          if (otherAudio !== audio) {
            otherAudio.pause();
            const otherPlayer = otherAudio.closest(".audio-player");
            const otherIcon = otherPlayer.querySelector(".play-icon");
            otherIcon.classList.replace("bi-pause-fill", "bi-play-fill");
          }
        });

        audio.play();
        setPauseIcon();
      } else {
        audio.pause();
        resetIcon();
      }
    });

    audio.addEventListener("timeupdate", () => {
      progress.value = Math.floor(audio.currentTime);
      current.textContent = formatTime(audio.currentTime);
    });

    progress.addEventListener("input", () => {
      audio.currentTime = progress.value;
    });

    volume.addEventListener("input", () => {
      audio.volume = volume.value;
    });

    audio.addEventListener("ended", () => {
      resetIcon();
      progress.value = 0;
      current.textContent = "0:00";
    });

    function formatTime(sec) {
      if (isNaN(sec)) return "0:00";
      const m = Math.floor(sec / 60);
      const s = Math.floor(sec % 60)
        .toString()
        .padStart(2, "0");
      return `${m}:${s}`;
    }
  });
}

function filterSongs(query) {
  const cards = document.querySelectorAll(".audio-player");
  query = query.toLowerCase();

  cards.forEach((card) => {
    const title = card.querySelector(".title").textContent.toLowerCase();
    card.style.display = title.includes(query) ? "block" : "none";
  });
}

const updateBtn = document.querySelectorAll(".update-btn");

if (updateBtn) {
  updateBtn.forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-id");

      fetch(`/songs/delete/${id}`, { method: "POST" })
        .then((res) => {
          console.log(res);
          return res.json();
        })
        .then((data) => {
          console.log(data);
          if (data) {
            btn.closest(".song-card").remove();
            Swal.fire("Deleted!", "Song has been deleted.", "success");
          }
        });
    });
  });
}
