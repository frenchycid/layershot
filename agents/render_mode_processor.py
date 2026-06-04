"""Render Mode Processor — Per-mode post-processing with real AI background removal."""
import logging
import numpy as np
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image, ImageEnhance, ImageFilter
from agents.material_enhancement_agent import MaterialEnhancementAgent

log = logging.getLogger("render_mode_processor")

# Lazy-load rembg sessions
_rembg_session = None
_human_seg_session = None

# Threshold: if human-seg model finds humans covering > this fraction of the image,
# we mask them out and retry product extraction.
_HUMAN_PRESENCE_THRESHOLD = 0.12   # 12 % of total pixels


def _get_rembg_session():
    """Lazy-load rembg product-extraction session (u2net)."""
    global _rembg_session
    if _rembg_session is None:
        try:
            from rembg import new_session
            _rembg_session = new_session("u2net")
            log.info("rembg session loaded (u2net)")
        except ImportError:
            log.warning("rembg not installed — isolated mode will use fallback")
            _rembg_session = "unavailable"
    return _rembg_session


def _get_human_seg_session():
    """Lazy-load rembg human-segmentation session (u2net_human_seg)."""
    global _human_seg_session
    if _human_seg_session is None:
        try:
            from rembg import new_session
            _human_seg_session = new_session("u2net_human_seg")
            log.info("rembg human_seg session loaded")
        except Exception:
            log.warning("u2net_human_seg unavailable — human detection disabled")
            _human_seg_session = "unavailable"
    return _human_seg_session


def _boost_saturation_hsv(image: Image.Image, factor: float) -> Image.Image:
    """Boost saturation in HSV space — preserves hue, no colour shift."""
    hsv = image.convert("HSV")
    arr = np.array(hsv, dtype=np.float32)
    arr[:, :, 1] = np.clip(arr[:, :, 1] * factor, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode="HSV").convert("RGB")


