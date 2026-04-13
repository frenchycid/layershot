"""PostProcessor Agent — Color grading for generated images to match a reference moodboard style."""

import logging
import numpy as np
from pathlib import Path

from PIL import Image, ImageEnhance

log = logging.getLogger("post_processor")


class PostProcessor:
    """Applies automatic color grading to generated images based on a reference image."""

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Core adjustments
    # ------------------------------------------------------------------

    def adjust_exposure(self, image: Image.Image, factor: float = 1.0) -> Image.Image:
        """Adjust brightness/exposure of an image.

        Args:
            image: Source PIL image.
            factor: Multiplier. > 1.0 = brighter, < 1.0 = darker, 1.0 = unchanged.

        Returns:
            New PIL image with adjusted exposure.
        """
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(factor)

    def adjust_saturation(self, image: Image.Image, factor: float = 1.0) -> Image.Image:
        """Adjust color saturation of an image.

        Args:
            image: Source PIL image.
            factor: Multiplier. 0.0 = grayscale, 1.0 = original, 2.0 = double saturation.

        Returns:
            New PIL image with adjusted saturation.
        """
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(factor)

    def adjust_temperature(self, image: Image.Image, shift: int = 0) -> Image.Image:
        """Shift the color temperature of an image.

        Args:
            image: Source PIL image.
            shift: Positive values warm the image (boost red, reduce blue);
                   negative values cool it (boost blue, reduce red).

        Returns:
            New PIL image with adjusted temperature.
        """
        if shift == 0:
            return image.copy()

        arr = np.array(image, dtype=np.float32)

        # Apply shift proportional to the shift value (capped at ±255)
        shift_clamped = max(-255, min(255, shift))

        # Red channel: add for warm, subtract for cool
        arr[:, :, 0] = np.clip(arr[:, :, 0] + shift_clamped, 0, 255)
        # Blue channel: subtract for warm, add for cool
        arr[:, :, 2] = np.clip(arr[:, :, 2] - shift_clamped, 0, 255)

        return Image.fromarray(arr.astype(np.uint8))

    # ------------------------------------------------------------------
    # Style matching
    # ------------------------------------------------------------------

    def match_style(self, image: Image.Image, reference: Image.Image) -> Image.Image:
        """Analyse the reference image and apply its style to the source image.

        Computes:
        - Exposure ratio (luminance of reference vs. image).
        - Saturation ratio (colorfulness of reference vs. image).
        - Temperature shift (mean red-blue balance of reference vs. image).

        Args:
            image: The image to grade.
            reference: The moodboard / style reference.

        Returns:
            New PIL image with style applied.
        """
        img_rgb = image.convert("RGB")
        ref_rgb = reference.convert("RGB")

        img_arr = np.array(img_rgb, dtype=np.float32)
        ref_arr = np.array(ref_rgb, dtype=np.float32)

        # --- Exposure ---
        img_lum = img_arr.mean()
        ref_lum = ref_arr.mean()
        exposure_factor = (ref_lum / img_lum) if img_lum > 0 else 1.0
        # Clamp to a reasonable range to avoid extreme changes
        exposure_factor = float(np.clip(exposure_factor, 0.2, 5.0))

        # --- Saturation ---
        img_sat = self._colorfulness(img_arr)
        ref_sat = self._colorfulness(ref_arr)
        sat_factor = (ref_sat / img_sat) if img_sat > 0 else 1.0
        sat_factor = float(np.clip(sat_factor, 0.0, 4.0))

        # --- Temperature shift ---
        img_temp = float(img_arr[:, :, 0].mean() - img_arr[:, :, 2].mean())
        ref_temp = float(ref_arr[:, :, 0].mean() - ref_arr[:, :, 2].mean())
        temp_shift = int(np.clip((ref_temp - img_temp) / 2, -128, 128))

        # Apply adjustments in order: exposure → saturation → temperature
        result = self.adjust_exposure(img_rgb, factor=exposure_factor)
        result = self.adjust_saturation(result, factor=sat_factor)
        result = self.adjust_temperature(result, shift=temp_shift)

        return result

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------

    def process(self, input_path: Path, reference_path: Path, output_path: Path) -> Path:
        """Full pipeline: load → match_style → save.

        Args:
            input_path: Path to the generated image to process.
            reference_path: Path to the reference / moodboard image.
            output_path: Destination path for the graded image.

        Returns:
            The output_path where the result was saved.
        """
        input_path = Path(input_path)
        reference_path = Path(reference_path)
        output_path = Path(output_path)

        log.info(f"PostProcessor: loading {input_path}")
        image = Image.open(input_path).convert("RGB")
        reference = Image.open(reference_path).convert("RGB")

        log.info("PostProcessor: applying style match...")
        result = self.match_style(image, reference)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(output_path)
        log.info(f"PostProcessor: saved to {output_path}")

        return output_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _colorfulness(arr: np.ndarray) -> float:
        """Compute a simple colorfulness metric (Hasler & Süsstrunk, 2003).

        A higher value means more saturated / colorful.
        """
        r = arr[:, :, 0].astype(float)
        g = arr[:, :, 1].astype(float)
        b = arr[:, :, 2].astype(float)

        rg = np.abs(r - g)
        yb = np.abs(0.5 * (r + g) - b)

        mean_rg = rg.mean()
        mean_yb = yb.mean()
        std_rg = rg.std()
        std_yb = yb.std()

        colorfulness = np.sqrt(std_rg ** 2 + std_yb ** 2) + 0.3 * np.sqrt(mean_rg ** 2 + mean_yb ** 2)
        return float(colorfulness)
