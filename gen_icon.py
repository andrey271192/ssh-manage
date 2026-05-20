"""Generate PCA SSH icon in .ico (Windows) and .icns (macOS) formats."""
from PIL import Image, ImageDraw, ImageFont
import struct, os, sys

SIZE = 512

def draw_icon(size=SIZE):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Dark rounded-rect background
    r = size // 6
    draw.rounded_rectangle([4, 4, size - 4, size - 4], radius=r, fill="#1e1e2e", outline="#3b3b5c", width=3)

    # "PCA" text
    font_size = size // 4
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except OSError:
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), "PCA", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2
    ty = size // 4 - th // 4
    draw.text((tx, ty), "PCA", fill="#6c8fff", font=font)

    # Blue dots pattern (like water drops)
    cx = size // 2
    cy = int(size * 0.62)
    dot_r = size // 30

    dot_positions = [
        (0, 0),
        (-3 * dot_r, -2 * dot_r),
        (3 * dot_r, -2 * dot_r),
        (-1.5 * dot_r, 2 * dot_r),
        (1.5 * dot_r, 2 * dot_r),
        (0, 4 * dot_r),
        (-4.5 * dot_r, 1 * dot_r),
        (4.5 * dot_r, 1 * dot_r),
    ]

    for dx, dy in dot_positions:
        x = cx + dx
        y = cy + dy
        draw.ellipse([x - dot_r, y - dot_r, x + dot_r, y + dot_r], fill="#6c8fff")

    # Subtle connecting lines between dots
    line_color = "#3d5abf"
    connections = [(0, 1), (0, 2), (1, 3), (2, 4), (3, 5), (4, 5), (1, 6), (2, 7)]
    abs_positions = [(cx + dx, cy + dy) for dx, dy in dot_positions]
    for a, b in connections:
        draw.line([abs_positions[a], abs_positions[b]], fill=line_color, width=max(1, size // 200))

    return img


def save_ico(img, path):
    sizes = [16, 24, 32, 48, 64, 128, 256]
    icons = []
    for s in sizes:
        icons.append(img.resize((s, s), Image.LANCZOS))
    icons[0].save(path, format="ICO", sizes=[(s, s) for s in sizes], append_images=icons[1:])


def save_icns(img, path):
    # macOS .icns via iconutil
    import tempfile, subprocess
    iconset = tempfile.mkdtemp(suffix=".iconset")
    for size in [16, 32, 64, 128, 256, 512]:
        resized = img.resize((size, size), Image.LANCZOS)
        resized.save(os.path.join(iconset, f"icon_{size}x{size}.png"))
        if size <= 256:
            resized2x = img.resize((size * 2, size * 2), Image.LANCZOS)
            resized2x.save(os.path.join(iconset, f"icon_{size}x{size}@2x.png"))
    subprocess.run(["iconutil", "-c", "icns", iconset, "-o", path], check=True)
    import shutil
    shutil.rmtree(iconset)


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    img = draw_icon(512)

    ico_path = os.path.join(out_dir, "pca_ssh.ico")
    save_ico(img, ico_path)
    print(f"ICO: {ico_path}")

    if sys.platform == "darwin":
        icns_path = os.path.join(out_dir, "pca_ssh.icns")
        save_icns(img, icns_path)
        print(f"ICNS: {icns_path}")

    png_path = os.path.join(out_dir, "pca_ssh.png")
    img.save(png_path)
    print(f"PNG: {png_path}")
