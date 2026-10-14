# METRIC CATALOG — N2-05B CVAT Quality Dashboard

**Phạm vi:** CVAT for images, 2D bounding box; thống kê phân bố và kiểm tra tín hiệu chất lượng **không dùng Ground Truth**.  
**Mã tham chiếu:** `app.py`, `core/distribution.py`, `core/coverage_dynamic.py`, `core/coverage_ui.py`, `core/scene_finder.py`.  
**Quy ước:** `N` là số bản ghi `<image>` trong XML; `M` là số box; `M_valid` là số box có `valid_geometry=True` theo module tương ứng. Các tỷ lệ phải ghi rõ mẫu số. Ngưỡng là cấu hình thử nghiệm, không phải chuẩn phổ quát.

## 1. Nhóm Inventory & Class Distribution

| ID | Metric / trường | Công thức hoặc cách tính | Đơn vị, mẫu số | Diễn giải và lưu ý |
|---|---|---|---|---|
| INV01 | `total_images` | Số bản ghi `<image>` | ảnh | Khác số file ảnh giải mã thành công nếu ZIP không đủ ảnh. |
| INV02 | `total_boxes` | Đếm `<box>` | box | Bao gồm box không hợp lệ nếu lấy từ `dist_boxes`. |
| INV03 | `class_count` | Số class khác nhau trong box | class | Không chứng minh có đủ class yêu cầu khi class vắng hoàn toàn. |
| DP01 | `boxes` theo class | Đếm box mang nhãn `c` | box | Trong `core/distribution.py`, bảng class đếm mọi box đã parse. |
| DP02 | `images` theo class | Số `image_name` phân biệt chứa `c` | ảnh | Module distribution dùng `image_name`; Coverage dùng `image_id` trên box hợp lệ. |
| DP03 | `share_pct` | `100 × boxes(c) / M` | % box | Tổng qua các class ~100% khi có box. |
| DP04 | `image_coverage_pct` | `100 × distinct image_id chứa c / N` | % ảnh | Coverage tab chỉ đếm **box hợp lệ**; các class có thể cùng xuất hiện trong một ảnh nên tổng % có thể >100%. |
| DP05 | `object_share_pct` | `100 × valid boxes(c) / M_valid` | % box hợp lệ | Chỉ số ở Coverage tab, không đồng nhất với `share_pct` nếu có box sai hình học. |
| DP06 | `area_pct` | `100 × (xbr−xtl) × (ybr−ytl) / (W×H)` | % diện tích ảnh | Chỉ có nghĩa với W,H>0 và box hình học hợp lệ. |
| DP07 | `size_group` | `<0.1%`, `0.1–1%`, `>1%` | nhóm | Phân nhóm minh họa trong tab Distribution; không phải tiêu chuẩn sai nhãn. |
| DP08 | `occluded` theo class | Đếm theo `(label, occluded)` | box | Thuộc tính do annotator khai báo, không phải kết quả model tự nhận diện. |
| DP09 | `weather` | `value_counts` trên ảnh XML | ảnh | Giá trị lấy từ tag CVAT; `unknown` khác `missing`. |
| DP10 | `timeofday` | `value_counts` trên ảnh XML | ảnh | Phụ thuộc chất lượng metadata được gán. |
| DP11 | `weather × timeofday` | `groupby(weather, timeofday).size()` | ảnh | Hữu ích để tìm nhóm ảnh thiếu thông tin. |
| DP12 | Custom attributes | Đếm `(attribute,value,class)` | box | Phát hiện tên attribute động từ `<box><attribute>`. |

### Cảnh báo lệch phân bố class

Trong `core/distribution.py`, một class được đưa vào bảng cảnh báo khi **ít nhất một** điều kiện đúng: `boxes < min_count`, `share_pct < min_share`, `share_pct > max_share`. Mặc định trong giao diện: **30 box**, **1%**, **60%**. Đây là cảnh báo phân bố quan sát, **không** phải kiểm tra nhãn đúng/sai và cũng **không** phải target coverage.

## 2. Image Quality (IQ)

