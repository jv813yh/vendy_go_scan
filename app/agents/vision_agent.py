from app.tools.vision_tool import VisionFeatures, extract_features


def analyze_image(image_bytes: bytes) -> VisionFeatures:
    return extract_features(image_bytes)
