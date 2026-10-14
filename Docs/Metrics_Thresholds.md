# CVAT Quality Control Dashboard — Tài liệu chỉ số và ngưỡng

**Phiên bản tài liệu:** 1.0 · **Code tham chiếu:** `cvat_quality_dashboard_merged.py` · **Phạm vi:** Image Quality + Label Check A (Geometry) + B (Visual)

> **Nguyên tắc:** Dashboard không có Ground Truth. `REVIEW`, `HIGH`, `POSSIBLE_*` là tín hiệu cần kiểm tra, **không phải** kết luận nhãn sai. `PASS`/`NO_SIGNAL` không chứng minh ảnh hoặc annotation đúng.

## 1. Mục tiêu và luồng xử lý

Dashboard hỗ trợ Leader sàng lọc ảnh và bounding box CVAT để ưu tiên kiểm tra thủ công. Upload **một ZIP** chứa ảnh (`.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`) và tùy chọn `annotations.xml` theo định dạng **CVAT for images**. ZIP chỉ có ảnh chạy Image Quality; Label Check yêu cầu thẻ `<image>` và `<box>` trong XML. Phiên bản này chỉ kiểm tra **2D bounding box**; không xác thực class đúng/sai, missing object, polygon, segmentation, 3D cuboid hoặc tracking.

- **Giới hạn ZIP:** tối đa 50 MiB/ảnh và 1 GiB tổng dung lượng ảnh giải nén theo kiểm tra trong code. File vượt giới hạn bị bỏ qua hoặc ZIP bị từ chối; không phải chỉ số chất lượng ảnh.
- **Matching XML–ảnh:** thử khớp đường dẫn đầy đủ, đường dẫn hậu tố, rồi basename nếu duy nhất. Ảnh không khớp XML vẫn có thể được phân tích Image Quality; box XML thiếu ảnh chỉ chạy A.
- **Cache:** thay ZIP hoặc thay ngưỡng tương ứng sẽ tính lại module; đổi bộ lọc/tab không phải upload lại.

## 2. Cách đọc giao diện theo tab

| Tab | Nội dung chính | Cách diễn giải |
|---|---|---|
| **Tổng quan** | Tổng ảnh, ảnh cần review, CVAT boxes, box cần review, số class; donut trạng thái ảnh, bar số box/class, donut priority | Các số đếm độc lập; một ảnh có thể chứa nhiều box có cảnh báo. |
| **Image Quality** | PASS/REVIEW/ERROR, điểm trung bình, histogram độ nét, scatter brightness–contrast, box plot điểm, biểu đồ tần suất issue, bảng chỉ số ảnh | Chỉ đánh giá các tín hiệu kỹ thuật ảnh, không đánh giá nhãn. |
| **Label Check A+B** | Tổng box, box review, HIGH, số box có ảnh kiểm tra B; histogram area%, scatter edge–foreground contrast, box plot aspect ratio/class, issue chart, thống kê class, bảng box | A dùng tọa độ XML; B dùng pixel trong ảnh và vùng xung quanh box. |
| **Review ảnh** | Ảnh gốc + chỉ số Image Quality hoặc ảnh vẽ box với priority | Màu đỏ HIGH, cam MEDIUM, xanh LOW là mức ưu tiên xem xét, không phải độ chính xác. |
| **Xuất báo cáo** | `image_quality_report.csv`, `label_check_ab_report.csv`, `class_summary.csv` | Báo cáo sàng lọc; giữ cả các chỉ số thô để phân tích lại. |

**Lưu ý về bộ lọc:** tab Label Check có lọc class, priority và chỉ hiện box có cảnh báo. KPI và biểu đồ trong tab này được tính từ **toàn bộ** `label_df`, còn bảng chi tiết dùng tập đã lọc. Vì vậy các số trên KPI có thể không trùng số dòng bảng.

## 3. Image Quality — Chỉ số, công thức, ý nghĩa

Ảnh được đọc bằng OpenCV, chuyển sang grayscale `gray` có giá trị pixel 0–255.

