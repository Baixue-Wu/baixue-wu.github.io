"""Extract frames, colour palettes and film barcodes from Baixue's works.

Reads a manifest (media/sources.json), pulls the listed frames and stills out
of the source videos and images, and writes small JPEGs plus one
media/media.json that records every frame's palette and every film's barcode.
The renderer reads only media/, never the source videos.
"""

import argparse
import glob
import json
import subprocess
from io import BytesIO
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image


def resolve(root: Path, pattern: str) -> Path:
    matches = sorted(glob.glob(str(root / pattern)))
    if len(matches) != 1:
        raise FileNotFoundError(
            f"expected exactly one file for {pattern!r} under {root}, found {len(matches)}"
        )
    return Path(matches[0])


def grab(ffmpeg: str, video: Path, t: float) -> Image.Image:
    cmd = [ffmpeg, "-loglevel", "error", "-ss", str(t), "-i", str(video),
           "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"]
    run = subprocess.run(cmd, capture_output=True)
    if run.returncode != 0 or not run.stdout:
        raise RuntimeError(f"ffmpeg failed on {video} at {t}s:\n{run.stderr.decode()}")
    return Image.open(BytesIO(run.stdout)).convert("RGB")


def crop(img: Image.Image, aspect: float, focus: tuple[float, float]) -> Image.Image:
    """Largest crop of the given width/height ratio, centred near focus."""
    w, h = img.size
    if w / h > aspect:
        cw, ch = round(h * aspect), h
    else:
        cw, ch = w, round(w / aspect)
    x = min(max(round(focus[0] * w - cw / 2), 0), w - cw)
    y = min(max(round(focus[1] * h - ch / 2), 0), h - ch)
    return img.crop((x, y, x + cw, y + ch))


def palette(img: Image.Image, k: int) -> list[dict]:
    """k-means colours of an image, largest share first."""
    px = np.asarray(img.resize((64, 64)), dtype=np.float64).reshape(-1, 3)
    lum = px @ np.array([0.299, 0.587, 0.114])
    order = np.argsort(lum)
    centres = np.stack([px[order[int((i + 0.5) * len(px) / k)]] for i in range(k)])
    for _ in range(30):
        labels = np.argmin(((px[:, None, :] - centres[None]) ** 2).sum(-1), axis=1)
        for i in range(k):
            if np.any(labels == i):
                centres[i] = px[labels == i].mean(0)
    shares = np.bincount(labels, minlength=k) / len(px)
    out = [{"hex": "#%02x%02x%02x" % tuple(int(round(v)) for v in c), "share": round(float(s), 4)}
           for c, s in zip(centres, shares) if s > 0]
    return sorted(out, key=lambda c: -c["share"])


def barcode(ffmpeg: str, video: Path, slices: int) -> list[str]:
    """Mean colour of evenly spaced moments across the whole film."""
    probe = subprocess.run([ffmpeg, "-i", str(video)], capture_output=True).stderr.decode()
    hms = probe.split("Duration: ")[1].split(",")[0].split(":")
    duration = int(hms[0]) * 3600 + int(hms[1]) * 60 + float(hms[2])
    cmd = [ffmpeg, "-loglevel", "error", "-i", str(video), "-vf",
           f"fps={slices / duration},scale=16:9:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    run = subprocess.run(cmd, capture_output=True)
    if run.returncode != 0:
        raise RuntimeError(f"ffmpeg failed on {video}:\n{run.stderr.decode()}")
    frames = np.frombuffer(run.stdout, dtype=np.uint8).reshape(-1, 9 * 16, 3).mean(1)
    return ["#%02x%02x%02x" % tuple(int(v) for v in f) for f in frames[:slices]]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest", type=Path, help="sources manifest, e.g. media/sources.json")
    ap.add_argument("--root", type=Path, required=True,
                    help="folder the manifest's video and image paths are relative to")
    ap.add_argument("--out", type=Path, default=Path("media"), help="output folder (default: media)")
    ap.add_argument("--k", type=int, default=5, help="palette size per frame (default: 5)")
    ap.add_argument("--frame-width", type=int, default=240, help="default frame width in px (default: 240)")
    ap.add_argument("--ffmpeg", default=imageio_ffmpeg.get_ffmpeg_exe(), help="ffmpeg executable")
    args = ap.parse_args()

    spec = json.loads(args.manifest.read_text())
    (args.out / "frames").mkdir(parents=True, exist_ok=True)
    result = {"frames": {}, "barcodes": {}, "stills": {}}

    for f in spec["frames"]:
        img = crop(grab(args.ffmpeg, resolve(args.root, f["video"]), f["t"]), f["aspect"], f["focus"])
        width = f.get("width", args.frame_width)
        img = img.resize((width, round(width / f["aspect"])), Image.LANCZOS)
        name = f"frames/{f['id']}.jpg"
        img.save(args.out / name, quality=78, optimize=True, progressive=True)
        result["frames"][f["id"]] = {"file": name, "size": list(img.size), "palette": palette(img, args.k)}
        print("frame", f["id"])

    for b in spec["barcodes"]:
        result["barcodes"][b["id"]] = barcode(args.ffmpeg, resolve(args.root, b["video"]), b["slices"])
        print("barcode", b["id"])

    for s in spec["stills"]:
        img = Image.open(resolve(args.root, s["image"])).convert("RGB")
        if "box" in s:
            img = img.crop(tuple(s["box"]))
        img = img.resize((round(img.width * s["height"] / img.height), s["height"]), Image.LANCZOS)
        name = f"frames/{s['id']}.jpg"
        img.save(args.out / name, quality=80, optimize=True, progressive=True)
        result["stills"][s["id"]] = {"file": name, "size": list(img.size)}
        print("still", s["id"])

    (args.out / "media.json").write_text(json.dumps(result, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
