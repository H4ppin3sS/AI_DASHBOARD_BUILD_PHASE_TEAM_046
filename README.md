# CVAT Quality Control Dashboard

Dashboard cho Leader thống kê phân bố nhãn CVAT, kiểm tra chất lượng ảnh và tín hiệu bất thường của bounding box, phân tích coverage/slice và truy tìm ảnh theo metadata **weather × timeofday**. **Không yêu cầu Ground Truth**.

## Tính năng

- **Overview:** Tổng ảnh, số nhãn, trạng thái kiểm tra.
- **Distribution & Attributes:** Phân bố class, kích thước box, occlusion, thời tiết và thời điểm.
- **Scene Finder:** Lọc ảnh theo weather/timeofday (bao gồm `unknown` và `missing`), xem ảnh nếu ZIP chứa ảnh gốc, xuất CSV.
- **Image Quality:** Blur, brightness, contrast, noise và các cảnh báo.
- **Label Check A+B:** Kiểm tra hình học box và tín hiệu bất thường từ pixel ảnh.
- **Coverage & Slice:** Slice do Leader cấu hình động, so sánh observed/target, gap, attainment, weighted gap và gợi ý slice cần review/bổ sung.
- **Reports:** Xuất báo cáo.

> Các tín hiệu chất lượng không phải kết luận annotation sai; cần người review xác nhận. Coverage thấp cũng không tự động đồng nghĩa với dữ liệu sai hoặc thiếu.

## Khởi chạy

Yêu cầu Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Mở http://localhost:8501, upload ZIP từ CVAT (có `annotations.xml`; kèm ảnh nếu muốn preview/kiểm tra pixel).

## Scene Finder

Trong tab **Phân bố & thuộc tính**, tới phần **Phân bố kết hợp thời tiết × thời điểm**. Chọn Weather=`unknown` và Time of day=`unknown` để tìm ảnh có cả hai trường. `missing` khác `unknown`.

## Coverage

Tại tab **Coverage & Slice**, tạo slice thủ công, sinh tổ hợp tự động hoặc nhập JSON. Chọn `unit=images` hoặc `objects`, nhập `target` (số lượng tuyệt đối) và `weight`. Không hard-code class hoặc target. `attainment_pct = support / target × 100`; `gap = max(0, target-support)`.

## Cấu trúc repository

```text
app.py                     # Streamlit entry point
ui_theme.py                # Modern theme
core/
  distribution.py          # Phân bố nhãn, thuộc tính
  coverage_dynamic.py      # Công thức coverage
  coverage_ui.py           # UI cấu hình và so sánh
  scene_finder.py          # Truy tìm ảnh theo metadata
Docs/
  Algorithms_Formulas.md
  Algorithms_Formulas.docx
  Metrics_Thresholds.md
tests/                     # Kiểm thử
.streamlit/config.toml     # Theme settings
Dockerfile
requirements.txt
requirements-dev.txt
```

## Tài liệu

Ba tài liệu gốc được lưu **nguyên byte** trong `Docs/`. Xem `Docs/README.md` để biết phạm vi.

## Kiểm thử

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## Giới hạn

- Ưu tiên CVAT for images, bounding box 2D.
- Không có GT nên chỉ đưa ra cảnh báo cần review.
- ZIP chỉ có XML vẫn có thể thống kê metadata, nhưng không xem được ảnh gốc.
- CSS tùy chỉnh có thể cần cập nhật theo phiên bản Streamlit.
- Chưa tích hợp các module GitHub cũ nguyên trạng; dự án này được **tổ chức theo phong cách repository GitHub đã cung cấp**, nhưng bảo toàn logic phiên bản ZIP mới.
