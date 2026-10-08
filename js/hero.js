// Hero reel: frames from Baixue's works run past a scanner. Right of the scanner
// they are watched as images; left of it they are measured as k-means palettes.
// The scanner follows the pointer, and drifts on its own when left alone.
(() => {
  const canvas = document.getElementById("reel");
  const hero = document.getElementById("hero");
  if (!canvas || !hero) return;
  const ctx = canvas.getContext("2d");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const css = getComputedStyle(document.documentElement);
  const color = (name) => css.getPropertyValue(name).trim();
  const C = { cyan: color("--cyan"), amber: color("--amber"), ink: color("--ink"), muted: color("--muted"), dim: color("--dim") };
  const MONO = '"SiteMono", ui-monospace, Menlo, monospace';
  const SANS = '-apple-system, "PingFang SC", "Microsoft YaHei", sans-serif';

  const lum = (h) => (0.299 * parseInt(h.slice(1, 3), 16) + 0.587 * parseInt(h.slice(3, 5), 16) + 0.114 * parseInt(h.slice(5, 7), 16)) / 255;
  function hsv(h) {
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
    const mx = Math.max(r, g, b), d = mx - Math.min(r, g, b);
    let hue = 0;
    if (d) hue = mx === r ? 60 * (((g - b) / d) % 6) : mx === g ? 60 * ((b - r) / d + 2) : 60 * ((r - g) / d + 4);
    return [Math.round((hue + 360) % 360), Math.round(mx ? (d / mx) * 100 : 0), Math.round(mx * 100)];
  }

  let frames = [], W = 0, H = 0, scanX = 0, target = null, pointerAt = -1e9, offset = 0, last = 0, visible = true;

  function resize() {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    W = canvas.clientWidth; H = canvas.clientHeight;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (!scanX) scanX = W / 2;
  }

  function draw(now) {
    const s = Math.min(210, H * 0.3, W * 0.36);
    const top = Math.max(130, H * 0.2);
    const slot = s + 22;
    const band = { y: top - 34, h: s + 66 };
    ctx.clearRect(0, 0, W, H);

    // projector light, flickering a little, centred on the scanner
    const flick = reduce ? 1 : 0.9 + Math.random() * 0.1;
    const cone = ctx.createRadialGradient(scanX, band.y, 0, scanX, band.y, H * 0.95);
    cone.addColorStop(0, `rgba(255,248,235,${0.09 * flick})`);
    cone.addColorStop(1, "rgba(255,248,235,0)");
    ctx.fillStyle = cone;
    ctx.fillRect(0, 0, W, H);

    ctx.fillStyle = "#050506";
    ctx.fillRect(0, band.y, W, band.h);
    ctx.fillStyle = "#0b0b0d";
    const sp = 25, so = -(offset % sp);
    for (let x = so; x < W; x += sp) {
      ctx.fillRect(x + 5, band.y + 7, 14, 9);
      ctx.fillRect(x + 5, band.y + band.h - 16, 14, 9);
    }

    if (frames.length) {
      const total = frames.length * slot;
      const start = -(offset % total);
      for (let n = 0, x = start + 11; x < W; n++, x += slot) {
        const f = frames[n % frames.length];
        if (x + s < 0) continue;
        // edge print
        ctx.font = `10px ${MONO}`; ctx.fillStyle = C.dim;
        ctx.fillText(String((n % frames.length) + 1).padStart(2, "0"), x, top - 10);
        ctx.font = `11px ${SANS}`; ctx.fillStyle = "#77727c";
        ctx.fillText(f.work[0], x + 24, top - 10);
        // measured side
        if (x < scanX) {
          ctx.save(); ctx.beginPath(); ctx.rect(x, top, Math.min(s, scanX - x), s); ctx.clip();
          let bx = x;
          for (const c of f.pal) { const w = c.share * s; ctx.fillStyle = c.hex; ctx.fillRect(bx, top, w + 0.6, s); bx += w; }
          const tone = lum(f.dom) > 0.55 ? "#111" : C.ink;
          const [hh, ss, vv] = hsv(f.dom);
          ctx.fillStyle = tone;
          ctx.font = `600 12px ${MONO}`; ctx.fillText(f.dom.toUpperCase(), x + 10, top + s - 28);
          ctx.font = `10px ${MONO}`; ctx.fillText(`H${hh} S${ss} V${vv}`, x + 10, top + s - 12);
          ctx.font = `10px ${MONO}`; ctx.fillText("K=5", x + 10, top + 18);
          ctx.restore();
        }
        // watched side
        if (x + s > scanX && f.img.complete && f.img.naturalWidth) {
          const cx = Math.max(x, scanX);
          ctx.save(); ctx.beginPath(); ctx.rect(cx, top, x + s - cx, s); ctx.clip();
          ctx.drawImage(f.img, x, top, s, s);
          ctx.restore();
        }
      }
    }

    // scanner beam and line
    const glow = ctx.createLinearGradient(scanX - 40, 0, scanX + 40, 0);
    glow.addColorStop(0, "rgba(126,224,210,0)");
    glow.addColorStop(0.5, `rgba(255,255,255,${0.55 * flick})`);
    glow.addColorStop(1, "rgba(242,166,90,0)");
    ctx.fillStyle = glow;
    ctx.fillRect(scanX - 40, band.y - 8, 80, band.h + 16);
    ctx.fillStyle = "rgba(255,255,255,.9)";
    ctx.fillRect(scanX - 1, band.y - 30, 2, H - band.y - 40);

    ctx.font = `11px ${MONO}`;
    ctx.textAlign = "right"; ctx.fillStyle = C.cyan; ctx.fillText("MEASURED", scanX - 14, band.y + band.h + 24);
    ctx.textAlign = "left"; ctx.fillStyle = C.amber; ctx.fillText("WATCHED", scanX + 14, band.y + band.h + 24);
  }

  function tick(now) {
    const dt = last ? Math.min(now - last, 64) / 1000 : 0;
    last = now;
    if (!reduce) offset += dt * 34;
    const idle = now - pointerAt > 3500;
    const goal = target === null || idle ? W * (0.5 + (reduce ? 0 : 0.14 * Math.sin(now / 3400))) : target;
    scanX += (goal - scanX) * (reduce ? 1 : 0.09);
    draw(now);
    if (visible && !reduce) requestAnimationFrame(tick);
  }

  function point(e) {
    const r = canvas.getBoundingClientRect();
    target = Math.max(0, Math.min(W, e.clientX - r.left));
    pointerAt = performance.now();
  }
  hero.addEventListener("pointermove", point);
  hero.addEventListener("pointerdown", point);
  window.addEventListener("resize", () => { resize(); if (reduce) draw(0); });

  new IntersectionObserver(([e]) => {
    const was = visible; visible = e.isIntersecting;
    if (visible && !was && !reduce) { last = 0; requestAnimationFrame(tick); }
  }).observe(hero);

  // running timecode in the hero footer
  const tc = document.getElementById("tc"), t0 = performance.now();
  if (tc && !reduce) setInterval(() => {
    const sec = Math.floor((performance.now() - t0) / 1000);
    const fr = Math.floor(((performance.now() - t0) % 1000) / 1000 * 24);
    tc.textContent = `TC 00:${String(Math.floor(sec / 60) % 60).padStart(2, "0")}:${String(sec % 60).padStart(2, "0")}:${String(fr).padStart(2, "0")}`;
  }, 1000 / 24);

  resize();
  fetch("media/media.json")
    .then((r) => { if (!r.ok) throw new Error(`media.json: HTTP ${r.status}`); return r.json(); })
    .then((m) => {
      const works = m.works;
      frames = Object.entries(m.frames)
        .filter(([k]) => /^[a-z]+-\d+$/.test(k) && works[k.split("-")[0]])
        .map(([k, v]) => {
          const img = new Image(); img.src = "media/" + v.file;
          img.onload = () => { if (reduce) draw(0); };
          return { img, work: works[k.split("-")[0]], dom: v.palette[0].hex, pal: [...v.palette].sort((a, b) => lum(a.hex) - lum(b.hex)) };
        });
      window.dispatchEvent(new CustomEvent("media-ready", { detail: m }));
      requestAnimationFrame(tick);
    })
    .catch((err) => { console.error("Hero reel could not load its frames:", err); requestAnimationFrame(tick); });
})();
