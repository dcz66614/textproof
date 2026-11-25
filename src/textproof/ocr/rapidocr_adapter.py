"""TextProof OCR adapter: RapidOCR 3.10.0, ONNX Runtime CPU-only, fully offline.

Frozen model route (PROJECT_BOOK.md §6.2; confirmed against the installed
``rapidocr`` 3.10.0 package ``config.yaml`` defaults and
``default_models.yaml`` routing):

- Detection: PP-OCRv6 ``small`` (``multi_PP-OCRv6_det_small``)
- Recognition: PP-OCRv6 ``small`` (``multi_PP-OCRv6_rec_small``)
- Direction classification: PP-OCRv4 ``mobile``
  (``ch_ppocr_mobile_v2.0_cls_mobile``)

All model files and the recognition dictionary live under an
``assets/ocr`` directory, resolved by :func:`default_assets_dir`:
the checkout ``<repo>/assets/ocr`` in a source tree, or the packaged
``<package>/assets/ocr`` shipped in the wheel (verbatim model copies
plus the dictionary rebuilt there by
``python -m textproof.setup_dictionary``).  An explicit
``TEXTPROOF_ASSETS_DIR`` overrides both.
The adapter verifies every asset (existence + SHA-256) *before* constructing
the RapidOCR engine and passes explicit ``model_path`` values, so RapidOCR
never takes its download path at runtime. A missing or tampered asset raises
instead of triggering a download (fail-closed, PROJECT_BOOK.md §9).

The recognition dictionary (``ppocrv6_dict.txt``, 18,708 entries) is the
character list embedded in the ``PP-OCRv6_rec_small.onnx`` model metadata;
the local copy is byte-identical to that embedded list and to the upstream
registry ``dict_url`` file. At runtime the ONNX engine reads the embedded
copy; the adapter cross-checks the local file against the embedded list on
every start-up so a missing or altered dictionary is a hard error, not a
silent fallback. See THIRD_PARTY_NOTICES.md for the dictionary licence
status (separately verified: no dictionary-specific licence statement was
found; it is NOT covered by the RapidOCR model Apache-2.0 declaration).
"""

from __future__ import annotations

import hashlib
import io
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple, Union

# Privacy (PROJECT_BOOK.md §9; T010 finding F-T010-02): ONNX Runtime
# 1.32.0 official builds ship with 1DS telemetry ON by default.  Every
# process that creates an InferenceSession writes a persistent device
# identifier plus a SQLite telemetry outbox
# (``~/.cache/Microsoft/DeveloperTools/.onnxruntime/onnxruntime.db``)
# and queues SessionCreation / ProcessInfo / EpDeviceUsage /
# ModelLoadEnd events for upload to Microsoft over HTTPS.  That
# violates §9 ("不写数据库、不调用遥测、不发外部 HTTP 请求") even
# though the payloads carry no user data (T010 verified: environment
# and session metadata only — OS, CPU model, ORT version, executable
# path, session GUID, device hash).  The documented runtime opt-out
# is ``ORT_DISABLE_TELEMETRY=1``, which must be set before ONNX
# Runtime initializes; per the bundled ``onnxruntime/Privacy.md`` it
# "prevents the uploader, events, and persistent device identifier
# from being created for the process lifetime".  This module is the
# only place in the repo that ever imports ``onnxruntime`` /
# ``rapidocr`` (both lazily, inside methods), so setting it here at
# import time covers every product entry point (CLI, API, serve,
# verify-s0).  Set unconditionally: §9 forbids telemetry, so an
# ambient ``ORT_DISABLE_TELEMETRY=0`` must not re-enable it.
os.environ["ORT_DISABLE_TELEMETRY"] = "1"

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Frozen by PROJECT_BOOK.md §6.2 and T001 requirements.lock.
RAPIDOCR_VERSION = "3.10.0"
ONNXRUNTIME_VERSION = "1.32.0"
# The only execution provider that may ever be used.
ALLOWED_PROVIDERS = ("CPUExecutionProvider",)

# Frozen model route. Keys: (asset file name, registry URL, SHA-256,
# registry model_key). Source: rapidocr 3.10.0 ``default_models.yaml``
# (``onnxruntime`` section) and the official model licence page
# https://rapidai.github.io/RapidOCRDocs/latest/en/model_licenses/ §6,
# which lists exactly these three artifacts and hashes.
DET_MODEL = (
    "PP-OCRv6_det_small.onnx",
    "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv6/det/PP-OCRv6_det_small.onnx",
    "090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f",
    "multi_PP-OCRv6_det_small",
)
REC_MODEL = (
    "PP-OCRv6_rec_small.onnx",
    "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv6/rec/PP-OCRv6_rec_small.onnx",
    "6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884",
    "multi_PP-OCRv6_rec_small",
)
CLS_MODEL = (
    "ch_ppocr_mobile_v2.0_cls_mobile.onnx",
    "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv4/cls/ch_ppocr_mobile_v2.0_cls_mobile.onnx",
    "e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c",
    "ch_ppocr_mobile_v2.0_cls_mobile",
)

