// Page behaviour that needs media.json: film barcodes as video scrubbers,
// video durations, and the barcode under the hero slogan.
(() => {
  const nav = document.getElementById("nav");
  const onScroll = () => nav.classList.toggle("solid", window.scrollY > 40);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // sound wave under 理解用户
  const wave = document.getElementById("sloganWave");
  if (wave) for (let i = 0; i < 44; i++) {
    const bar = document.createElement("i");
    bar.style.animationDelay = `-${(Math.random() * 1.3).toFixed(2)}s`;
    bar.style.opacity = (0.35 + 0.65 * Math.sin((Math.PI * i) / 43)).toFixed(2);
    wave.appendChild(bar);
  }

  const clock = (t) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, "0")}`;

  function stripes(el, colors) {
    el.replaceChildren(...colors.map((c) => { const i = document.createElement("i"); i.style.background = c; return i; }));
  }

  function scrubber(el, colors, duration) {
    const video = document.getElementById(el.dataset.video);
    stripes(el, colors);
    const head = document.createElement("span"); head.className = "head";
    const tip = document.createElement("span"); tip.className = "tip";
    el.append(head, tip);
    el.tabIndex = 0;
    el.setAttribute("role", "slider");
    el.setAttribute("aria-label", "电影条形码，点击跳转到对应时刻");
    el.setAttribute("aria-valuemin", "0");
    el.setAttribute("aria-valuemax", String(Math.round(duration)));
    const frac = (e) => Math.max(0, Math.min(1, (e.clientX - el.getBoundingClientRect().left) / el.clientWidth));
    el.addEventListener("pointermove", (e) => { const f = frac(e); tip.style.left = `${f * 100}%`; tip.textContent = clock(f * duration); });
    el.addEventListener("click", (e) => {
      video.currentTime = frac(e) * (video.duration || duration);
      video.play().catch(() => {});
    });
    el.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight") video.currentTime = Math.min(duration, video.currentTime + 5);
      if (e.key === "ArrowLeft") video.currentTime = Math.max(0, video.currentTime - 5);
    });
    video.addEventListener("timeupdate", () => {
      const f = video.currentTime / (video.duration || duration);
      head.style.left = `${f * 100}%`;
      el.setAttribute("aria-valuenow", String(Math.round(video.currentTime)));
    });
  }

  window.addEventListener("media-ready", ({ detail: m }) => {
    const line = document.getElementById("sloganBarcode");
    if (line && m.barcodes.jimo) stripes(line, m.barcodes.jimo.filter((_, i) => i % 3 === 0));
    document.querySelectorAll(".barcode[data-barcode]").forEach((el) => {
      const id = el.dataset.barcode;
      if (m.barcodes[id] && m.videos[id]) scrubber(el, m.barcodes[id], m.videos[id].duration);
    });
    document.querySelectorAll("[data-duration]").forEach((el) => {
      const v = m.videos[el.dataset.duration];
      if (v) el.textContent = v.duration >= 60 ? `${Math.floor(v.duration / 60)} 分 ${Math.round(v.duration % 60)} 秒` : `${Math.round(v.duration)} 秒`;
    });
  });

  // only one video plays at a time
  const videos = [...document.querySelectorAll("video")];
  videos.forEach((v) => v.addEventListener("play", () => videos.forEach((o) => { if (o !== v) o.pause(); })));
})();
