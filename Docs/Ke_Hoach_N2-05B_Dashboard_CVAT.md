# KẾ HOẠCH THỰC HIỆN — N2-05B DASHBOARD CVAT

**Đề tài:** Dashboard phân bố class và thuộc tính dữ liệu, hỗ trợ Leader giám sát và kiểm tra chất lượng annotation CVAT.  
**Phạm vi triển khai hiện tại:** CVAT for images 1.1, ảnh raster và bounding box 2D, **không có Ground Truth**.  
**Thời gian kế hoạch:** 03 tuần theo định hướng dự án; các mốc dưới đây là **đề xuất**, không phải nhật ký đã hoàn thành.

## 1. Bối cảnh và vấn đề

Leader nhận ZIP export từ annotator và cần trả lời nhanh: dataset có bao nhiêu ảnh/box/class; class nào quá ít hoặc quá nhiều; độ che khuất, thời tiết và thời điểm phân bố ra sao; ảnh/box nào đáng review; slice nào chưa đạt mục tiêu. Kiểm tra bằng tay từng XML và từng ảnh mất thời gian, khó tái lập và khó ưu tiên. Không có GT nên dashboard phải minh bạch rằng các tín hiệu bất thường không phải kết luận nhãn sai.

## 2. Mục tiêu

1. Tự động đọc ZIP CVAT, thống kê inventory, class, box size, occlusion, scene tags và custom attributes.
2. Sàng lọc Image Quality và Label Check A/B bằng các phép đo hình học/pixel.
3. Tạo Coverage theo class và slice **động**, cho Leader đặt target/weight và xem gap/attainment.
4. Tìm và xem ảnh theo `weather × timeofday`, nhất là `unknown`/`missing`, xuất danh sách review.
5. Xuất báo cáo và đo hiệu quả **baseline → pilot** theo thời gian trả lời câu hỏi và số phát hiện hữu ích.

## 3. Phạm vi và không thuộc phạm vi

| Trong phạm vi | Chưa triển khai / không cam kết |
|---|---|
| CVAT ZIP/XML, ảnh raster, bbox 2D | 3D cuboid, tracking, polygon/mask QA đầy đủ |
| Phân bố class/metadata/box size | Xác nhận class đúng/sai khi không có GT |
| Image Quality và tín hiệu Label Check A/B | Auto-correct annotation hoặc cập nhật trực tiếp CVAT |
| Coverage động, target số lượng, recommendations | Tối ưu target tự động bằng AI hoặc target % trực tiếp |
| Tìm ảnh theo weather/timeofday và CSV | Review workflow nhiều người có phân quyền, lịch sử duyệt |
| Một ZIP mỗi lần upload | Hợp nhất nhiều annotator ZIP với provenance bảo đảm |

## 4. Đối tượng và kịch bản sử dụng

- **Leader:** Upload ZIP, xem tổng quan, chọn ngưỡng, định nghĩa slice quan trọng, xuất danh sách ảnh/box cần review.
- **Annotator:** Nhận CSV danh sách ảnh cần kiểm tra, sửa metadata/box trong CVAT theo quyết định của người review.
- **Mentor:** Đối chiếu kết quả demo với mục tiêu, xem cách chọn metrics và baseline/pilot.

**Kịch bản điển hình:** Leader chọn `weather=unknown` và `timeofday=unknown`, nhận danh sách ảnh, preview ảnh gốc, ghi nhận ảnh cần sửa; sau đó đặt target cho `bus × night × rain`, xem gap và đề xuất ưu tiên.

## 5. Kế hoạch 3 tuần (đề xuất)

| Giai đoạn | Công việc | Deliverable | Tiêu chí kiểm tra |
|---|---|---|---|
| Tuần 1 | Rà soát parser, chuẩn hóa schema; thống kê class, box, weather, timeofday, occluded; xử lý unknown/missing | Distribution & Attributes | Kết quả đối chiếu được với mẫu XML nhỏ; rõ mẫu số |
| Tuần 2 | Image Quality, Label Check A/B, biểu đồ, review ảnh; hiệu chỉnh threshold bằng mẫu reviewer | Image/Label Quality | Rule chạy ổn với box invalid, ảnh thiếu, metadata thiếu |
| Tuần 3 | Coverage động, target, recommendations, Scene Finder, export, giao diện, test và đo baseline/pilot | Demo và báo cáo | Test các case chính; bảng thời gian và phản hồi reviewer |

## 6. Phân rã công việc (WBS)