| Chỉ số trong CSV | Cách tính đúng theo code | Ý nghĩa và giới hạn |
|---|---|---|
| `width`, `height` | Kích thước ảnh (pixel) | Kiểm tra độ phân giải tối thiểu; không trực tiếp phản ánh mức chi tiết đối tượng. |
| `size_kb` | Số byte ảnh / 1024 | Dung lượng file, **không** phải điểm chất lượng. |
| `blur_score` | `Var(Laplacian(gray))` | Độ biến thiên đạo hàm bậc hai; thấp thường gợi ý ảnh mờ/ít chi tiết. Ảnh nền trơn cũng có thể thấp; nhiễu có thể làm tăng chỉ số. |
| `brightness` | `Mean(gray)` | Độ sáng trung bình, thang 0–255; không đo riêng vùng quan trọng. |
| `contrast` | `Std(gray)` | Độ phân tán mức xám; thấp nghĩa là biến thiên sáng–tối toàn ảnh thấp, không phải đánh giá ngữ nghĩa. |
| `noise_score` | MAD của residual `gray - GaussianBlur(gray,3×3)` trên pixel có gradient Sobel < 15; nhân hệ số 1.4826 | Ước lượng nhiễu ở vùng tương đối phẳng. Nếu có < 100 pixel phù hợp thì `NaN`, **không** gắn cờ nhiễu. |
| `black_pct` | `100 × Mean(gray < 20)` | % pixel gần đen; chỉ để quan sát, hiện **không** kích hoạt cảnh báo. |
| `white_pct` | `100 × Mean(gray > 245)` | % pixel gần trắng; chỉ để quan sát, hiện **không** kích hoạt cảnh báo. |
| `score` | Bắt đầu 100, trừ điểm theo issue, chặn dưới 0 | **Điểm sàng lọc quy tắc**, không phải điểm chất lượng được kiểm định hay độ chính xác (%). |
| `status` | `ERROR` khi không đọc được ảnh; `REVIEW` khi có ≥1 issue; ngược lại `PASS` | `PASS` chỉ nghĩa là không vượt ngưỡng hiện tại. |

### 3.1 Image Quality thresholds (sidebar)

| Cấu hình | Mặc định | Điều kiện phát cảnh báo | Issue | Lý do sử dụng và cách chọn |
|---|---:|---|---|---|
| **Độ nét tối thiểu** `blur_threshold` | **100.0** | `blur_score < 100` | `BLUR` | Khởi tạo để tìm ảnh thiếu chi tiết. Nên xem phân bố Laplacian của ảnh rõ/mờ thực tế; threshold phụ thuộc độ phân giải, texture, camera và tiền xử lý. |
| **Ngưỡng tối** `dark_threshold` | **40** | `brightness < 40` | `DARK` | Sàng lọc ảnh thiếu sáng tổng thể. Nếu có ảnh đêm hợp lệ, cần phân tích riêng nhóm ban đêm. |
| **Ngưỡng quá sáng** `bright_threshold` | **215** | `brightness > 215` | `OVEREXPOSED` | Tìm ảnh có độ sáng trung bình rất cao. Ảnh sáng ban ngày hoặc nhiều bầu trời có thể bị gắn cờ dù không cháy sáng vùng đối tượng. |
| **Độ tương phản tối thiểu** `contrast_threshold` | **25.0** | `contrast < 25` | `LOW_CONTRAST` | Tìm ảnh grayscale có độ phân tán thấp. Cần hiệu chỉnh theo thời tiết/sương mù/đêm. |
| **Ngưỡng nhiễu MAD** `noise_threshold` | **10.0** | `noise_score > 10` khi đo được | `POSSIBLE_HIGH_NOISE` | Ước lượng nhiễu trên vùng phẳng. Ngưỡng nên lấy từ ảnh sạch và ảnh nhiễu do reviewer chọn. |
| **Chiều rộng tối thiểu** `min_width` | **320 px** | `width < 320` | `LOW_RESOLUTION` | Mốc tối thiểu kỹ thuật, **không** chứng minh vật thể đủ lớn để annotate. |
| **Chiều cao tối thiểu** `min_height` | **240 px** | `height < 240` | `LOW_RESOLUTION` | Chỉ cần một chiều thấp hơn ngưỡng sẽ phát issue. |

Hai hằng số không có slider trong giao diện: `black_threshold=20`, `white_threshold=245`; chỉ dùng tính `black_pct`/`white_pct`. Bộ ước lượng noise dùng `gradient < 15` và tối thiểu 100 pixel vùng phẳng, cũng là hằng số trong code.

