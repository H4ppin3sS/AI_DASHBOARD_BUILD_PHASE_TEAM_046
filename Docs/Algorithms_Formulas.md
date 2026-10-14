# CVAT Quality Dashboard — Tài liệu thuật toán và công thức

**Phiên bản đối chiếu:** `cvat_quality_dashboard_merged.py` (bản hiện tại).  
**Mục đích:** giải thích cơ sở toán học, cách code triển khai, ví dụ tính, ngưỡng và giới hạn cho hai module **Image Quality** và **Label Check A/B**.  
**Phạm vi:** ảnh raster và bounding box 2D xuất từ CVAT for images; **không có Ground Truth**.

> **Phân biệt:** Các công thức dưới đây mô tả phép đo thật sự trong code. Các nhận xét về mục đích, ưu/nhược điểm và phương án hiệu chỉnh là diễn giải kỹ thuật. Những threshold mặc định là quy tắc thử nghiệm, **không phải kết quả tối ưu hóa thực nghiệm**.

## 1. Tổng quan pipeline

```text
ZIP upload
  ├── Quét file JPG/JPEG/PNG/BMP/WEBP (đường dẫn thư mục con được giữ nguyên)
  │     └── Giải mã bằng OpenCV → Image Quality → điểm, flags, CSV
  └── Tìm annotations.xml → đọc <image> và <box>
        ├── Geometry A: kiểm tra tọa độ, diện tích, aspect ratio, IoU
        └── Visual B: crop box từ ảnh → Canny, variance, Laplacian, LAB, perimeter
              └── flags → REVIEW / NO_SIGNAL / A_ONLY → HIGH / MEDIUM / LOW
```

**Cách khớp ảnh–annotation:** tìm đường dẫn tương đối trùng khớp; nếu không có, thử hậu tố đường dẫn rồi tên file duy nhất. Nếu nhiều ảnh trùng basename, không đoán tùy tiện. Module Image Quality vẫn có thể chạy khi không có XML; Label Check cần XML. ZIP có XML nhưng không có ảnh có thể dùng riêng hàm kiểm tra A trong mã gốc, tuy nhiên **giao diện merged hiện tại chặn ZIP không có ảnh**, nên không thể chạy A-only qua giao diện này. Đây là giới hạn triển khai cần phân biệt.

**Kiểm soát dữ liệu:** giới hạn 50 MiB/ảnh và tổng 1 GiB dữ liệu ảnh giải nén theo metadata ZIP. Định dạng XML đang xử lý `<image>` và `<box>`, không phân tích polygon, segmentation, 3D cuboid hay tracking.

## 2. Quy ước toán học và tiền xử lý

- Ảnh màu OpenCV có dạng `image[H, W, 3]` theo thứ tự kênh **BGR**.
- Ảnh xám `gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)`; pixel xám thường trong [0,255]. OpenCV chuyển BGR sang gray theo tổ hợp trọng số xấp xỉ: \(Y = 0.114 B + 0.587 G + 0.299 R\).
- Với \(N = W H\), trung bình \(\mu = \frac{1}{N}\sum_{i=1}^{N}Y_i\), phương sai tổng thể \(\sigma^2 = \frac{1}{N}\sum_i(Y_i-\mu)^2\), độ lệch chuẩn \(\sigma=\sqrt{\sigma^2}\). NumPy `mean`, `var`, `std` mặc định dùng mẫu số \(N\), không phải \(N-1\).
- Các chỉ số pixel/đạo hàm phụ thuộc độ phân giải, độ nén, nội dung cảnh và tiền xử lý; **không nên so sánh mù quáng** giữa các tập ảnh rất khác nhau.

## 3. Image Quality — thuật toán và công thức

### 3.1 Blur Score — phương sai Laplacian

**Trong code:** `cv2.Laplacian(gray, cv2.CV_64F).var()`.

Laplacian xấp xỉ đạo hàm bậc hai của cường độ ảnh:

\[\nabla^2Y = \frac{\partial^2Y}{\partial x^2}+\frac{\partial^2Y}{\partial y^2}.\]

