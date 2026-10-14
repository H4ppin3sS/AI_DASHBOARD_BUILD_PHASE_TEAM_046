import pandas as pd
from core.coverage_dynamic import evaluate_targets


def test_image_support_deduplicates_multiple_boxes():
    images = pd.DataFrame([
        {"image_id": 1, "image_name": "a.jpg", "weather": "clear", "timeofday": "day"},
        {"image_id": 2, "image_name": "b.jpg", "weather": "rain", "timeofday": "night"},
    ])
    boxes = pd.DataFrame([
        {"image_id": 1, "label": "car", "valid_geometry": True, "occluded": False, "box_id": 1},
        {"image_id": 1, "label": "car", "valid_geometry": True, "occluded": False, "box_id": 2},
        {"image_id": 2, "label": "bus", "valid_geometry": True, "occluded": False, "box_id": 3},
    ])
    targets = [{"name": "cars", "filters": {"class": "car"}, "unit": "images", "target": 2, "weight": 1}]
    result = evaluate_targets(images, boxes, targets)
    assert len(result) == 1
    assert result.iloc[0]["support"] == 1
    assert result.iloc[0]["gap"] == 1