### 3.2 Điểm và trạng thái ảnh

- `BLUR`: **−20 điểm**.
- `DARK`, `OVEREXPOSED`, `LOW_CONTRAST`, `LOW_RESOLUTION`, `POSSIBLE_HIGH_NOISE`: mỗi loại **−15 điểm**.
- `score = max(0, 100 − tổng điểm trừ)`.
- `READ_ERROR`: `status=ERROR`, `score=0`; không tính được các metric khác.

**Ví dụ:** một ảnh có `blur_score=72`, `brightness=35`, `contrast=21`, còn các chỉ số khác không kích hoạt cảnh báo: `BLUR + DARK + LOW_CONTRAST`, điểm `100 − 20 − 15 − 15 = 50`, trạng thái `REVIEW`. Các trọng số 20/15 là lựa chọn thủ công của code, **chưa được xác thực thống kê**.

## 4. Label Check A — Geometry

Nguồn dữ liệu là tọa độ `xtl`, `ytl`, `xbr`, `ybr` của từng `<box>` trong `annotations.xml`, cùng kích thước ảnh. `box_width = xbr − xtl`, `box_height = ybr − ytl`.

| Chỉ số / rule | Mặc định | Điều kiện / công thức | Ý nghĩa |
|---|---:|---|---|
| `INVALID_BOX` | Không chỉnh | Tọa độ không hữu hạn hoặc `xbr ≤ xtl` hoặc `ybr ≤ ytl` | Lỗi hình học rõ ràng; được gắn HIGH. |
| `OUT_OF_BOUNDS` | Không chỉnh | `xtl < 0`, `ytl < 0`, `xbr > image_width` hoặc `ybr > image_height` | Box vượt giới hạn ảnh; được gắn HIGH. |
| **Min box area (% ảnh)** `min_area_pct` | **0.01%** | `area_pct < 0.01` → `SMALL_BOX` | `area_pct = 100 × box_width × box_height / (W × H)`. Vật thể xa có thể hợp lệ dù nhỏ. |
| **Max box area (% ảnh)** `max_area_pct` | **80%** | `area_pct > 80` → `LARGE_BOX` | Box rất lớn; người/vật thể gần camera có thể hợp lệ. |
| **Min aspect ratio** `min_aspect` | **0.15** | `aspect_ratio < 0.15` → `ASPECT_RATIO_OUTLIER` | `aspect_ratio = box_width / box_height`. Vật thể cao và hẹp có thể hợp lệ. |
| **Max aspect ratio** `max_aspect` | **7.0** | `aspect_ratio > 7` → `ASPECT_RATIO_OUTLIER` | Vật thể dài và thấp có thể hợp lệ. |
| **Duplicate IoU** `duplicate_iou` | **0.90** | Hai box **cùng class, cùng ảnh** có `IoU ≥ 0.90` → `POSSIBLE_DUPLICATE` cho cả hai | IoU = diện tích giao / diện tích hợp. Có thể là hai đối tượng thực sự chồng lấn; không tự động xóa. |

**Ví dụ diện tích:** ảnh 640×640, box 20×20 → `area_pct = 100×400/409600 ≈ 0.0977%`, lớn hơn min 0.01%, không phát `SMALL_BOX` theo mặc định. Box 4×4 → `≈0.0039%`, bị gắn cờ.

**Ví dụ tỷ lệ:** box 10×100 → aspect 0.10, thấp hơn 0.15 nên `ASPECT_RATIO_OUTLIER`. Với cột đèn hoặc người rất xa, đây có thể là box hợp lệ.

**Quan trọng:** geometry threshold hiện áp dụng **chung cho tất cả class**. `area_pct`, `aspect_ratio` dùng kích thước ảnh thực nếu đọc được, nếu không dùng kích thước từ XML. `POSSIBLE_DUPLICATE` chỉ so box cùng class; không so khác class. Các ngưỡng này chưa phải ngưỡng thống kê theo class.

## 5. Label Check B — Visual (OpenCV)

