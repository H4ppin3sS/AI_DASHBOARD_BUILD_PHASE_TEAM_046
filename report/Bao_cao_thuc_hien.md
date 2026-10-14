# BÁO CÁO THỰC HIỆN — N2-05B CVAT QUALITY DASHBOARD

**Tên đề tài:** Dashboard phân bố class và thuộc tính dữ liệu CVAT, hỗ trợ Leader thống kê và kiểm tra chất lượng annotation.  
**Thời điểm tổng hợp:** 14/10/2026.  
**Nguồn xác nhận:** mã nguồn `CVAT_Quality_Dashboard_GitHub_Ready`, `Docs/Algorithms_Formulas.md`, `Docs/Metrics_Thresholds.md`.  
**Phương pháp đánh giá:** rà soát chức năng trong mã nguồn; **không tự suy ra** số liệu thực nghiệm, thời gian tiết kiệm hoặc accuracy khi chưa có log/fixture được cung cấp.

## 1. Tóm tắt

Dự án đã xây dựng ứng dụng Streamlit để nhận ZIP CVAT, thống kê class/thuộc tính, phân tích chất lượng ảnh, kiểm tra hình học và tín hiệu pixel của bounding box, so sánh coverage theo mục tiêu cấu hình động và truy tìm ảnh theo thời tiết × thời điểm. Dashboard phục vụ **review không có Ground Truth**, do đó không được gọi các cảnh báo là lỗi đã xác nhận.

## 2. Các chức năng đã có trong mã nguồn

| Module | Chức năng được xác nhận qua code | Trạng thái bằng chứng |
|---|---|---|
| Upload/parse | Nhận ZIP, đọc ảnh, tìm `annotations.xml`, phân tích ảnh/box | Đã lập trình; chưa có benchmark ZIP lớn |
| Overview | KPI ảnh/box/class, trạng thái review | Đã lập trình |
| Distribution | Class count/share, box area, occlusion, weather, timeofday, attributes | Đã lập trình |
| Image Quality | Blur, brightness, contrast, noise, black/white, score và issue | Đã lập trình |
| Label Check A | Invalid/out-of-bounds, area, aspect, duplicate IoU | Đã lập trình |
| Label Check B | Edge/texture/foreground/boundary signals | Đã lập trình |
| Scene Finder | Lọc AND weather/timeofday, unknown/missing, keyword, preview, CSV | Đã lập trình |
| Coverage & Slice | Slice động, support, target, gap, attainment, weight, recommendations | Đã lập trình |
| Reports | CSV/JSON export | Đã lập trình |
| Modern UI | CSS/theme và 7 tab Streamlit | Đã lập trình; chưa có đánh giá UX định lượng |

## 3. Kết quả thực hiện theo nhóm nhiệm vụ

### 3.1. Phân bố class và thuộc tính

Code phát hiện tên class/attribute từ XML; hiển thị số box và số ảnh chứa class, tỷ lệ box, cảnh báo lệch tỷ lệ theo ngưỡng Leader đặt. Phân bố kích thước box, occlusion, weather và timeofday được thể hiện bằng bảng/biểu đồ. Đây là kết quả về **khả năng tính toán**, chưa phải báo cáo thống kê một dataset cụ thể.

### 3.2. Image Quality

Đã có pipeline tính các chỉ số kỹ thuật ảnh và cờ `BLUR`, `DARK`, `OVEREXPOSED`, `LOW_CONTRAST`, `LOW_RESOLUTION`, `POSSIBLE_HIGH_NOISE`. Dashboard cho chỉnh ngưỡng và xem histogram/scatter/issue frequency. `score` là điểm quy tắc, chưa được hiệu chuẩn bằng tập ảnh có đánh giá chất lượng chuẩn.

### 3.3. Label Check A+B

Đã có kiểm tra tọa độ/diện tích/aspect/IoU và các tín hiệu ảnh trong box; hiển thị mức ưu tiên review. Chưa có GT hoặc reviewer labels để đo precision/recall của các cảnh báo. Không tuyên bố hệ thống phát hiện chính xác bao nhiêu lỗi thật.

### 3.4. Coverage động

Đã hỗ trợ bốn chiều `class`, `weather`, `timeofday`, `occluded`, hai đơn vị `images` và `objects`, target và weight do Leader đặt. Có tạo slice thủ công, tự động, nhập JSON, chỉnh sửa target, bảng observed vs target, gap và recommendations. Hệ thống không cố định class/target như một bộ dữ liệu duy nhất.

### 3.5. Scene Finder

Đã bổ sung bộ lọc thời tiết × thời điểm, hỗ trợ `unknown` và `missing`, tìm theo tên ảnh, preview nếu ZIP có ảnh và export CSV. Ví dụ Leader có thể tìm ảnh có cả hai giá trị `weather=unknown` và `timeofday=unknown` để review, nhưng chưa có tính năng sửa metadata trực tiếp trong CVAT.

## 4. Kết quả kiểm thử và bằng chứng

**Đã có:** các file `tests/test_coverage_dynamic.py`, `tests/test_scene_finder.py` và cấu hình GitHub Actions. **Chưa được xác nhận trong báo cáo này:** một lần chạy pytest toàn bộ thành công trên môi trường triển khai, kiểm thử end-to-end bằng ZIP CVAT thật, kết quả đối chiếu thủ công và các phép đo baseline/pilot. Không điền số lượng lỗi hay thời gian tiết kiệm khi thiếu biên bản đo.