| Mã | Hạng mục | Công việc chi tiết | Phụ thuộc |
|---|---|---|---|
| W01 | Ingestion | Kiểm tra ZIP, parse XML, match ảnh, bảo vệ tài nguyên | Không |
| W02 | Normalization | Schema ảnh/box, chuẩn hóa `missing`/`unknown`, ID | W01 |
| W03 | Distribution | Class count/share, size, occlusion, scene, attributes | W02 |
| W04 | Image Quality | Blur, brightness, contrast, noise, issue/score | W01 |
| W05 | Label A/B | Geometry, visual signals, priority, overlay | W01, W02 |
| W06 | Coverage | Target động, support/gap/attainment, weight | W02, W03 |
| W07 | Scene Finder | Lọc AND weather/timeofday, preview, CSV | W01, W02 |
| W08 | Reports | Export CSV/JSON, hướng dẫn đọc chỉ số | W03–W07 |
| W09 | Validation | Unit test, case đối chiếu thủ công, pilot | W01–W08 |

## 7. Dữ liệu thử nghiệm và tiêu chí nghiệm thu

**Bộ test tối thiểu cần có:** ZIP chỉ có ảnh; ZIP có XML+ảnh; XML có image không box; box sai tọa độ; hai box cùng class trong một ảnh; ảnh thiếu file; metadata `unknown`, `missing`, `rain`, `night`; slice support=0; target vượt và không vượt; slice giao nhau; ZIP có tên ảnh trùng basename. Những trường hợp này là **kế hoạch test**, không phải tất cả đã được xác minh.

**Tiêu chí nghiệm thu đề xuất:**

- Thống kê số box/class và số ảnh chứa class khớp kiểm đếm thủ công trên fixture nhỏ.
- Slice `images` đếm ảnh duy nhất, `objects` đếm box; gap/attainment/weight khớp công thức.
- Scene Finder lọc đồng thời hai điều kiện và export đúng danh sách.
- Không kết luận annotation sai chỉ từ proxy/threshold.
- Chức năng không có dữ liệu phải hiển thị `not available`/thông báo rõ, không suy diễn 0 thành lỗi.

## 8. Đo lường baseline → pilot

| KPI | Baseline | Pilot | Cách đo |
|---|---|---|---|
| Thời gian trả lời câu hỏi thống kê | `T_manual` — chưa đo | `T_dashboard` — chưa đo | Cùng bộ dữ liệu, cùng câu hỏi, đo từ lúc bắt đầu đến khi trả lời đúng |
| Số class/thuộc tính phân tích được | Chưa đo | Chưa đo | Đếm class, trường metadata và thuộc tính có thống kê hợp lệ |
| Số ảnh/box cần review phát hiện | Chưa đo | Chưa đo | Đếm các cờ theo loại; **không** đồng nghĩa số lỗi thật |
| Precision của review flags | Chưa đo | Chưa đo | Reviewer xác nhận TP/FP trên mẫu đã chọn; `TP/(TP+FP)` |
| Metadata unresolved tìm được | Chưa đo | Chưa đo | Đếm ảnh có unknown/missing; đối chiếu CSV |
| Mức đạt target slice | Theo target Leader đặt | Theo target Leader đặt | Support, gap, attainment và weighted coverage |

**Tỷ lệ tiết kiệm thời gian** (khi có số đo): `100 × (T_manual−T_dashboard)/T_manual`. Không ghi kết quả % nếu chưa chạy pilot.

## 9. Rủi ro và giảm thiểu

| Rủi ro | Tác động | Hướng xử lý |
|---|---|---|
| ZIP/XML thiếu ảnh hoặc tag | Thiếu preview/metadata | Phân biệt missing/unknown; thông báo giới hạn |
| Class hiếm tự nhiên | Cảnh báo mất cân bằng sai ngữ cảnh | Cho Leader đặt target theo nghiệp vụ |
| Ảnh đêm/sương mù bị coi là chất lượng kém | Nhiều false positive | Hiệu chỉnh ngưỡng theo slice, review mẫu |
| Trùng `image_id` khi nhiều dataset | Đếm coverage sai | Thêm khóa ghép `dataset_id:image_id` trước khi hỗ trợ multi-ZIP |
| Tổ hợp slice chồng lấn | Cộng gap sai | Không cộng gap giữa các slice |
| Nhiều slice tự sinh | Quá tải giao diện | Giới hạn 250 và cho lọc ưu tiên |
| Giao diện CSS phụ thuộc Streamlit | Hiển thị khác phiên bản | Chốt dependency, test trên môi trường triển khai |

## 10. Kết quả cần bàn giao

Mã nguồn và README; hướng dẫn chạy; metric catalog; tài liệu giải pháp kỹ thuật; báo cáo thực hiện; tập fixture/test; bảng baseline→pilot sau khi đo; ví dụ CSV/JSON và ảnh demo. **Tình trạng hiện có của các deliverable được ghi riêng trong `Bao_cao_thuc_hien.md`.**