# Recognition dictionary: the PP-OCRv6 multilingual character list.
# Registry dict_url (rapidocr 3.10.0 default_models.yaml, paddle/torch
# PP-OCRv6 rec entries) and PaddleOCR upstream:
#   https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/paddle/PP-OCRv6/rec/PP-OCRv6_rec_small/ppocrv6_dict.txt
#   https://github.com/PaddlePaddle/PaddleOCR/blob/main/ppocr/utils/dict/ppocrv6_dict.txt
# All three copies (registry download, upstream file, model-embedded
# metadata) were verified byte-identical during T003 (18,708 lines).
DICT_FILE = (
    "ppocrv6_dict.txt",
    "https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/paddle/PP-OCRv6/rec/PP-OCRv6_rec_small/ppocrv6_dict.txt",
    "b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d",
    18708,  # line count
)

MODEL_FILES = (DET_MODEL, REC_MODEL, CLS_MODEL)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _has_models(assets_dir: Path) -> bool:
    """True when ``assets_dir/models`` holds all three frozen models."""
    models = assets_dir / "models"
    return all((models / name).is_file() for name, _url, _sha, _key in MODEL_FILES)


def default_assets_dir() -> Path:
    """Resolve the ``assets/ocr`` directory for this installation.

    Resolution order (T013-U01: the installed wheel must run with no
    source checkout, PROJECT_BOOK.md §11.2):

    1. ``TEXTPROOF_ASSETS_DIR`` when set (explicit override wins).
    2. The checkout assets at ``<repo>/assets/ocr`` when they hold
       the three frozen models — the source-tree behaviour, unchanged.
    3. The packaged assets at ``<package>/assets/ocr`` (the verbatim
       model copies shipped in the wheel, plus the dictionary rebuilt
       there by ``python -m textproof.setup_dictionary``).
    4. Otherwise the checkout path, so a missing-asset error names
       the familiar location instead of failing in an odd place.

    The dictionary is always resolved from the same directory the
    models come from: a checkout dictionary lives under the checkout
    assets, an installed dictionary under the packaged assets.
    """
    env_dir = os.environ.get("TEXTPROOF_ASSETS_DIR")
    if env_dir:
        return Path(env_dir)
    checkout = Path(__file__).resolve().parents[3] / "assets" / "ocr"
    if _has_models(checkout):
        return checkout
    packaged = Path(__file__).resolve().parents[1] / "assets" / "ocr"
    if _has_models(packaged):
        return packaged
    return checkout


def _default_assets_dir() -> Path:
    """Backwards-compatible alias for :func:`default_assets_dir`."""
    return default_assets_dir()


@dataclass(frozen=True)
class OCRLine:
    """One recognised text line (IMPLEMENTATION_PLAN.md §5.1, PROJECT_BOOK.md §7.1).

    ``line_index`` is the zero-based index in RapidOCR output order; at this
    layer it is identical to ``source_order``. Reading-order reassignment is
    owned by T004 (``core/line_order.py``) and must not be done here.
    """

    line_index: int
    text: str
    confidence: float
    bbox_xyxy: Tuple[float, float, float, float]
    quad: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float], Tuple[float, float]]
    source_order: int

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        """Alias for ``bbox_xyxy`` (axis-aligned bounding box)."""
        return self.bbox_xyxy


class OCRAdapterError(RuntimeError):
    """Raised when the OCR engine cannot run (missing asset, bad provider, ...)."""