class RenderModeProcessor:
    """Orchestrates render mode-specific post-processing."""

    def __init__(self):
        self.material_enhancer = MaterialEnhancementAgent()

    def process(self, image: Image.Image, product_context: str, render_mode: str, save_to: Optional[Path] = None) -> Image.Image:
        """Process image according to render mode."""
        if render_mode not in ["isolated", "white_background", "enhanced"]:
            raise KeyError(f"Unknown render mode: {render_mode}")

        log.info(f"Processing image in {render_mode} mode")

        if render_mode == "isolated":
            result = self._process_isolated(image)
        elif render_mode == "white_background":
            result = self._process_white_background(image)
        elif render_mode == "enhanced":
            result = self._process_enhanced(image, product_context)

        if save_to:
            save_to.parent.mkdir(parents=True, exist_ok=True)
            result.save(save_to)
            log.info(f"Processed image saved to {save_to}")

        return result

    def _process_isolated(self, image: Image.Image) -> Image.Image:
        """Remove background using rembg AI — output transparent PNG.

        Bug-2 fix: before running product extraction, the u2net_human_seg
        model checks whether people dominate the scene.  If they do, their
        pixels are replaced with sampled background colour so rembg focuses
        on the product instead of the person.
        """
        session = _get_rembg_session()
        if session != "unavailable":
            try:
                from rembg import remove
                src = image

                # ── Bug-2 fix: detect & erase humans before product extraction ──
                has_humans, human_alpha = self._detect_humans(image)
                if has_humans:
                    log.info(
                        f"Human body detected ({(human_alpha > 128).mean():.0%} of frame) "
                        "— erasing before product extraction"
                    )
                    src = self._erase_human_regions(image, human_alpha)

                result = remove(src, session=session, bgcolor=None)
                log.info("Background removed via rembg")
                return result
            except Exception as e:
                log.warning(f"rembg failed ({e}), using fallback")

        # Fallback: simple threshold-based removal
        if image.mode != "RGBA":
            image = image.convert("RGBA")
        img_array = np.array(image)
        gray = np.mean(img_array[:, :, :3], axis=2)
        img_array[gray > 240, 3] = 0
        return Image.fromarray(img_array)

    def _process_white_background(self, image: Image.Image) -> Image.Image:
        """Remove background, add synthetic contact shadow, composite on white.

        The contact shadow is a soft elliptical gradient placed at the base of
        the product — it simulates the natural shadow a product casts on a white
        cyclorama floor, which rembg would otherwise remove entirely.
        """
        # First remove background
        isolated = self._process_isolated(image)

        w, h = isolated.size
        alpha = np.array(isolated.convert("RGBA"), dtype=np.float32)[:, :, 3]

        # ── Compute product bounding box from alpha mask ──────────────────────
        rows = np.any(alpha > 32, axis=1)
        cols = np.any(alpha > 32, axis=0)
        if rows.any() and cols.any():
            y_min, y_max = np.where(rows)[0][[0, -1]]
            x_min, x_max = np.where(cols)[0][[0, -1]]
        else:
            y_min, y_max = 0, h - 1
            x_min, x_max = 0, w - 1

        prod_width = int(x_max - x_min)
        prod_cx = int((x_min + x_max) / 2)
        base_y = int(y_max)  # bottom edge of product

        # ── Generate contact shadow layer ─────────────────────────────────────
        shadow_layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        shadow_arr = np.zeros((h, w), dtype=np.float32)

        # Shadow ellipse parameters: wide & flat (x:y ratio ~3:1)
        sx = max(int(prod_width * 0.55), 20)   # half-width
        sy = max(int(prod_width * 0.12), 6)    # half-height (flat shadow)
        shadow_center_y = base_y + sy           # just below product base

        # Clamp to image bounds
        shadow_center_y = min(shadow_center_y, h - 1)

        # Build elliptical Gaussian shadow
        for dy in range(-sy * 3, sy * 3 + 1):
            py = shadow_center_y + dy
            if py < 0 or py >= h:
                continue
            for dx in range(-sx * 3, sx * 3 + 1):
                px = prod_cx + dx
                if px < 0 or px >= w:
                    continue
                # Normalised ellipse distance
                dist = ((dx / sx) ** 2 + (dy / sy) ** 2) ** 0.5
                intensity = max(0.0, 1.0 - dist)
                shadow_arr[py, px] = max(shadow_arr[py, px], intensity)

        # Gaussian blur to soften the shadow
        shadow_img = Image.fromarray((shadow_arr * 80).astype(np.uint8), mode="L")
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=max(sx // 4, 4)))

        # ── Composite: white → shadow → product ──────────────────────────────
        white_bg = Image.new("RGBA", (w, h), (255, 255, 255, 255))

        # Darken white bg by shadow opacity
        shadow_rgba = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        shadow_rgba.putalpha(shadow_img)
        white_bg = Image.alpha_composite(white_bg, shadow_rgba)

        # Paste isolated product on top
        white_bg.paste(isolated, (0, 0), isolated)

        result = white_bg.convert("RGB")

        # Slight brightness boost for clean studio feel
        enhancer = ImageEnhance.Brightness(result)
        result = enhancer.enhance(1.03)

        log.info(f"White background composite done (contact shadow: cx={prod_cx}, base_y={base_y}, sx={sx}, sy={sy})")
        return result

    def _process_enhanced(self, image: Image.Image, product_context: str) -> Image.Image:
        """Remove background, enhance materials, composite on neutral gradient.

        Bug-1 fix: saturation is now boosted in HSV space (hue-preserving) and
        the gradient background uses a neutral white instead of warm beige, so
        brand colours (e.g. Sephora blush pink) are not shifted toward caramel.
        """
        # Remove background first
        isolated = self._process_isolated(image)

        # Neutral gradient background — pure white at top, very subtle grey at bottom
        # (was warm (245, 243, 240) which tinted pink products beige)
        w, h = isolated.size
        gradient = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        arr = np.array(gradient, dtype=np.float32)
        for y in range(h):
            factor = 1.0 - (y / h) * 0.04  # gentler 4% top-to-bottom darkening
            arr[y, :, :3] *= factor
        gradient = Image.fromarray(arr.astype(np.uint8))

        # Composite
        gradient.paste(isolated, (0, 0), isolated)
        result = gradient.convert("RGB")

        # Sharpness boost — makes textures pop (unchanged)
        result = ImageEnhance.Sharpness(result).enhance(1.6)

        # Contrast boost — reduced from 1.25 → 1.12 to avoid amplifying warm cast
        result = ImageEnhance.Contrast(result).enhance(1.12)

        # Hue-preserving saturation boost in HSV space (was RGB 1.3× which shifts pink → orange)
        result = _boost_saturation_hsv(result, factor=1.25)

        # Slight brightness lift (unchanged)
        result = ImageEnhance.Brightness(result).enhance(1.05)

        # Apply material-specific enhancements on top
        result = self.material_enhancer.process(result, product_context)

        log.info("Enhanced mode with hue-preserving material processing done")
        return result

    # ── Human detection helpers (Bug-2 fix) ──────────────────────────────────

    @staticmethod
    def _detect_humans(
        image: Image.Image,
        threshold: float = _HUMAN_PRESENCE_THRESHOLD,
    ) -> Tuple[bool, np.ndarray]:
        """Use u2net_human_seg to detect human bodies in the image.

        Returns (has_humans, human_alpha_array) where human_alpha_array is a
        uint8 (H, W) array with 255 where a human was detected, 0 elsewhere.

        Falls back to an all-zero mask if the human-seg model is unavailable.
        """
        h, w = image.size[1], image.size[0]
        empty = np.zeros((h, w), dtype=np.uint8)

        human_session = _get_human_seg_session()
        if human_session == "unavailable":
            return False, empty

        try:
            from rembg import remove
            human_result = remove(image, session=human_session, bgcolor=None)
            alpha = np.array(human_result.convert("RGBA"), dtype=np.float32)[:, :, 3]
            human_alpha = (alpha > 128).astype(np.uint8) * 255
            ratio = float((human_alpha > 128).mean())
            log.debug(f"Human-seg coverage: {ratio:.1%}")
            return ratio > threshold, human_alpha
        except Exception as e:
            log.debug(f"Human-seg failed ({e})")
            return False, empty

    @staticmethod
    def _erase_human_regions(image: Image.Image, human_alpha: np.ndarray) -> Image.Image:
        """Replace pixels where humans were detected with sampled background colour.

        Sampling background from image corners avoids any hardcoded colour and
        works regardless of environment lighting (including VP passthrough).
        """
        arr = np.array(image.convert("RGB"), dtype=np.float32)
        h, w = arr.shape[:2]

        # Sample background from 5 % corner patches
        pad = max(int(min(h, w) * 0.05), 4)
        corners = np.concatenate([
            arr[:pad, :pad].reshape(-1, 3),
            arr[:pad, -pad:].reshape(-1, 3),
            arr[-pad:, :pad].reshape(-1, 3),
            arr[-pad:, -pad:].reshape(-1, 3),
        ], axis=0)
        bg_color = corners.mean(axis=0)

        mask = human_alpha > 128
        arr[mask] = bg_color
        log.debug(
            f"Erased {mask.sum()} human pixels ({mask.mean():.1%} of frame) "
            f"with bg colour R={bg_color[0]:.0f} G={bg_color[1]:.0f} B={bg_color[2]:.0f}"
        )
        return Image.fromarray(arr.astype(np.uint8), mode="RGB")

    def batch_process(self, images: List[Image.Image], product_context: str, render_mode: str, output_dir: Optional[Path] = None) -> List[Image.Image]:
        """Process multiple images with same mode."""
        results = []
        for idx, img in enumerate(images):
            output_path = None
            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{render_mode}_{idx:04d}.png"

            result = self.process(img, product_context, render_mode, save_to=output_path)
            results.append(result)

        log.info(f"Batch processed {len(results)} images in {render_mode} mode")
        return results
