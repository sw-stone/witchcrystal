(function () {
  "use strict";

  const EXPECTED_CATEGORIES = 5;
  const EXPECTED_TRACKS = 10;
  const DEFAULT_VOLUME = 0.55;

  function initialize() {
    const library = window.SOUND_LIBRARY;

    if (!Array.isArray(library) || library.length === 0) {
      console.error("[晚安水晶球] 初始化失败：未读取到声音数据库。");
      return;
    }

    const elements = {
      categoryTabs: document.getElementById("categoryTabs"),
      sceneList: document.getElementById("sceneList"),
      sceneTitle: document.getElementById("sceneTitle"),
      sceneDescription: document.getElementById("sceneDescription"),
      sceneVideo: document.getElementById("sceneVideo"),
      sceneAudio: document.getElementById("sceneAudio"),
      crystalOrb: document.getElementById("crystalOrb"),
      orbFallback: document.getElementById("orbFallback"),
      playButton: document.getElementById("playButton"),
      volumeRange: document.getElementById("volumeRange"),
      volumeValue: document.getElementById("volumeValue"),
      timerOptions: document.getElementById("timerOptions"),
      timerCountdown: document.getElementById("timerCountdown"),
      statusMessage: document.getElementById("statusMessage")
    };

    if (Object.values(elements).some(function (element) { return !element; })) {
      console.error("[晚安水晶球] 初始化失败：页面结构不完整。");
      return;
    }

    const tracks = library.reduce(function (allTracks, category) {
      return allTracks.concat(Array.isArray(category.tracks) ? category.tracks : []);
    }, []);

    if (library.length !== EXPECTED_CATEGORIES || tracks.length !== EXPECTED_TRACKS) {
      console.warn(
        "[晚安水晶球] 素材数量与预期不一致：" +
        library.length + " 个分类，" + tracks.length + " 条场景。"
      );
    }

    const state = {
      activeCategoryId: library[0].id,
      activeTrack: tracks[0],
      timerId: null,
      timerEndsAt: null
    };

    elements.sceneVideo.muted = true;
    elements.sceneVideo.defaultMuted = true;
    elements.sceneVideo.volume = 0;
    elements.sceneAudio.loop = true;
    elements.sceneAudio.volume = DEFAULT_VOLUME;

    function setStatus(message, type) {
      elements.statusMessage.textContent = message;
      elements.statusMessage.dataset.type = type || "info";
    }

    function updatePlayButton() {
      const isPlaying = !elements.sceneAudio.paused;
      const icon = elements.playButton.querySelector(".play-icon");
      const text = elements.playButton.querySelector(".play-text");

      if (icon) icon.textContent = isPlaying ? "Ⅱ" : "▶";
      if (text) text.textContent = isPlaying ? "暂停" : "播放";
      elements.playButton.setAttribute("aria-label", isPlaying ? "暂停当前声音" : "播放当前声音");
      elements.playButton.classList.toggle("is-playing", isPlaying);
    }

    function enforceSilentVideo() {
      if (!elements.sceneVideo.muted || elements.sceneVideo.volume !== 0) {
        console.warn("[晚安水晶球] 已阻止视频原声音输出。");
      }
      elements.sceneVideo.muted = true;
      elements.sceneVideo.defaultMuted = true;
      elements.sceneVideo.volume = 0;
    }

    function playVideo() {
      enforceSilentVideo();
      const playAttempt = elements.sceneVideo.play();
      if (playAttempt && typeof playAttempt.catch === "function") {
        playAttempt.catch(function (error) {
          console.warn("[晚安水晶球] 视频自动播放被浏览器阻止。", error);
        });
      }
    }

    function loadVideo(track) {
      elements.crystalOrb.classList.add("is-transitioning");
      elements.crystalOrb.classList.remove("has-video-error");
      elements.sceneVideo.src = track.videoSrc;
      elements.sceneVideo.load();
      playVideo();
    }

    function loadAudio(track) {
      elements.sceneAudio.src = track.audioSrc;
      elements.sceneAudio.load();
    }

    function renderCategories() {
      elements.categoryTabs.replaceChildren();

      library.forEach(function (category) {
        const button = document.createElement("button");
        const isActive = category.id === state.activeCategoryId;
        button.type = "button";
        button.className = "category-tab";
        button.dataset.categoryId = category.id;
        button.setAttribute("aria-pressed", String(isActive));
        button.innerHTML = '<span aria-hidden="true">' + category.icon + "</span>" + category.name;
        button.addEventListener("click", function () {
          state.activeCategoryId = category.id;
          document.body.dataset.theme = category.id;
          renderCategories();
          renderScenes(category);
        });
        elements.categoryTabs.appendChild(button);
      });
    }

    function renderScenes(category) {
      elements.sceneList.replaceChildren();

      category.tracks.forEach(function (track) {
        const button = document.createElement("button");
        const isActive = state.activeTrack && state.activeTrack.id === track.id;
        button.type = "button";
        button.className = "scene-card";
        button.dataset.trackId = track.id;
        button.setAttribute("aria-pressed", String(isActive));

        const name = document.createElement("strong");
        name.textContent = track.name;
        const description = document.createElement("span");
        description.textContent = track.description;
        const marker = document.createElement("span");
        marker.className = "scene-marker";
        marker.setAttribute("aria-hidden", "true");
        marker.textContent = isActive ? "正在聆听" : "进入场景";
        button.append(name, description, marker);

        button.addEventListener("click", function () {
          selectTrack(track, true);
        });
        elements.sceneList.appendChild(button);
      });
    }

    function selectTrack(track, shouldPlayAudio) {
      state.activeTrack = track;
      elements.sceneTitle.textContent = track.name;
      elements.sceneDescription.textContent = track.description;
      loadVideo(track);
      loadAudio(track);

      const activeCategory = library.find(function (category) {
        return category.id === state.activeCategoryId;
      });
      if (activeCategory) renderScenes(activeCategory);

      if (shouldPlayAudio) {
        const playAttempt = elements.sceneAudio.play();
        if (playAttempt && typeof playAttempt.catch === "function") {
          playAttempt.catch(function (error) {
            console.warn("[晚安水晶球] 音频播放失败：" + track.audioSrc, error);
            setStatus("声音暂时无法播放，请检查素材或浏览器权限。", "warning");
            updatePlayButton();
          });
        }
      }
    }

    function toggleAudio() {
      if (!state.activeTrack) return;

      if (elements.sceneAudio.paused) {
        const playAttempt = elements.sceneAudio.play();
        if (playAttempt && typeof playAttempt.catch === "function") {
          playAttempt.catch(function (error) {
            console.warn("[晚安水晶球] 音频播放失败。", error);
            setStatus("声音暂时无法播放，请检查素材或浏览器权限。", "warning");
          });
        }
      } else {
        elements.sceneAudio.pause();
      }
    }

    function formatRemaining(milliseconds) {
      const totalSeconds = Math.max(0, Math.ceil(milliseconds / 1000));
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      return String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0") + " 后停止";
    }

    function updateTimerButtons(minutes) {
      elements.timerOptions.querySelectorAll("button").forEach(function (button) {
        button.setAttribute("aria-pressed", String(Number(button.dataset.minutes) === minutes));
      });
    }

    function cancelTimer(showStatus) {
      if (state.timerId) window.clearInterval(state.timerId);
      state.timerId = null;
      state.timerEndsAt = null;
      elements.timerCountdown.textContent = "未开启";
      updateTimerButtons(0);
      if (showStatus) setStatus("睡眠计时已关闭。", "info");
    }

    function finishTimer() {
      cancelTimer(false);
      elements.sceneAudio.pause();
      updatePlayButton();
      setStatus("晚安，声音已停下。", "success");
    }

    function setTimer(minutes) {
      cancelTimer(false);

      if (minutes === 0) {
        setStatus("睡眠计时已关闭。", "info");
        return;
      }

      state.timerEndsAt = Date.now() + minutes * 60 * 1000;
      updateTimerButtons(minutes);
      elements.timerCountdown.textContent = formatRemaining(state.timerEndsAt - Date.now());
      setStatus(minutes + " 分钟后，声音会轻轻停下。", "info");

      state.timerId = window.setInterval(function () {
        const remaining = state.timerEndsAt - Date.now();
        if (remaining <= 0) {
          finishTimer();
          return;
        }
        elements.timerCountdown.textContent = formatRemaining(remaining);
      }, 1000);
    }

    elements.sceneVideo.addEventListener("loadeddata", function () {
      enforceSilentVideo();
      elements.crystalOrb.classList.remove("is-transitioning", "has-video-error");
    });
    elements.sceneVideo.addEventListener("volumechange", enforceSilentVideo);
    elements.sceneVideo.addEventListener("error", function () {
      elements.crystalOrb.classList.remove("is-transitioning");
      elements.crystalOrb.classList.add("has-video-error");
      console.warn("[晚安水晶球] 视频素材加载失败：" + (state.activeTrack && state.activeTrack.videoSrc));
      setStatus("画面暂时无法加载，声音控制仍可使用。", "warning");
    });
    elements.sceneAudio.addEventListener("play", function () {
      updatePlayButton();
      setStatus("正在播放 · " + state.activeTrack.name, "success");
    });
    elements.sceneAudio.addEventListener("pause", function () {
      updatePlayButton();
      if (!elements.sceneAudio.ended) setStatus("声音已暂停", "info");
    });
    elements.sceneAudio.addEventListener("error", function () {
      console.warn("[晚安水晶球] 音频素材加载失败：" + (state.activeTrack && state.activeTrack.audioSrc));
      setStatus("声音暂时无法加载，请检查素材路径。", "warning");
      updatePlayButton();
    });
    elements.playButton.addEventListener("click", toggleAudio);
    elements.volumeRange.addEventListener("input", function () {
      const volume = Number(elements.volumeRange.value);
      elements.sceneAudio.volume = volume;
      elements.volumeValue.value = Math.round(volume * 100) + "%";
    });
    elements.timerOptions.addEventListener("click", function (event) {
      const button = event.target.closest("button[data-minutes]");
      if (button) setTimer(Number(button.dataset.minutes));
    });

    renderCategories();
    renderScenes(library[0]);
    selectTrack(tracks[0], false);
    updatePlayButton();

    if (window.location.protocol === "http:" || window.location.protocol === "https:") {
      tracks.forEach(function (track) {
        [track.audioSrc, track.videoSrc].forEach(function (path) {
          fetch(path, { method: "HEAD" }).then(function (response) {
            if (!response.ok) console.warn("[晚安水晶球] 素材不可用：" + path + "（" + response.status + "）");
          }).catch(function () {
            console.warn("[晚安水晶球] 无法检查素材：" + path);
          });
        });
      });
    }

    console.info("[晚安水晶球] 初始化完成：5 个分类，10 组音频与视频场景。");
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})();