Với ảnh rời rạc, OpenCV áp dụng kernel Laplacian (mặc định `ksize=1`) để có \(L_i\). Điểm:

\[S_{blur}=\operatorname{Var}(L)=\frac1N\sum_i(L_i-\bar L)^2.\]

**Trực giác:** cạnh sắc tạo biến thiên mạnh ở đạo hàm bậc hai → phương sai cao; ảnh mất nét thường có điểm thấp. **Điều kiện cảnh báo:** `S_blur < 100` → `BLUR`. **Không có đơn vị vật lý chuẩn.** Ảnh bề mặt phẳng ít chi tiết cũng có điểm thấp dù chụp đúng nét; nhiễu có thể làm điểm cao giả.

**Ví dụ minh họa:** ảnh A điểm 65 → cờ `BLUR`; ảnh B điểm 180 → không bật cờ này. Không suy ra ảnh B “tốt hơn toàn diện”.

### 3.2 Brightness — độ sáng trung bình

\[B=\frac1N\sum_iY_i.\]

**Code:** `np.mean(gray)`. Ngưỡng: `B < 40` → `DARK`; `B > 215` → `OVEREXPOSED`. Các so sánh là **nghiêm ngặt** (`<`, `>`), bằng ngưỡng không bị gắn cờ. Đây là độ sáng trung bình toàn ảnh, không phải phép đo exposure vật lý; ảnh đêm hợp lệ có thể bị gắn `DARK`.

### 3.3 Contrast — độ lệch chuẩn mức xám

\[C=\sqrt{\frac1N\sum_i(Y_i-B)^2}.\]

**Code:** `np.std(gray)`. `C < 25` → `LOW_CONTRAST`. Giá trị thấp nghĩa là mức xám tập trung gần trung bình, nhưng không chứng minh thiếu chi tiết quan trọng. **Phân biệt:** Contrast của Image Quality là *độ lệch chuẩn gray toàn ảnh*, khác hoàn toàn với `foreground_contrast` LAB ở Label Check B.

**Ví dụ:** các pixel [90, 100, 110] có \(B=100\), \(C=\sqrt{200/3}\approx8.16\), nên nếu đó là toàn bộ ảnh thì kích hoạt `LOW_CONTRAST`.

### 3.4 Noise Score — Gaussian residual + Sobel + MAD

Code không dùng độ lệch chuẩn toàn ảnh để ước lượng nhiễu vì cạnh và texture tự nhiên có thể làm lệch kết quả. Pipeline cụ thể:

1. Chuyển `gray` sang `float32`.
2. Làm mượt Gaussian 3×3: \(G=\operatorname{GaussianBlur}_{3\times3}(Y)\).
3. Lấy phần dư: \(R=Y-G\).
4. Tính gradient Sobel \(g_x=\operatorname{Sobel}_x(Y)\), \(g_y=\operatorname{Sobel}_y(Y)\), độ lớn \(M=\sqrt{g_x^2+g_y^2}\).
5. Chỉ lấy vùng có gradient thấp \(\Omega=\{i:M_i<15\}\) để giảm tác động của biên vật thể.
6. Nếu \(|\Omega|<100\), trả `NaN` (không đủ mẫu).
7. Với phần dư \(r_i, i\in\Omega\), tính \(m=\operatorname{median}(r_i)\) và:

\[\operatorname{MAD}=\operatorname{median}_{i\in\Omega}|r_i-m|.\]

\[S_{noise}=1.4826\times\operatorname{MAD}.\]

Hệ số **1.4826** quy đổi MAD thành ước lượng độ lệch chuẩn khi nhiễu xấp xỉ phân phối Gaussian. **Code:** `S_noise > 10` → `POSSIBLE_HIGH_NOISE`; `NaN` thì **không** tự gắn cờ. Đây là **ước lượng proxy**, có thể bị ảnh hưởng bởi JPEG artifacts, chi tiết nhỏ, sharpening hoặc cấu trúc ảnh.

### 3.5 Black / White pixel percentage

