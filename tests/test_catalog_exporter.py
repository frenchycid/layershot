"""Tests for CatalogExporter — multi-format image export agent."""

from pathlib import Path
from PIL import Image
import pytest

from agents.catalog_exporter import CatalogExporter


def make_image(width: int = 2400, height: int = 3000, color: str = "red") -> Image.Image:
    """Create a synthetic RGB test image."""
    return Image.new("RGB", (width, height), color=color)


# ─── Test 1 : export_web ────────────────────────────────────────────────────

def test_export_web_creates_jpeg_72dpi_max_1920(tmp_path):
    exporter = CatalogExporter()
    img = make_image(2400, 3000)
    out = tmp_path / "web.jpg"

    result = exporter.export_web(img, out)

    assert result == out
    assert out.exists()
    with Image.open(out) as saved:
        assert saved.format == "JPEG"
        assert max(saved.size) <= 1920
        dpi = saved.info.get("dpi", (72, 72))
        assert round(dpi[0]) == 72


# ─── Test 2 : export_print ──────────────────────────────────────────────────

def test_export_print_creates_png_300dpi(tmp_path):
    exporter = CatalogExporter()
    img = make_image(800, 1000)
    out = tmp_path / "print.png"

    result = exporter.export_print(img, out)

    assert result == out
    assert out.exists()
    with Image.open(out) as saved:
        assert saved.format == "PNG"
        assert saved.size == (800, 1000)
        dpi = saved.info.get("dpi", (300, 300))
        assert round(dpi[0]) == 300


# ─── Test 3 : export_social ─────────────────────────────────────────────────

def test_export_social_creates_three_variants(tmp_path):
    exporter = CatalogExporter()
    img = make_image(1200, 1500)

    result = exporter.export_social(img, tmp_path)

    assert set(result.keys()) == {"square", "portrait", "story"}

    # square 1:1
    with Image.open(result["square"]) as sq:
        assert sq.size[0] == sq.size[1]

    # portrait 4:5
    with Image.open(result["portrait"]) as po:
        ratio = po.size[0] / po.size[1]
        assert abs(ratio - 4 / 5) < 0.02

    # story 9:16
    with Image.open(result["story"]) as st:
        ratio = st.size[0] / st.size[1]
        assert abs(ratio - 9 / 16) < 0.02


# ─── Test 4 : export_ecommerce ──────────────────────────────────────────────

def test_export_ecommerce_creates_white_background_square(tmp_path):
    exporter = CatalogExporter()
    img = make_image(600, 900, color="blue")
    out = tmp_path / "ecom.png"

    result = exporter.export_ecommerce(img, out)

    assert result == out
    assert out.exists()
    with Image.open(out) as saved:
        # Must be square
        assert saved.size[0] == saved.size[1]
        # Corner pixels should be white (background)
        px = saved.convert("RGB").getpixel((0, 0))
        assert px == (255, 255, 255)


# ─── Test 5 : export_all ────────────────────────────────────────────────────

def test_export_all_creates_sku_subfolder_with_all_variants(tmp_path):
    exporter = CatalogExporter()
    # Write a real JPEG to disk so export_all can open it
    img = make_image(1200, 1500)
    src = tmp_path / "source.jpg"
    img.save(src, format="JPEG")

    result = exporter.export_all(src, tmp_path, sku="SKU-001")

    sku_dir = tmp_path / "SKU-001"
    assert sku_dir.is_dir()

    expected_keys = {"web", "print", "square", "portrait", "story", "ecommerce"}
    assert expected_keys == set(result.keys())

    for key, path in result.items():
        assert Path(path).exists(), f"Missing file for key '{key}': {path}"
        assert Path(path).parent == sku_dir