Chỉ chạy khi tìm được ảnh tương ứng trong ZIP, box có tọa độ hợp lệ và vùng ROI sau clipping đạt ít nhất **8×8 px**. ROI quá nhỏ trả `ROI_TOO_SMALL` và các visual metric là `NaN`; **không** được coi là box trống. Nếu ảnh thiếu, status là `A_ONLY` hoặc `REVIEW_A_ONLY`.

| Chỉ số / threshold | Mặc định | Cách tính trong code | Điều kiện cảnh báo | Giới hạn |
|---|---:|---|---|---|
| **Min edge density** `min_edge` | **0.02** | Canny(ROI grayscale, 50,150), `Mean(edge > 0)` | `< 0.02` → `LOW_EDGE_DENSITY` | Vùng vật thể ít cạnh hoặc mờ cũng có thể hợp lệ. |
| **Min grayscale variance** `min_texture` | **100.0** | `Var(ROI grayscale)` | `< 100` → `LOW_TEXTURE` | Vật thể trơn có variance thấp. Không đo texture bằng mô hình học sâu. |
| **Min Laplacian variance** `min_sharpness` | **50.0** | `Var(Laplacian(ROI grayscale))` | `< 50` → `LOW_SHARPNESS` | Đo độ nét **trong box**, khác `blur_score` của cả ảnh. |
| **Min LAB contrast** `min_contrast` | **12.0** | Khoảng cách Euclid giữa vector màu LAB trung bình **trong box** và **vành ngoài box** | `< 12` → `LOW_FOREGROUND_CONTRAST` nếu đo được | Không phải phân đoạn foreground thật; box có nhiều background làm sai lệch so sánh. |
| **Min boundary edge density** `min_boundary` | **0.02** | `Mean(Canny(ROI) > 0)` trên dải pixel sát **bốn cạnh bên trong box** | `< 0.02` → `WEAK_BOUNDARY_SUPPORT` | Chỉ là tín hiệu gần biên, **không chứng minh box ôm sát đối tượng**. |

**Các hằng số B không có slider:** Canny low/high = **50/150**; ROI nhỏ hơn 8 px ở bất kỳ chiều nào không đánh giá B; vùng ngoài box có `margin = max(4 px, 25% × max(box_width,box_height))` và bị giới hạn trong ảnh; dải viền trong box có bề rộng `min(4, max(1, min(width,height)//8))` pixel. Đây là chi tiết thuật toán hiện tại, không phải ngưỡng đã tối ưu.

### 5.1 `POSSIBLE_EMPTY_BOX` được tạo thế nào?

Chỉ khi **đồng thời** có ba tín hiệu:

1. `LOW_EDGE_DENSITY`;
2. `LOW_TEXTURE`;
3. `LOW_FOREGROUND_CONTRAST`.

Nhãn `POSSIBLE_EMPTY_BOX` được bổ sung và priority đặt HIGH. Điều này **không xác nhận** box trống: một xe tối màu trong bóng râm hoặc đối tượng ít texture có thể tạo ra cả ba tín hiệu.

### 5.2 Phân biệt hai loại blur

- **Image Quality `blur_score`:** đo trên **toàn bộ ảnh**, threshold mặc định **100**.
- **Label B `laplacian_variance`:** đo trên **ROI của một box**, threshold mặc định **50**.

Hai ngưỡng không nên so sánh trực tiếp vì vùng đo khác nhau.

## 6. Logic mức ưu tiên và trạng thái của Label Check

| Trường hợp | `priority` | `status` |
|---|---|---|
| Có `INVALID_BOX`, `OUT_OF_BOUNDS`, `POSSIBLE_DUPLICATE` hoặc `POSSIBLE_EMPTY_BOX` | HIGH | REVIEW; nếu không có ảnh là REVIEW_A_ONLY |
| Có cảnh báo geometry khác, hoặc cảnh báo visual khác `LOW_SHARPNESS`/`ROI_TOO_SMALL` | MEDIUM | REVIEW; nếu thiếu ảnh là REVIEW_A_ONLY |
| Chỉ có `LOW_SHARPNESS` | LOW | REVIEW |
| Chỉ có `ROI_TOO_SMALL`, hoặc không có issue | LOW | NO_SIGNAL; nếu thiếu ảnh là A_ONLY |

