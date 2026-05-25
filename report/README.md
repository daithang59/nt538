# Report LaTeX Template

Template này được tạo theo đề `_Lab__Parallel_Computing.pdf` và mã nguồn trong `challenge/`.

## File chính

- `main.tex`: cấu hình LaTeX, metadata nhóm/key/thành viên, macro dùng chung.
- `sections/01_overview.tex`: tổng quan yêu cầu và cách đo hiệu năng.
- `sections/challenge1.tex` đến `sections/challenge6.tex`: nội dung cho từng challenge, gồm phân tích và lưu đồ thuật toán.
- `sections/08_conclusion.tex`: tổng hợp kết quả và checklist trước khi nộp.
- `sections/09_appendix.tex`: phụ lục đo hiệu năng và rubric đối chiếu đề.

## Cách build

Khuyến nghị dùng XeLaTeX vì báo cáo viết tiếng Việt Unicode:

```bash
cd report
latexmk -xelatex main.tex
```

Nếu không có `latexmk`:

```bash
cd report
xelatex main.tex
xelatex main.tex
```

## Các phần cần điền

Tìm toàn bộ placeholder:

```bash
grep -R "CẦN ĐIỀN\\|placeholder" .
```

Cần điền tối thiểu:

- `\ReportGroupCode`, `\ReportKey`, `\MemberOne`... trong `main.tex`.
- Bảng môi trường thực nghiệm ở `sections/01_overview.tex`.
- Bảng benchmark và phần nhận xét của từng challenge.
- Cập nhật `sections/challenge5.tex` sau khi có code cuối cùng vì `challenge/challenge5.py` hiện đang rỗng.

## Lưu ý theo đề

- Chỉ nộp mã nguồn song song lên hệ thống chấm.
- Phiên bản tuần tự chỉ dùng để đo so sánh trong báo cáo.
- Challenge 3 nên có số liệu cho `n = 128, 256, 512, 1024, 5000` nếu môi trường đủ RAM.
- Challenge 4 nên có số liệu cho `n = 10^4, 10^5, 10^6`.