| ID | Chỉ số | Cách tính | Ngưỡng mặc định / tín hiệu | Giới hạn |
|---|---|---|---|---|
| IQ01 | `width`, `height` | Kích thước ảnh sau decode | width<320 hoặc height<240 → `LOW_RESOLUTION` | Không đo độ rõ của vật thể. |
| IQ02 | `size_kb` | Byte ảnh nén / 1024 | Không tự gắn cờ | Là dung lượng nén, không phải kích thước raster. |
| IQ03 | `blur_score` | `Var(Laplacian(gray))` | `<100` → `BLUR` | Nhiễu có thể tăng điểm, vùng trơn có thể giảm điểm. |
| IQ04 | `brightness` | `Mean(gray)` | `<40` → `DARK`; `>215` → `OVEREXPOSED` | Ảnh đêm hợp lệ có thể bị cảnh báo. |
| IQ05 | `contrast` | `Std(gray)` | `<25` → `LOW_CONTRAST` | Không phản ánh riêng foreground. |
| IQ06 | `noise_score` | `1.4826 × MAD(gray − GaussianBlur(gray,3×3))` trên pixel Sobel magnitude<15 | `>10` → `POSSIBLE_HIGH_NOISE`; <100 pixel phẳng → NaN | Proxy nhạy với JPEG/sharpening/texture. |
| IQ07 | `black_pct` | `100 × mean(gray<20)` | Không trực tiếp kích hoạt cờ | Tỷ lệ gần đen. |
| IQ08 | `white_pct` | `100 × mean(gray>245)` | Không trực tiếp kích hoạt cờ | Tỷ lệ gần trắng. |
| IQ09 | `score` | `max(0,100−Σpenalty)` | `BLUR`: −20; các issue còn lại: −15 | Điểm quy tắc thủ công, **không** phải xác suất hoặc accuracy. |
| IQ10 | `status` | `ERROR` nếu không đọc được; `REVIEW` nếu có issue; còn lại `PASS` | Theo các rule đang bật | `PASS` không chứng minh ảnh tốt. |

**Biểu đồ:** histogram `blur_score` để quan sát độ nét; scatter `brightness × contrast` để tìm cụm ảnh tối/mờ; phân bố `score` để xem mức sàng lọc; bar tần suất issue để ưu tiên kiểm tra. Các biểu đồ phụ thuộc ngưỡng và đặc điểm camera.

## 3. Label Check A — Geometry

| ID | Chỉ số / flag | Điều kiện | Ý nghĩa |
|---|---|---|---|
| LA01 | `INVALID_BOX` | Tọa độ không hữu hạn hoặc `xbr≤xtl` hoặc `ybr≤ytl` | Hình học không hợp lệ; ưu tiên cao. |
| LA02 | `OUT_OF_BOUNDS` | Box vượt kích thước ảnh | Box nằm ngoài ảnh; ưu tiên cao. |
| LA03 | `area_pct` | `100 × area(box)/(W×H)` | Kích thước tương đối. |
| LA04 | `SMALL_BOX` | `area_pct < 0.01%` (mặc định) | Có thể là vật thể xa hợp lệ. |
| LA05 | `LARGE_BOX` | `area_pct > 80%` (mặc định) | Có thể là vật thể rất gần. |
| LA06 | `aspect_ratio` | `(xbr−xtl)/(ybr−ytl)` | Hình dạng box. |
| LA07 | `ASPECT_RATIO_OUTLIER` | ratio<0.15 hoặc >7 (mặc định) | Nên hiệu chỉnh theo class. |
| LA08 | `POSSIBLE_DUPLICATE` | Box cùng class/cùng ảnh có IoU≥0.90 | Cảnh báo trùng lặp tiềm năng; không tự xóa. |

`IoU(A,B)=Area(A∩B)/Area(A∪B)` khi hợp hợp lệ. Mỗi issue là **review signal**; `POSSIBLE_DUPLICATE` không đồng nghĩa chắc chắn gán hai lần.

## 4. Label Check B — Pixel/Visual

Các tín hiệu được đo từ crop của box và vùng lân cận, gồm **edge density** (Canny), **texture variance**, **Laplacian variance**, **foreground contrast** (chênh LAB giữa vùng trong box và vòng ngoài) và **boundary support**. Cảnh báo `POSSIBLE_EMPTY_BOX` dựa trên tổ hợp nhiều tín hiệu yếu; không có GT nên không thể chứng minh box chứa sai class hay thiếu đối tượng. Biểu đồ phân bố `area_pct`, `aspect_ratio` theo class và `edge density × foreground contrast` giúp chọn box cần review. Xem công thức và ngưỡng chi tiết trong `Algorithms_Formulas.md` và `Metrics_Thresholds.md` (tài liệu gốc).

## 5. Coverage theo class & slice (dynamic)

**Nguồn tính:** `core/coverage_dynamic.py` chỉ lấy box có `valid_geometry=True`, ghép metadata ảnh qua `image_id`. Các chiều hỗ trợ: `class`, `weather`, `timeofday`, `occluded`. Giá trị class/weather/time được đọc từ dữ liệu; target do Leader nhập. **Không cố định danh sách class/target.**