**Lưu ý về code hiện tại:** `priority=LOW` được dùng cả cho box không có vấn đề, vì vậy **donut Priority không phải biểu đồ phân bố mức độ lỗi**. Để đếm box cần review phải kết hợp `status.startswith('REVIEW')`. `ROI_TOO_SMALL` được ghi trong `issues`/`issue_count`, nhưng không làm status chuyển REVIEW khi đứng một mình. Nếu một box thiếu ảnh, `image_available=False` và B không chạy; không nên coi là B đã pass.

## 7. Các cột báo cáo và chỉ số tổng hợp

### 7.1 Image Quality CSV

`filename`, `status`, `score`, `issues`, `width`, `height`, `size_kb`, `blur_score`, `brightness`, `contrast`, `noise_score`, `black_pct`, `white_pct`, `error`.

### 7.2 Label Check A+B CSV

- **Định danh:** `image_id`, `image_name`, `box_id`, `label`, `occluded`.
- **Tọa độ:** `xtl`, `ytl`, `xbr`, `ybr`.
- **Trạng thái ảnh:** `image_available`, `image_error`.
- **Geometry:** `area_pct`, `aspect_ratio`, `geometry_issues`.
- **Visual:** `edge_density`, `texture_variance`, `laplacian_variance`, `foreground_contrast`, `boundary_support`, `visual_issues`.
- **Kết quả:** `issues`, `issue_count`, `priority`, `status`.

`occluded` hiện **được đọc từ XML nhưng chưa dùng để điều chỉnh threshold**. `issue_count` là số cờ, không phải số lỗi đã xác nhận; các cờ visual có tương quan với nhau.

### 7.3 KPI / thống kê class

- **Tổng ảnh:** số file ảnh đã đọc vào pipeline Image Quality; không nhất thiết bằng số thẻ `<image>` trong XML.
- **Ảnh cần review:** số ảnh có `status=REVIEW` ở Image Quality.
- **CVAT boxes:** số box đọc từ XML khi có dữ liệu label.
- **Box cần review:** số dòng Label Check có status bắt đầu bằng `REVIEW` (bao gồm `REVIEW_A_ONLY`).
- **Số class:** số class khác nhau xuất hiện trong các box XML; không phải tổng class được định nghĩa nhưng chưa gán.
- **Box có ảnh kiểm tra B:** số box có `image_available=True`; một số trong đó vẫn có thể `ROI_TOO_SMALL` hoặc `INVALID_BOX`, nghĩa là **B chưa chắc đã tính metric thành công**.
- **`review_rate_pct` theo class:** `100 × review_boxes / total_boxes`; đây là **tỷ lệ box bị rule gắn cờ**, không phải tỷ lệ annotation sai.
- **Điểm Image Quality trung bình:** trung bình `score` trên toàn bộ ảnh, bao gồm `ERROR=0`; nên đọc kèm số ERROR.

### 7.4 Cách đọc các biểu đồ

| Biểu đồ | Mục đích | Lưu ý |
|---|---|---|
| Donut trạng thái ảnh | Tỷ trọng PASS/REVIEW/ERROR | Phụ thuộc ngưỡng đang chọn. |
| Donut priority box | Tỷ trọng HIGH/MEDIUM/LOW | LOW bao gồm cả box không có cảnh báo. |
| Bar số box theo class | Phát hiện class nhiều/ít box | Không tự kết luận class imbalance là lỗi annotation. |
| Histogram blur | Xem phân bố `blur_score`, xác định đuôi thấp | Có thể lệch mạnh theo cảnh/độ phân giải. |
| Scatter brightness–contrast | Tìm cụm ảnh tối/ít tương phản | Màu điểm theo trạng thái Image Quality. |
| Box plot điểm ảnh | Trung vị, độ phân tán, outlier score | Score rời rạc do rule-based, không phải thang đo liên tục khách quan. |
| Histogram area% | Nhận diện nhiều box rất nhỏ/rất lớn | Nên tách class để tránh pha trộn phân bố. |
| Scatter edge–LAB contrast | Tìm box ít cạnh và ít khác nền | Cần đối chiếu ảnh; không thể xác nhận box trống. |
| Box plot aspect ratio/class | So sánh phân bố tỷ lệ box giữa class | Class có hình dạng khác nhau là bình thường. |
| Bar issue frequency | Biết rule nào kích hoạt nhiều | Một box/ảnh có thể có nhiều issue; tổng các cột không bằng tổng đối tượng review. |

