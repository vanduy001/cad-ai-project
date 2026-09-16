# CAD-AI Prototype — Đồ án tốt nghiệp

Pipeline: **Yêu cầu ngôn ngữ tự nhiên → LLM → Parametric Spec → CadQuery code → Mô hình 3D → STEP**

## Cấu trúc dự án

```
cad-ai-project/
├── spec_schema.py     # Định nghĩa Parametric Spec (PartSpec, Feature, Constraint)
├── cq_generator.py    # Sinh code CadQuery từ PartSpec (template-based)
├── cq_executor.py     # Chạy code CadQuery, export STEP, bắt lỗi
├── validator.py        # LỚP KIỂM TRA — trọng tâm nghiên cứu (3 nhóm check)
├── llm_client.py       # Gọi Claude API cho NL->Spec và sửa lỗi (feedback loop)
├── pipeline.py          # Ghép toàn bộ, có vòng lặp tự sửa (max_iterations)
├── examples/            # Bộ NL request mẫu + spec tham chiếu
├── tests/                # Unit test cho từng module
└── requirements.txt
```

## Cài đặt

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
# Nếu pip cài cadquery lỗi (hay gặp trên Windows), dùng conda:
#   conda install -c conda-forge -c cadquery cadquery=2.4

export ANTHROPIC_API_KEY=sk-ant-...   # để dùng LLM thật, bỏ qua nếu chỉ chạy demo
```

## Chạy thử nhanh (không cần API key)

```bash
python pipeline.py --demo
```

Lệnh này dùng `DemoLLMClient` (rule-based, không gọi mạng) để build câu mẫu
"tấm phẳng 100x60x5mm, 4 lỗ Ø6mm, bo góc R3mm", chạy toàn bộ pipeline, export
`output.step`. Dùng để xác nhận môi trường CadQuery cài đúng trước khi tốn
API credit cho LLM thật.

## Chạy với yêu cầu tự do (cần API key + cadquery)

```bash
python pipeline.py --request "Thiết kế mặt bích thép, đường kính ngoài 80mm, đường kính trong 40mm, dày 8mm, bo cạnh R2mm" --output flange.step
```

## Chạy từng module độc lập (để debug/hiểu pipeline)

```bash
python spec_schema.py      # in ra spec mẫu + validate cấu trúc
python cq_generator.py     # in ra code CadQuery sinh từ spec mẫu
python cq_executor.py      # chạy thử executor (cần cadquery)
python validator.py        # test validator với 2 case: đúng / thiếu feature
```

## Mở rộng thêm part_type / feature_type mới

1. Thêm dataclass field cần thiết vào `PartSpec`/`Feature` nếu cần (thường không cần vì `params: dict` đã linh hoạt).
2. Thêm rule bắt buộc trong `validate_spec()` (spec_schema.py) — ví dụ base_dimensions bắt buộc cho part_type mới.
3. Viết hàm `_build_xxx_base()` trong `cq_generator.py`, đăng ký vào `_BASE_BUILDERS`.
4. Nếu là feature mới: viết `_apply_xxx()`, đăng ký vào `_FEATURE_APPLIERS`.
5. Thêm case kỳ vọng bounding box vào `_expected_bounding_box()` trong `validator.py`.
6. Cập nhật `SYSTEM_PROMPT` trong `llm_client.py` để LLM biết cách sinh spec cho part_type/feature mới.
7. Thêm 1-2 case vào `examples/` + chạy `pipeline.py --request "..."` để kiểm tra.

## Ghi log cho phần đánh giá (Chương 4 báo cáo)

`PipelineRunLog` (trong `pipeline.py`) đã chứa sẵn toàn bộ số liệu cần cho
bảng tiêu chí đánh giá đã thống nhất:

| Trường trong log | Dùng cho tiêu chí |
|---|---|
| `n_iterations` | Số vòng lặp hội tụ (đo khả năng tự sửa) |
| `success` | Tỷ lệ thành công |
| `final_metrics` (từ ValidationReport.metrics) | Sai lệch kích thước (%) |
| `history` | Chi tiết từng vòng lặp — dùng để phân tích case fail |
| `elapsed_sec` | Thời gian xử lý |

Gợi ý: viết thêm 1 script `run_batch_eval.py` (chưa có trong bản này) lặp qua
toàn bộ `examples/*.txt`, gọi `run_pipeline()`, gom `PipelineRunLog` vào 1
file CSV/JSON để vẽ biểu đồ trong báo cáo. Đây nên là việc làm ở Giai đoạn 4.

## Lưu ý quan trọng khi triển khai thật

- **Không exec() trực tiếp code LLM sinh** trong sản phẩm thật nếu bỏ qua
  bước template (nếu sau này thử hướng "LLM sinh code tự do" để so sánh) —
  dùng `run_subprocess()` trong `cq_executor.py`, có timeout, thay vì
  `run_inprocess()` chỉ nên dùng lúc dev.
- `cq_generator.py` hiện dùng cách tiếp cận **template-based** (đã thống
  nhất trong đề cương) — LLM chỉ sinh Spec (JSON có schema), không sinh code
  CadQuery trực tiếp. Điều này giúp validator biết chính xác cấu trúc code
  để kiểm tra, và giảm rủi ro code lỗi cú pháp/nguy hiểm.
- `validator.py` hiện kiểm tra ở mức bounding box + volume — đủ cho phase 1.
  Bản mở rộng nên duyệt `result.val().Faces()` để đếm chính xác số mặt trụ
  (đối chiếu số lỗ khoan) và đo khoảng cách giữa các mặt (đối chiếu
  min_wall_thickness) — đây là điểm có thể phát triển thêm để bài nghiên cứu
  sâu hơn.