class RapidOCRAdapter:
    """CPU-only, offline RapidOCR adapter with fail-closed local assets.

    Parameters
    ----------
    assets_dir:
        Directory holding ``models/`` (three ``.onnx`` files) and
        ``dictionaries/ppocrv6_dict.txt``. Defaults to
        :func:`default_assets_dir` (checkout assets in a source tree,
        packaged assets in an installed wheel).
    """

    def __init__(self, assets_dir: Union[str, Path, None] = None) -> None:
        self.assets_dir = Path(assets_dir) if assets_dir is not None else _default_assets_dir()
        self.models_dir = self.assets_dir / "models"
        self.dict_path = self.assets_dir / "dictionaries" / DICT_FILE[0]

        self._check_versions()
        self._verify_assets()
        self._engine = self._build_engine()
        # Eagerly load the three sessions so a bad model / wrong provider is
        # a start-up error, not a first-request surprise, and so the provider
        # assertion below runs before any recognition.
        self._load_sessions()
        self._assert_cpu_only()
        self._verify_dictionary_matches_model()

    # -- start-up checks -------------------------------------------------

    def _check_versions(self) -> None:
        import importlib.metadata as _md

        rapidocr_version = _md.version("rapidocr")
        if rapidocr_version != RAPIDOCR_VERSION:
            raise OCRAdapterError(
                f"rapidocr version is {rapidocr_version}, frozen version is "
                f"{RAPIDOCR_VERSION}; refusing to run."
            )
        onnx_version = _md.version("onnxruntime")
        if onnx_version != ONNXRUNTIME_VERSION:
            raise OCRAdapterError(
                f"onnxruntime version is {onnx_version}, frozen version is "
                f"{ONNXRUNTIME_VERSION}; refusing to run."
            )

    def _verify_assets(self) -> None:
        """Existence + SHA-256 for every model and the dictionary.

        Raises FileNotFoundError / ValueError. This runs *before* any
        RapidOCR object exists, so a missing asset can never fall through to
        RapidOCR's download path.
        """
        for filename, _url, sha256, _key in MODEL_FILES:
            path = self.models_dir / filename
            if not path.is_file():
                # R-04 (PROJECT_BOOK.md §9): the message must name only
                # the file, never the absolute path — it used to carry
                # ``{path}`` and leaked the deployment directory into
                # server logs via logger.exception.
                raise FileNotFoundError(
                    f"OCR model asset missing: {filename}. Refusing to "
                    "download at runtime (offline-only operation)."
                )
            actual = _sha256_file(path)
            if actual != sha256:
                raise ValueError(
                    f"OCR model asset hash mismatch: {filename}\n"
                    f"  expected: {sha256}\n  actual:   {actual}"
                )
        if not self.dict_path.is_file():
            raise FileNotFoundError(
                f"OCR dictionary asset missing: {DICT_FILE[0]}. Refusing "
                "to download at runtime (offline-only operation)."
            )
        actual = _sha256_file(self.dict_path)
        if actual != DICT_FILE[2]:
            raise ValueError(
                f"OCR dictionary hash mismatch: {DICT_FILE[0]}\n"
                f"  expected: {DICT_FILE[2]}\n  actual:   {actual}"
            )

    def _build_engine(self):
        """Construct RapidOCR with explicit local model paths.

        Explicit ``model_path`` values make
        ``rapidocr.inference_engine.onnxruntime.OrtInferSession`` skip its
        download branch entirely (it only resolves/downloads when
        ``model_path`` is None). ``Global.model_root_dir`` is also pointed at
        the local models directory so no other code path can resolve a
        remote location.
        """
        from rapidocr import RapidOCR

        det_path = str(self.models_dir / DET_MODEL[0])
        cls_path = str(self.models_dir / CLS_MODEL[0])
        rec_path = str(self.models_dir / REC_MODEL[0])
        params = {
            "Global.model_root_dir": str(self.models_dir),
            "Global.log_level": "error",
            "Det.model_path": det_path,
            "Cls.model_path": cls_path,
            "Rec.model_path": rec_path,
            # Belt and braces: every non-CPU execution provider off.
            "EngineConfig.onnxruntime.use_cuda": False,
            "EngineConfig.onnxruntime.use_dml": False,
            "EngineConfig.onnxruntime.use_cann": False,
            "EngineConfig.onnxruntime.use_coreml": False,
        }
        return RapidOCR(params=params)

    def _load_sessions(self) -> None:
        # RapidOCR 3.10.0 loads each sub-model lazily on first use; these
        # are its pinned-version loader entry points. Loading eagerly makes
        # start-up fail-closed and lets the provider check run up front.
        self._engine._load_det_model()
        self._engine._load_cls_model()
        self._engine._load_rec_model()

    def _sessions(self):
        return {
            "det": self._engine.text_det.session.session,
            "cls": self._engine.text_cls.session.session,
            "rec": self._engine.text_rec.session.session,
        }

    def _assert_cpu_only(self) -> None:
        for name, session in self._sessions().items():
            providers = list(session.get_providers())
            if providers != list(ALLOWED_PROVIDERS):
                raise OCRAdapterError(
                    f"ONNX Runtime providers for {name} are {providers}, "
                    f"expected exactly {list(ALLOWED_PROVIDERS)}; refusing "
                    "to run."
                )

    def _embedded_characters(self) -> List[str]:
        """Character list embedded in the recognition model's metadata."""
        import onnxruntime as ort

        session = ort.InferenceSession(
            str(self.models_dir / REC_MODEL[0]),
            providers=list(ALLOWED_PROVIDERS),
        )
        meta = session.get_modelmeta().custom_metadata_map
        if "character" not in meta:
            raise OCRAdapterError(
                "Recognition model carries no embedded 'character' metadata; "
                "cannot verify the dictionary."
            )
        return meta["character"].splitlines()

    def _verify_dictionary_matches_model(self) -> None:
        embedded = self._embedded_characters()
        local = self.dict_path.read_text(encoding="utf-8").splitlines()
        if local != embedded:
            raise OCRAdapterError(
                "Local dictionary does not match the character list embedded "
                f"in {REC_MODEL[0]} ({len(local)} local lines vs "
                f"{len(embedded)} embedded); refusing to run."
            )
        if len(local) != DICT_FILE[3]:
            raise OCRAdapterError(
                f"Dictionary line count is {len(local)}, expected "
                f"{DICT_FILE[3]}."
            )

    # -- public interface ------------------------------------------------

    @property
    def providers(self) -> dict:
        """Actual ONNX Runtime providers per sub-model, e.g. ``{'det': [...]}``."""
        return {name: list(s.get_providers()) for name, s in self._sessions().items()}

    @property
    def model_info(self) -> dict:
        """Frozen model route + asset hashes (for reports / diagnostics)."""
        return {
            "rapidocr_version": RAPIDOCR_VERSION,
            "onnxruntime_version": ONNXRUNTIME_VERSION,
            "providers": self.providers,
            "det": {"file": DET_MODEL[0], "model_key": DET_MODEL[3],
                    "url": DET_MODEL[1], "sha256": DET_MODEL[2]},
            "rec": {"file": REC_MODEL[0], "model_key": REC_MODEL[3],
                    "url": REC_MODEL[1], "sha256": REC_MODEL[2]},
            "cls": {"file": CLS_MODEL[0], "model_key": CLS_MODEL[3],
                    "url": CLS_MODEL[1], "sha256": CLS_MODEL[2]},
            "dict": {"file": DICT_FILE[0], "url": DICT_FILE[1],
                     "sha256": DICT_FILE[2], "lines": DICT_FILE[3]},
        }

    def recognize(
        self, image: Union[bytes, bytearray, np.ndarray, Image.Image]
    ) -> List[OCRLine]:
        """Run OCR on one image; return lines in RapidOCR output order.

        Accepts PNG/JPEG/WebP bytes, a NumPy ``(H, W, 3)`` uint8 array, or a
        PIL image. Returns ``[]`` when no text is found (that is a valid
        empty result; callers decide between ``OCR_FAILED`` and empty input).
        Raises :class:`ValueError` for undecodable input and
        :class:`OCRAdapterError` for engine failures. Never logs image bytes
        or recognised text (PROJECT_BOOK.md §9).
        """
        array = _to_numpy_array(image)
        result = self._engine(array)
        if result is None or result.txts is None or result.boxes is None:
            return []
        lines: List[OCRLine] = []
        for order, (text, score, quad) in enumerate(
            zip(result.txts, result.scores, result.boxes)
        ):
            text = str(text)
            if not text.strip():
                continue
            quad_pts = tuple(
                (round(float(p[0]), 2), round(float(p[1]), 2)) for p in quad
            )
            xs = [p[0] for p in quad_pts]
            ys = [p[1] for p in quad_pts]
            bbox = (min(xs), min(ys), max(xs), max(ys))
            lines.append(
                OCRLine(
                    line_index=order,
                    text=text,
                    confidence=max(0.0, min(1.0, float(score))),
                    bbox_xyxy=bbox,
                    quad=quad_pts,  # type: ignore[arg-type]
                    source_order=order,
                )
            )
        # RapidOCR already drops blank texts before returning, so `order`
        # is a dense 0..n-1 sequence and doubles as line_index/source_order.
        logger.info("OCR completed: %d line(s) recognised", len(lines))
        return lines


def _to_numpy_array(
    image: Union[bytes, bytearray, np.ndarray, Image.Image],
) -> np.ndarray:
    if isinstance(image, np.ndarray):
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(
                f"NumPy image must have shape (H, W, 3); got {image.shape}."
            )
        return image
    if isinstance(image, Image.Image):
        return np.asarray(image.convert("RGB"))
    if isinstance(image, (bytes, bytearray)):
        if not image:
            raise ValueError("Empty image bytes.")
        try:
            with Image.open(io.BytesIO(bytes(image))) as pil:
                return np.asarray(pil.convert("RGB"))
        except Exception as exc:
            raise ValueError(f"Cannot decode image bytes: {exc}") from exc
    raise TypeError(
        f"Unsupported image input type: {type(image).__name__}. Expected "
        "bytes, numpy.ndarray, or PIL.Image.Image."
    )


__all__ = [
    "OCRLine",
    "RapidOCRAdapter",
    "OCRAdapterError",
    "default_assets_dir",
    "RAPIDOCR_VERSION",
    "ONNXRUNTIME_VERSION",
    "ALLOWED_PROVIDERS",
    "DET_MODEL",
    "REC_MODEL",
    "CLS_MODEL",
    "DICT_FILE",
]