## 8. Cách chọn và hiệu chỉnh thresholds — Quy trình khuyến nghị

> **Phần này là khuyến nghị triển khai**, không phải quy trình hiệu chỉnh đã được thực hiện hoặc chứng minh bởi source code hiện tại.

**Bước 1 — Giữ baseline:** chạy ZIP mẫu với toàn bộ mặc định. Lưu file CSV và ghi lại số ảnh/box bị gắn cờ theo từng issue. Đừng thay nhiều ngưỡng cùng lúc.

**Bước 2 — Lấy mẫu review có phân tầng:** chọn ảnh/box ở cả nhóm được gắn cờ và không gắn cờ, theo class, kích thước box, ngày/đêm, che khuất, mờ/không mờ. Nếu có thể, Leader đánh dấu `valid issue`, `false alarm`, `uncertain` cho từng cảnh báo. Không cần full Ground Truth để hiệu chỉnh tỷ lệ cảnh báo hữu ích.

**Bước 3 — Vẽ phân bố từng metric:** histogram và percentiles (P1, P5, P50, P95, P99) cho từng nhóm. Xem ví dụ ảnh ở gần threshold; tránh lấy một percentile tùy ý làm chuẩn tuyệt đối.

**Bước 4 — Chọn theo chi phí review:** nếu mục tiêu là sàng lọc nhanh, ưu tiên precision của review queue (ít false alarm). Nếu mục tiêu là không bỏ sót ảnh nghi ngờ, chấp nhận nhiều false alarm hơn. Có thể đo `review_yield = số cảnh báo được reviewer xác nhận / số cảnh báo được reviewer kiểm tra` trên mẫu được review, không gọi đó là accuracy toàn bộ dataset.

**Bước 5 — Hiệu chỉnh có điều kiện:**

- `min_area_pct` / `max_area_pct` / aspect: nên theo **class** và có thể theo kích thước/độ xa; ví dụ pedestrian thường hẹp hơn bus.
- Blur/noise/brightness: nên theo **độ phân giải, camera, điều kiện ngày/đêm, thời tiết**.
- Edge/texture/LAB contrast/boundary: nên theo **class, diện tích ROI, occlusion**; đối tượng nhỏ, mờ hoặc che khuất dễ bị gắn cờ nhầm.
- `duplicate_iou`: nên bắt đầu với ngưỡng cao để tránh cảnh báo trùng quá nhiều; kiểm tra các cặp cùng class gần nhau trước khi thay.

**Bước 6 — Kiểm thử lại:** giữ riêng một tập ảnh/box chưa dùng để chỉnh ngưỡng; so sánh baseline → phiên bản hiệu chỉnh theo số cảnh báo, tỷ lệ review hữu ích, thời gian review và các false alarm điển hình. Ghi version của cấu hình cùng báo cáo.

### 8.1 Bảng thực hành chọn ngưỡng

| Ngưỡng | Khi muốn giảm false alarm | Khi muốn nhạy hơn | Cần kiểm tra trực quan |
|---|---|---|---|
| Blur min | **Giảm** threshold | **Tăng** threshold | Ảnh mờ thật hay vùng nền trơn? |
| Dark min | Giảm | Tăng | Ảnh đêm hợp lệ? |
| Bright max | Tăng | Giảm | Vùng đối tượng có cháy sáng? |
| Contrast min | Giảm | Tăng | Sương mù/đêm có được chấp nhận? |
| Noise max | Tăng | Giảm | Nhiễu hay chi tiết ảnh? |
| Min area% | Giảm | Tăng | Đối tượng xa/nhỏ có hợp lệ? |
| Max area% | Tăng | Giảm | Đối tượng gần camera? |
| Min aspect | Giảm | Tăng | Class cao/hẹp? |
| Max aspect | Tăng | Giảm | Class dài/thấp? |
| Duplicate IoU | Tăng | Giảm | Hai đối tượng thật chồng lấn? |
| Edge/texture/sharpness/LAB/boundary min | Giảm | Tăng | ROI trơn, mờ, nhỏ, che khuất? |

**Cảnh báo:** thay đổi threshold làm thay đổi cả số lượng issue, priority, trạng thái và score. Không so sánh số cảnh báo giữa hai phiên bản cấu hình như thể đó là thay đổi chất lượng annotator.