| Test / kiểm chứng | Tình trạng | Việc cần làm |
|---|---|---|
| Biên dịch Python | Đã có thông tin kiểm tra ở lần đóng gói trước | Chạy lại trên commit cuối |
| Unit test Coverage | Có file test | Chạy pytest và lưu log |
| Unit test Scene Finder | Có file test | Bảo đảm dependencies trong môi trường CI |
| ZIP CVAT có XML+ảnh | Chưa có log nghiệm thu đính kèm | Chạy với dataset mẫu và chụp màn hình |
| ZIP thiếu ảnh/metadata | Chưa có log nghiệm thu đính kèm | Kiểm tra thông báo và CSV |
| Baseline thủ công vs dashboard | Chưa đo | Dùng cùng 5–10 câu hỏi thống kê |
| Review flags TP/FP | Chưa đo | Reviewer kiểm tra mẫu ảnh/box |

## 5. Những vấn đề kỹ thuật đã nhận diện

1. `core/distribution.py` dùng tiêu chí valid geometry tối giản; cần thống nhất với Label Check A về out-of-bounds và non-finite coordinates.
2. Coverage và Distribution dùng tập box/mẫu số khác nhau, cần ghi rõ để tránh hiểu sai KPI.
3. `metadata_unresolved` có thể đếm một ảnh nhiều lần nếu thiếu nhiều chiều metadata; nên đổi thành số ảnh duy nhất và chi tiết theo field.
4. `confidence` là `Quan sát/Tạm thời`, không phải xác suất thống kê.
5. Một ZIP mỗi lần upload; chưa có provenance/multi-ZIP cho nhiều annotator.
6. Target chỉ là số lượng tuyệt đối; class hoàn toàn vắng mặt không tự được sinh từ XML.
7. Parser XML hiện dùng ElementTree tiêu chuẩn; cần hardening trước khi triển khai công khai.
8. CSS tùy chỉnh có thể phụ thuộc phiên bản Streamlit; cần test trình duyệt.

## 6. Đánh giá mức đáp ứng đề bài

| Yêu cầu đề bài | Đáp ứng trong mã nguồn | Nhận xét |
|---|---|---|
| Phân bố class | Có | Có số box, tỷ lệ và số ảnh chứa class |
| Kích thước box | Có | Có area%, nhóm kích thước, Label Check A |
| Độ che khuất | Có | Thống kê từ trường occluded của CVAT |
| Thời tiết và thời điểm | Có | Từ scene tags; phân biệt missing/unknown |
| Cảnh báo class lệch tỷ lệ | Có | Ngưỡng cấu hình; không coi lệch là lỗi |
| Chất lượng ảnh | Có | Các phép đo pixel OpenCV |
| Chất lượng label | Có, ở mức tín hiệu | Không GT; cần reviewer xác nhận |
| Coverage & target | Có | Target động, gap, attainment, weight |
| Đề xuất bổ sung slice | Có, rule-based | Dựa vào gap và metadata |
| Tìm ảnh cần review theo scene | Có | Lọc AND và preview/CSV |
| Baseline → pilot | Chưa có kết quả định lượng | Cần đo trên dữ liệu thực tế |

## 7. Đề xuất nghiệm thu và đo hiệu quả

Chọn một ZIP CVAT có metadata, lập bộ 10 câu hỏi cố định: tổng ảnh, tổng box, top class, class ít nhất, tỷ lệ ảnh có car, phân bố occlusion, số ảnh rain/night, số ảnh unknown/unknown, số box có issue và số slice chưa đạt target. Hai người thực hiện độc lập: thủ công và dashboard. Ghi thời gian, độ đúng đáp án và số bước thao tác. Chọn mẫu cảnh báo Image/Label để reviewer đánh dấu `true_issue`/`false_alarm` nhằm tính precision thực nghiệm. Đây là **đề xuất quy trình**, không phải số liệu đã thu được.

## 8. Kế hoạch cải thiện tiếp theo

**Ưu tiên cao:** thống nhất schema/ID và rule valid geometry; test ZIP thật; kiểm tra missing/unknown; đo baseline/pilot; sửa CI nếu cần.  
**Ưu tiên trung bình:** target theo %, Review Queue có trạng thái xác nhận, import nhiều ZIP có dataset_id, lọc sâu theo class×weather×timeofday×occluded.  
**Dài hạn:** phân quyền Leader/Annotator, lưu lịch sử review, tích hợp CVAT API và đối chiếu detector (khi có điều kiện).

## 9. Kết luận

Dashboard đã có bộ chức năng phục vụ quan sát phân bố class/thuộc tính, sàng lọc chất lượng ảnh/label, phân tích coverage động và tìm ảnh metadata cần kiểm tra. Giá trị thực tế kỳ vọng là giảm thời gian thống kê thủ công và tập trung review vào nhóm có tín hiệu bất thường. Tuy nhiên, **mức tiết kiệm thời gian và độ chính xác phát hiện lỗi vẫn cần pilot xác minh** trước khi đưa vào kết luận cuối cùng của chương trình.