| ID | Cột kết quả | Định nghĩa | Ví dụ | Lưu ý |
|---|---|---|---|---|
| CV01 | `slice` | Tên tổ hợp điều kiện | `class=bus × weather=rain` | Các điều kiện kết hợp bằng AND. |
| CV02 | `unit` | `images` hoặc `objects` | `images` | Không so sánh số lượng giữa hai đơn vị khác nhau. |
| CV03 | `support` | Số `image_id` duy nhất hoặc số box hợp lệ khớp điều kiện | 35 | Observed, không phải GT. |
| CV04 | `target` | Mục tiêu **số lượng tuyệt đối**, số nguyên >0 | 100 | Không hỗ trợ nhập target % trực tiếp. |
| CV05 | `gap` | `max(0,target−support)` | 65 | Slice có thể giao nhau; **không cộng gap** để suy ra số ảnh cần thu thập. |
| CV06 | `attainment_pct` | `100×support/target` | 35% | Có thể >100% khi vượt mục tiêu. |
| CV07 | `weight` | Trọng số dương do Leader đặt | 2 | Dùng xếp ưu tiên. |
| CV08 | `weighted_gap` | `(gap/target)×weight` | 1.30 | Không phải số ảnh thiếu. |
| CV09 | `status` | `Đạt` khi gap=0, còn lại `Thiếu` | `Thiếu` | Chỉ nói về target số lượng. |
| CV10 | `metadata_unresolved` | Tổng lượt ảnh có missing/unknown của từng chiều weather/time yêu cầu giá trị xác định | 162 | Một ảnh có thể được đếm nhiều lần; không phải số ảnh duy nhất. |
| CV11 | `confidence` | `Tạm thời` nếu unresolved>0, còn lại `Quan sát` | `Tạm thời` | **Không** phải xác suất tin cậy. |

**Weighted coverage:** `100×Σweight(slice có gap=0)/Σweight(tất cả slice)`; đây là tỷ lệ trọng số slice đạt, **không** phải tỷ lệ ảnh đã đạt. `recommendations()` chọn các slice có gap>0, sắp theo `weighted_gap` rồi `gap`; nếu metadata chưa rõ, khuyên rà soát metadata trước khi kết luận thiếu.

**Cấu hình slice:** thêm thủ công; sinh từ tổ hợp quan sát; hoặc tích Descartes từ các giá trị phát hiện (giới hạn 250); nhập JSON và sửa qua `st.data_editor`. JSON mẫu:

```json
[
  {"name":"bus-night-rain","filters":{"class":"bus","timeofday":"night","weather":"rain"},"unit":"images","target":100,"weight":2}
]
```

**Lưu ý:** Nếu class chưa từng xuất hiện, sinh slice tự động từ dữ liệu không thể biết class kỳ vọng đó. Cần khai báo mục tiêu bên ngoài hoặc cải tiến UI.

## 6. Scene Finder — tìm ảnh theo weather × timeofday

| Thành phần | Chức năng | Cách đọc |
|---|---|---|
| Weather filter | Lọc nhiều giá trị | `unknown` là giá trị đã gán nhưng chưa xác định; `missing` là không có dữ liệu. |
| Time of day filter | Lọc nhiều giá trị | Hai nhóm điều kiện kết hợp AND. |
| Keyword | Tìm chuỗi trong tên/đường dẫn ảnh | Không phải tìm ảnh bằng nội dung hình ảnh. |
| Matched images | Số bản ghi ảnh thỏa điều kiện | Dựa vào metadata XML. |
| Metadata unclear | Số ảnh có weather **hoặc** timeofday là unknown/missing | Không phải số nhãn chắc chắn sai. |
| Preview | Hiển thị ảnh gốc nếu ZIP chứa ảnh | Nếu ZIP chỉ XML vẫn có danh sách và CSV. |
| CSV export | `image_id,image_name,weather,timeofday` | Phục vụ review và sửa lại trong CVAT. |

## 7. Hướng dẫn đặt ngưỡng và đọc kết quả

1. Xác định **đơn vị và mẫu số** trước khi so sánh hai biểu đồ.
2. Chia dataset theo điều kiện camera/thời tiết nếu phân bố ảnh khác biệt lớn; đừng áp một ngưỡng blur cho mọi nguồn.
3. Chọn một tập mẫu được reviewer kiểm tra thủ công để đánh giá false positives/false negatives của rule.
4. Target coverage nên đến từ yêu cầu dữ liệu/mentor, không tự suy ra từ tỷ lệ class hiện có.
5. Phân biệt **Observed Imbalance** (lệch phân bố) với **Below Target** (không đạt mục tiêu) và **Label Review Signal** (nghi vấn chất lượng nhãn).
6. Báo cáo thiếu dữ liệu phải ghi rõ metadata missing/unknown, không tuyên bố ảnh sai khi chưa review.

## 8. Hạn chế và tính tái lập

- Chỉ hỗ trợ box 2D cho kiểm tra A/B; không đánh giá semantic class đúng/sai hoặc missing objects không có GT/model đối chiếu.
- `parse_distribution()` dùng `image_id` từ XML, không có khóa ghép dataset; bản hiện tại xử lý một ZIP mỗi phiên. Muốn nhiều ZIP/annotator phải thêm `dataset_id` và kiểm tra trùng ID.
- Parser `distribution.py` có tiêu chí `valid_geometry` tối giản (`x2>x1`, `y2>y1`, W,H>0); không tự loại out-of-bounds khỏi Coverage. Vì vậy cần chuẩn hóa với Label Check A trước khi coi tất cả box coverage là hợp lệ hoàn toàn.
- Các kết quả kiểm thử pilot, thời gian tiết kiệm và độ chính xác review **chưa có số đo được cung cấp**.