\[P_{black}=100\times\frac{\#\{i:Y_i<20\}}{N},\quad P_{white}=100\times\frac{\#\{i:Y_i>245\}}{N}.\]

Các chỉ số `black_pct`, `white_pct` được **hiển thị và xuất CSV**, nhưng **không trực tiếp tạo flag hay trừ điểm** trong code hiện tại. Chúng có thể giúp giải thích ảnh rất tối/sáng, nhưng không thay thế histogram hay phân tích vùng quan tâm.

### 3.6 Resolution và dung lượng

- `width`, `height`: kích thước giải mã thực tế theo pixel.
- `LOW_RESOLUTION` nếu `width < 320` **hoặc** `height < 240`.
- `size_kb = len(image_bytes)/1024`: dung lượng file ảnh nén, **không phải** kích thước ảnh sau giải mã; 1024 byte được hiển thị dưới nhãn KB (thực chất gần KiB).

### 3.7 Điểm sàng lọc Image Quality

**Quy tắc chính xác trong code:**

\[S=\max\bigl(0,100-20I_{BLUR}-15I_{DARK}-15I_{OVEREXPOSED}-15I_{LOW\_CONTRAST}-15I_{LOW\_RESOLUTION}-15I_{NOISE}\bigr).\]

Ở đây \(I\) bằng 1 nếu flag có mặt, ngược lại bằng 0. `READ_ERROR` có score = 0. **Ví dụ:** `BLUR` + `LOW_CONTRAST` + `POSSIBLE_HIGH_NOISE` → \(100-20-15-15=50\). `status=REVIEW` khi có bất kỳ issue, còn không thì `PASS`.

**Cảnh báo về diễn giải:** trọng số 20/15 là quy tắc do người thiết kế đặt, **không phải xác suất, độ chính xác hay thang điểm đã được kiểm định**. Trung bình score không đo trực tiếp độ đúng của annotation.

## 4. Label Check A — hình học bounding box

### 4.1 Tọa độ và điều kiện hợp lệ

Mỗi box lấy từ XML: \(b=(x_1,y_1,x_2,y_2)\), tương ứng `xtl`, `ytl`, `xbr`, `ybr`.

**Hợp lệ cơ bản** nếu mọi tọa độ hữu hạn (`np.isfinite`) và \(x_2>x_1, y_2>y_1\). Nếu không → `INVALID_BOX`. Box không hợp lệ **không** được tính visual metrics.

### 4.2 Box size và Area Percentage

\[w_b=x_2-x_1,\quad h_b=y_2-y_1,\quad A_b=w_bh_b.\]

\[A_{pct}=100\times\frac{A_b}{WH}.\]

`A_pct < 0.01` → `SMALL_BOX`; `A_pct > 80` → `LARGE_BOX` (khi W,H dương). **Ví dụ:** ảnh 640×640, box 64×80 → \(A_{pct}=100\times5120/409600=1.25\%\), không vi phạm hai ngưỡng trên. Một đối tượng nhỏ ở xa có thể hợp lệ dù diện tích rất nhỏ; vật thể chiếm toàn ảnh cũng có thể hợp lệ.

### 4.3 Aspect Ratio

\[AR=\frac{w_b}{h_b}.\]

`AR < 0.15` hoặc `AR > 7.0` → `ASPECT_RATIO_OUTLIER`. Ví dụ box 140×10 có `AR=14` → cảnh báo. Tuy nhiên tỷ lệ này phụ thuộc class (cột đèn, xe bus, biển báo, người đứng...) nên không nên xem là sai chắc chắn.

### 4.4 Out of Bounds

`OUT_OF_BOUNDS` nếu \(x_1<0\) hoặc \(y_1<0\) hoặc \(x_2>W\) hoặc \(y_2>H\). Đây là kiểm tra với **kích thước ảnh giải mã nếu có ảnh**, nếu không dùng width/height trong XML. Trường hợp `x2 == W` không bị coi vượt biên. Box vượt biên được *clip* về vùng ảnh **chỉ khi tính Visual B**, không thay đổi tọa độ XML ban đầu.

### 4.5 Intersection over Union (IoU) và duplicate

Với hai box A, B, tính diện tích giao:

\[A_{\cap}=\max(0,\min(x_{2A},x_{2B})-\max(x_{1A},x_{1B}))\times\max(0,\min(y_{2A},y_{2B})-\max(y_{1A},y_{1B})).\]

\[IoU(A,B)=\frac{A_{\cap}}{A_A+A_B-A_{\cap}}.\]

**Ví dụ:** A=[0,0,100,100], B=[5,5,105,105]. Giao = 95×95=9025, hợp = 10000+10000−9025=10975, IoU≈0.822. Với ngưỡng 0.90, cặp này **không** bị flag.

Code chỉ so sánh **các box cùng ảnh và cùng nhãn class**; nếu `IoU >= 0.90`, **cả hai** được gắn `POSSIBLE_DUPLICATE`. Hai vật thể thực tế có thể che khuất/chồng nhau, nên đây vẫn là tín hiệu cần review, không phải kết luận trùng nhãn.

**Độ phức tạp:** kiểm tra từng cặp box trong ảnh có \(O(k^2)\) với k box/ảnh; dataset đông đối tượng nên tối ưu bằng spatial index/grid hoặc lọc cặp theo vị trí.

## 5. Label Check B — xử lý ảnh bên trong box

**Tiền điều kiện:** có ảnh giải mã được và box có tọa độ hợp lệ. Tọa độ ROI được clip vào [0,W]×[0,H], với `floor` đầu và `ceil` cuối. Nếu ROI có chiều rộng hoặc chiều cao **< 8 pixel**, hàm `visual_metrics` trả `None`, gắn `ROI_TOO_SMALL`; không tính năm chỉ số dưới đây. Đây là điều kiện *không đủ vùng để đánh giá*, không tự khẳng định nhãn sai.

### 5.1 Edge Density — Canny

Code: `edges = cv2.Canny(roi_gray, 50, 150)` với ngưỡng Canny **cố định** 50 và 150. Canny gồm các bước khái niệm: làm mượt, gradient, non-maximum suppression và hysteresis thresholding; hàm OpenCV xử lý nội bộ.

\[D_{edge}=\frac{\#\{i\in ROI:edges_i>0\}}{|ROI|}.\]

`D_edge < 0.02` → `LOW_EDGE_DENSITY`. **Ví dụ:** ROI 100×100 có 120 pixel cạnh → 120/10000=0.012 → cảnh báo. Ít cạnh có thể do nền trơn, đối tượng ít texture, blur, ảnh đêm hoặc box nằm sai vị trí; **không tự chứng minh box trống**.

### 5.2 Texture Variance — phương sai mức xám trong ROI

\[V_{texture}=\frac1{|ROI|}\sum_{i\in ROI}(Y_i-\bar Y_{ROI})^2.\]

Code: `np.var(roi.astype(np.float32))`. `V_texture < 100` → `LOW_TEXTURE`. Đơn vị theo **mức xám bình phương**, không phải phần trăm. Texture thấp có thể là bề mặt đồng nhất hợp lệ.

### 5.3 Laplacian Variance — độ sắc nét trong ROI

\[S_{roi}=\operatorname{Var}(\nabla^2Y_{ROI}).\]

Code: `cv2.Laplacian(roi, cv2.CV_64F).var()`. `S_roi < 50` → `LOW_SHARPNESS`. Khác `blur_score` của Image Quality ở **phạm vi tính** (box thay vì toàn ảnh) và **ngưỡng** (50 thay vì 100). Không có nghĩa là ảnh gốc bị mờ toàn cục.

### 5.4 Foreground Contrast — khoảng cách màu LAB

1. Chuyển toàn ảnh BGR→LAB bằng `cv2.COLOR_BGR2LAB`.
2. Lấy vùng **inside** chính là ROI box.
3. Mở rộng box ra bốn phía bằng margin:

\[m=\max\left(4,\left\lfloor0.25\max(w_b,h_b)\right\rfloor\right).\]

4. Vùng **outside** là *vành xung quanh box* nằm trong vùng mở rộng nhưng loại bỏ chính phần inside.
5. Tính vector trung bình ba kênh LAB của inside và outside: \(\boldsymbol\mu_{in},\boldsymbol\mu_{out}\).
6. Tính khoảng cách Euclid:

\[C_{LAB}=\|\boldsymbol\mu_{in}-\boldsymbol\mu_{out}\|_2=\sqrt{(\Delta L)^2+(\Delta A)^2+(\Delta B)^2}.\]

`C_LAB < 12` → `LOW_FOREGROUND_CONTRAST` nếu có vành outside để đo. Nếu không có pixel outside, kết quả `NaN`, **không** gắn cờ này. Đây là **khoảng cách Euclid trên giá trị LAB mã hóa 8-bit của OpenCV**, **không phải ΔE2000**, và không phải kiểm tra segmentation. Một đối tượng cùng màu nền có thể hợp lệ; nền nhiều màu có thể làm trung bình bị triệt tiêu.

**Ví dụ minh họa:** \(\mu_{in}=(150,130,125)\), \(\mu_{out}=(154,135,128)\). Khoảng cách \(\sqrt{4^2+5^2+3^2}=\sqrt{50}\approx7.07<12\), gắn cảnh báo.

### 5.5 Boundary Support — mật độ cạnh ở dải viền trong box

Dùng cùng bản đồ Canny của ROI. Độ dày dải viền:

\[t=\min\left(4,\max\left(1,\left\lfloor\frac{\min(w_{ROI},h_{ROI})}{8}\right\rfloor\right)\right).\]

Tạo mask gồm các pixel trong `t` hàng trên/dưới và `t` cột trái/phải của ROI. Tính:

\[S_{boundary}=\frac{\#\{i\in band:edges_i>0\}}{|band|}.\]

`S_boundary < 0.02` → `WEAK_BOUNDARY_SUPPORT`. **Điểm cần nói chính xác:** thuật toán chỉ đo **mật độ cạnh gần đường biên box**, **không** xác định cạnh vật thể trùng cạnh box; nó **không phải thuật toán đo box tightness**. Box ôm sát vật thể có bề mặt mịn vẫn có thể cho giá trị thấp.

### 5.6 POSSIBLE_EMPTY_BOX — quy tắc kết hợp

Chỉ bật khi đồng thời thỏa ba điều kiện:

\[D_{edge}<0.02\ \land\ V_{texture}<100\ \land\ C_{LAB}<12.\]

Code kiểm tra sự có mặt của ba flags `LOW_EDGE_DENSITY`, `LOW_TEXTURE`, `LOW_FOREGROUND_CONTRAST`. `LOW_SHARPNESS` và `WEAK_BOUNDARY_SUPPORT` **không phải** điều kiện bắt buộc. **Đây là giả thuyết box có rất ít tín hiệu thị giác**, không phải phát hiện box trống đã được chứng minh; nền đường, tường, vật thể trơn, ảnh tối đều có thể gây false positive.

## 6. Thuật toán kết hợp flags, trạng thái và ưu tiên

### 6.1 Ưu tiên

| Priority | Điều kiện code |
|---|---|
| `HIGH` | Có một trong `INVALID_BOX`, `OUT_OF_BOUNDS`, `POSSIBLE_DUPLICATE`, `POSSIBLE_EMPTY_BOX` |
| `MEDIUM` | Không có HIGH, nhưng có flag Geometry A bất kỳ **hoặc** Visual B khác `LOW_SHARPNESS`, `ROI_TOO_SMALL` |
| `LOW` | Còn lại, bao gồm chỉ `LOW_SHARPNESS`, chỉ `ROI_TOO_SMALL`, hoặc không có flag |

**Lưu ý:** `LOW` không đồng nghĩa “đang có lỗi nhẹ”; nó cũng là priority mặc định của box **không có cảnh báo**. Priority là thứ tự review, **không phải xác suất sai**.

### 6.2 Trạng thái

- `REVIEW`: có bất kỳ Geometry flag, hoặc Visual flag **khác** `ROI_TOO_SMALL`.
- `NO_SIGNAL`: không có flag kích hoạt review; có thể vẫn có `ROI_TOO_SMALL`.
- `A_ONLY`: không có ảnh cho B và không có Geometry flag.
- `REVIEW_A_ONLY`: không có ảnh cho B nhưng có Geometry flag.

Ở giao diện, `Box cần review` dùng điều kiện `status.str.startswith("REVIEW")`, nên bao gồm `REVIEW_A_ONLY`. `Box có ảnh kiểm tra B` trong code **đếm box có `image_available=True`**, không bảo đảm ROI đủ 8×8 để thực sự tính được năm metrics B.

### 6.3 Ví dụ quyết định

| Box | A flags | B flags | Priority | Status |
|---|---|---|---|---|
| 1 | — | — | LOW | NO_SIGNAL |
| 2 | SMALL_BOX | — | MEDIUM | REVIEW |
| 3 | — | LOW_SHARPNESS | LOW | REVIEW |
| 4 | POSSIBLE_DUPLICATE | LOW_EDGE_DENSITY | HIGH | REVIEW |
| 5 | — | LOW_EDGE_DENSITY, LOW_TEXTURE, LOW_FOREGROUND_CONTRAST, POSSIBLE_EMPTY_BOX | HIGH | REVIEW |
| 6 (không có ảnh) | OUT_OF_BOUNDS | — | HIGH | REVIEW_A_ONLY |
| 7 | — | ROI_TOO_SMALL | LOW | NO_SIGNAL |

## 7. Chỉ số dashboard và thuật toán biểu đồ

- **Tổng ảnh:** số ảnh đọc được từ ZIP để phân tích, kể cả ảnh lỗi giải mã (ảnh lỗi có `ERROR`).
- **Ảnh cần review:** số ảnh Image Quality có `status=REVIEW`.
- **CVAT boxes:** số thẻ `<box>` đọc được từ XML (trong trường hợp `can_label=True`).
- **Box cần review:** số box Label Check có status bắt đầu `REVIEW`.
- **Số class:** số giá trị `label` khác nhau của box.
- **Điểm trung bình ảnh:** trung bình số học của `score`, **bao gồm ảnh `ERROR` có score=0**.
- **Review rate theo class:** \(100\times\frac{\text{review boxes trong class}}{\text{tổng boxes trong class}}\). Đây là *tỷ lệ kích hoạt quy tắc*, không phải tỷ lệ annotation sai.
- **Donut/Pie:** đếm số bản ghi theo status hoặc priority rồi chia tổng để biểu diễn tỷ trọng.
- **Histogram:** chia trục đo thành `nbins=35` (blur) hoặc `nbins=40` (box area), đếm quan sát mỗi bin; số bin là cấu hình biểu đồ, **không phải ngưỡng chất lượng**.
- **Scatter:** mỗi điểm là một ảnh (`brightness` × `contrast`) hoặc một box (`edge_density` × `foreground_contrast`). Màu thể hiện `status`/`priority`, không biểu thị mô hình phân cụm.
- **Box plot:** thể hiện phân vị, trung vị và các điểm ngoại lai theo quy tắc biểu đồ của Plotly. Outlier trên biểu đồ **không tự sinh flag** trong pipeline.
- **Bar chart:** tần suất các loại issue. Một ảnh/box có thể có nhiều flags, do đó **tổng số flags có thể lớn hơn số ảnh/box review**.

## 8. Lựa chọn và hiệu chỉnh thuật toán/ngưỡng

### 8.1 Vì sao dùng các thuật toán này?

| Thuật toán | Lý do phù hợp | Không thể xác định |
|---|---|---|
| Laplacian variance | Rẻ, dễ giải thích, phát hiện dấu hiệu mất nét | Focus đúng tuyệt đối, chất lượng annotation |
| Gray mean/std | Mô tả nhanh độ sáng và tương phản toàn ảnh | Đối tượng chính có nhìn rõ hay không |
| Gaussian + Sobel + MAD | Ước lượng nhiễu robust hơn residual std toàn ảnh | Phân biệt hoàn toàn nhiễu với texture/compression |
| Area/aspect/out-of-bounds | Rất nhanh, minh bạch, bắt bất thường hình học | Class đúng, box có ôm đối tượng không |
| IoU cùng class | Tìm box gần như chồng trùng | Hai đối tượng thật có chồng nhau không |
| Canny/texture/Laplacian ROI | Phát hiện vùng box ít tín hiệu ảnh | Vật thể thực sự có tồn tại không |
| LAB inside–outside | So sánh vùng box với lân cận | Ranh giới chính xác của vật thể |
| Perimeter edge density | Tìm vùng viền thiếu cạnh | Box tightness thật sự |

### 8.2 Quy trình calibration được đề xuất (chưa có trong code)

1. **Chọn mẫu có phân tầng:** lấy ảnh theo class, diện tích box (nhỏ/vừa/lớn), điều kiện sáng, che khuất và chất lượng ảnh. Không chỉ lấy ảnh “đẹp”.
2. **Leader review thủ công một tập nhỏ:** gắn nhãn `cần sửa / không cần sửa / không chắc`, ghi nguyên nhân; đây là **review sample** chứ không nhất thiết phải có GT cho toàn dataset.
3. **Vẽ phân bố** của từng metric theo class và nhóm kích thước; kiểm tra xem các threshold mặc định cắt vào vùng nào.
4. **Thử nhiều ngưỡng:** đo số lượng cảnh báo, tỷ lệ Leader xác nhận hữu ích, false alarms trên tập mẫu; ưu tiên **precision của review queue** và **thời gian review tiết kiệm** thay vì chỉ tăng số flag.
5. **Cố định ngưỡng và kiểm tra trên mẫu khác:** tránh chọn ngưỡng chỉ vì nó hợp với một vài ảnh đã xem.
6. **Ghi phiên bản cấu hình:** ngày, dữ liệu dùng calibration, threshold, kết quả review, người phê duyệt.

**Ví dụ (đề xuất, không phải code hiện tại):** thay ngưỡng `min_edge=0.02` cố định bằng percentile thứ 5–10 của edge density trong *từng class × nhóm kích thước*, nếu có đủ mẫu và Leader xác nhận cách này hữu ích. Với nhóm ít mẫu, dùng threshold chung hoặc ghi `NOT_CALIBRATED`.

### 8.3 Rủi ro và các trường hợp dễ báo sai

- **Ảnh đêm/thiếu sáng:** brightness, Laplacian, edge và LAB contrast có thể đồng loạt thấp → các cảnh báo tương quan, không phải bốn bằng chứng độc lập.
- **Box rất nhỏ:** crop 8×8 không đủ; với box 10×10, các metric dễ dao động mạnh.
- **Vật thể phẳng/đồng màu:** texture và edge thấp dù box hợp lệ.
- **Occlusion/truncation:** bounding box hợp lệ có thể chứa nhiều nền, khiến visual metrics khó diễn giải.
- **Ảnh bị resize/nén:** Laplacian, Canny, MAD thay đổi; cần chuẩn hóa quy trình nhập ảnh trước khi so sánh.
- **Không có GT:** không thể công bố accuracy, precision, recall hay false-positive rate của hệ thống trên toàn bộ dataset chỉ dựa vào flags tự động.

## 9. Một số chi tiết triển khai dễ hiểu nhầm

1. `PASS` và `NO_SIGNAL` nghĩa là **không kích hoạt quy tắc hiện tại**, không phải đã xác nhận đúng.
2. `HIGH` không phải nhãn “sai nghiêm trọng”; chỉ là **ưu tiên review cao**.
3. `LOW_SHARPNESS` trong B không đồng nghĩa `BLUR` toàn ảnh; phạm vi và ngưỡng khác nhau.
4. `foreground_contrast` LAB không giống `contrast` gray std.
5. `WEAK_BOUNDARY_SUPPORT` **không phải box tightness**.
6. `POSSIBLE_EMPTY_BOX` **không phải mô hình phát hiện đối tượng**.
7. `ROI_TOO_SMALL` không làm `status=REVIEW` khi đứng một mình; đây là dấu hiệu **không đánh giá được**.
8. Chỉ số `occluded` được đọc từ XML nhưng **chưa được dùng để điều chỉnh threshold**.
9. XML có thể chứa ảnh không nằm trong ZIP; Geometry có thể dùng kích thước khai báo, nhưng merged UI hiện yêu cầu ZIP có ít nhất một ảnh hợp lệ.
10. Code hiện tại tính gray/LAB lại cho từng box trong cùng ảnh; nếu dataset lớn có thể tối ưu bằng cách tính một lần/ảnh và truyền ROI.
11. `POSSIBLE_DUPLICATE` đánh dấu cả hai box cùng class có IoU vượt ngưỡng; không xác định box nào cần xóa.
12. Biểu đồ và điểm số dùng **heuristic/rule-based**, không có AI model, không có supervised learning và không có ground-truth matching.

## 10. Bảng tra nhanh: tham số trong code

| Tên tham số | Giá trị mặc định | Điều kiện phát cờ |
|---|---:|---|
| `blur_threshold` | 100 | `blur_score < 100` |
| `dark_threshold` | 40 | `brightness < 40` |
| `bright_threshold` | 215 | `brightness > 215` |
| `contrast_threshold` | 25 | `contrast < 25` |
| `noise_threshold` | 10 | `noise_score > 10` (nếu finite) |
| `min_width`, `min_height` | 320, 240 | width < 320 **hoặc** height < 240 |
| `black_threshold`, `white_threshold` | 20, 245 | chỉ tính tỷ lệ pixel, không phát cờ |
| `min_area_pct` | 0.01 | `area_pct < 0.01` |
| `max_area_pct` | 80 | `area_pct > 80` |
| `min_aspect`, `max_aspect` | 0.15, 7.0 | ngoài khoảng |
| `duplicate_iou` | 0.90 | `IoU >= 0.90`, cùng class |
| `min_edge` | 0.02 | `edge_density < 0.02` |
| `min_texture` | 100 | `texture_variance < 100` |
| `min_sharpness` | 50 | `laplacian_variance < 50` |
| `min_contrast` | 12 | `foreground_contrast < 12` (nếu finite) |
| `min_boundary` | 0.02 | `boundary_support < 0.02` |
| Canny low/high | 50 / 150 | cố định trong code, **không có slider** |
| Sobel flat gradient cutoff | 15 | cố định trong code |
| MAD minimum flat pixels | 100 | ít hơn → `NaN` |
| ROI minimum size | 8×8 | nhỏ hơn → `ROI_TOO_SMALL` |

## 11. Gợi ý cách trình bày trong báo cáo Build Phase

**Vấn đề:** Leader cần sàng lọc nhanh dữ liệu ảnh và nhãn CVAT khi không có GT cho toàn bộ tập.

**Giải pháp:** pipeline hai tầng: Image Quality kiểm tra tính sử dụng được của ảnh; Label Check A kiểm tra tính nhất quán hình học; Label Check B đối chiếu ROI với đặc trưng thị giác. Mọi tín hiệu được lưu ở mức ảnh/box, có giải thích và xem lại trực quan.

**Điểm mạnh:** dễ giải thích, không cần huấn luyện model, xử lý class tùy biến, xuất CSV để audit, cho phép thay threshold.

**Giới hạn:** heuristic không xác minh đúng/sai nhãn; chưa phát hiện missing object/class mismatch; nhiều metric phụ thuộc cảnh; chưa có calibration và chưa có phép đo độ hiệu quả review dựa trên mẫu đã được Leader kiểm tra.

**Hướng đánh giá đề xuất:** so sánh thời gian Leader tìm lỗi khi review thủ công ngẫu nhiên với khi review theo priority; báo cáo `review precision@K` trên mẫu đã kiểm tra và mức tiết kiệm thời gian. **Chỉ báo cáo các con số sau khi thực nghiệm thực sự được tiến hành.**

---

*Tài liệu này mô tả code đã có, không khẳng định các ngưỡng đã được xác thực hay các cảnh báo là lỗi thực tế.*