## 9. Ví dụ minh họa

**Ví dụ A — ảnh 640×640:** ảnh có brightness 34, contrast 19, blur 80, noise 6, kích thước đạt chuẩn. Với default: `DARK`, `LOW_CONTRAST`, `BLUR` → `REVIEW`, score 50/100. Đây chỉ là cảnh báo ảnh tối/ít tương phản/mờ theo metric.

**Ví dụ B — box pedestrian 4×20 trên ảnh 640×640:** area `100×80/409600≈0.0195%` nên không `SMALL_BOX` với min 0.01%; aspect `4/20=0.20` nên không `ASPECT_RATIO_OUTLIER` với min 0.15. Nếu đối tượng chỉ 2×20, area ≈0.0098% và aspect 0.10 → cả hai issue. Không có nghĩa box nhỏ đó sai.

**Ví dụ C — box trùng:** hai box cùng class trên cùng ảnh có IoU 0.94, vượt 0.90 → cả hai `POSSIBLE_DUPLICATE`, HIGH. Reviewer cần kiểm tra có hai đối tượng chồng nhau hay gán nhãn lặp.

**Ví dụ D — box visual:** edge density 0.01, texture variance 60, LAB contrast 8; thấp hơn lần lượt 0.02, 100, 12 → thêm `POSSIBLE_EMPTY_BOX` và HIGH. Chỉ nên dùng làm tín hiệu review, không tự xóa box.

## 10. Giới hạn và hướng phát triển

1. **Không có GT:** không đo precision/recall/F1 của nhãn so với chuẩn, không xác định nhãn class đúng hay missing object.
2. **Visual heuristic không hiểu đối tượng:** edge/texture/contrast có thể đánh dấu nhầm vật thể hợp lệ; boundary support chưa đo được tightness thực sự.
3. **Threshold toàn cục:** chưa theo class, box size, occlusion, time of day hay weather.
4. **Tín hiệu tương quan:** nhiều visual issue có thể cùng xuất phát từ một nguyên nhân (ví dụ ảnh mờ); không nên cộng số issue như số lỗi độc lập.
5. **Khả năng mở rộng:** duplicate check duyệt từng cặp box trong ảnh, chi phí tăng bậc hai theo số box/ảnh; phân tích visual chuyển grayscale/LAB lặp lại theo box nên có thể chậm.
6. **Mức ưu tiên hiện tại:** `LOW` không đồng nghĩa có lỗi; nên bổ sung trạng thái `NONE/NOT_EVALUATED` tách khỏi priority khi nâng cấp.
7. **Nguồn file:** dashboard hiện yêu cầu ZIP có **ít nhất một ảnh hợp lệ**; không chạy Label A với ZIP chỉ có XML mặc dù hàm `audit` hỗ trợ logic A-only khi thiếu một số ảnh.
8. **Ảnh lỗi:** điểm trung bình Image Quality tính cả `ERROR=0`, có thể kéo trung bình xuống.

## 11. Checklist dành cho Leader trước khi sử dụng

- [ ] ZIP chứa đúng ảnh và `annotations.xml` tương ứng, không nhầm tên ảnh trùng ở thư mục khác.
- [ ] Kiểm tra số ảnh ZIP so với số ảnh XML; kiểm tra tỷ lệ box có `image_available=True`.
- [ ] Xác nhận class, độ phân giải và điều kiện ảnh phù hợp với threshold.
- [ ] Xem một số ví dụ cảnh báo HIGH và các box không có cảnh báo.
- [ ] Lưu cấu hình threshold khi xuất CSV để báo cáo có thể tái lập.
- [ ] Khi báo cáo, dùng từ **“cảnh báo / tín hiệu cần review”**, không dùng **“lỗi nhãn được xác nhận”** nếu chưa có người review.

---

**Nguồn:** tài liệu được đối chiếu với các hàm `analyze_image`, `estimate_noise`, `visual_metrics`, `audit`, `get_cfg_image`, `get_cfg_label` và phần hiển thị 5 tab của `cvat_quality_dashboard_merged.py`. Các khuyến nghị hiệu chỉnh trong Mục 8 là đề xuất phương pháp, không phải kết quả thực nghiệm trên dataset.
