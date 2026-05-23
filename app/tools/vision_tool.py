from dataclasses import asdict, dataclass
from io import BytesIO

import cv2
import numpy as np
from PIL import Image

try:
    from pillow_heif import register_heif_opener
except ImportError:
    register_heif_opener = None

if register_heif_opener:
    register_heif_opener()


@dataclass(frozen=True)
class VisionFeatures:
    face_detected: bool
    eyes: str
    emotion: str
    confidence: float

    def to_dict(self) -> dict[str, bool | str | float]:
        return asdict(self)


def extract_features(image_bytes: bytes) -> VisionFeatures:
    image_array = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        image = _decode_with_pillow(image_bytes)
    if image is None:
        return VisionFeatures(False, "unknown", "neutral", 0.0)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    eye_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60),
    )
    if len(faces) == 0:
        return VisionFeatures(False, "unknown", "neutral", 0.0)

    x, y, w, h = max(faces, key=lambda face: face[2] * face[3])
    face_region = gray[y : y + h, x : x + w]
    upper_face = face_region[: max(1, h // 2), :]
    eyes = eye_detector.detectMultiScale(
        upper_face,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(15, 15),
    )

    eye_state = "open" if len(eyes) >= 1 else "closed"
    emotion = "tired" if eye_state == "closed" else "neutral"

    image_area = image.shape[0] * image.shape[1]
    face_area_ratio = (w * h) / image_area
    confidence = 0.65 + min(face_area_ratio * 2.0, 0.25)
    if eye_state == "closed":
        confidence -= 0.05

    return VisionFeatures(True, eye_state, emotion, round(max(0.0, min(confidence, 0.95)), 2))


def _decode_with_pillow(image_bytes: bytes) -> np.ndarray | None:
    try:
        with Image.open(BytesIO(image_bytes)) as pil_image:
            rgb_image = pil_image.convert("RGB")
            return cv2.cvtColor(np.array(rgb_image), cv2.COLOR_RGB2BGR)
    except Exception:
        return None
