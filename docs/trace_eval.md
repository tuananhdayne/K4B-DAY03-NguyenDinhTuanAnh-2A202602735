# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Nguyen Dinh Tuan Anh  
> **Mã Sinh Viên / Mã Học viên:** 2A202602735  
> **Chủ đề Lựa chọn:** Trợ lý Học vụ VinUni: Tra cứu sinh viên và đặt lịch tư vấn  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 5 / 5 | TC04 cần tra cứu cố vấn trước rồi mới đặt lịch tư vấn. |
| **2. Tool Interaction** | 5 / 5 | Agent dùng `academic_query` và `schedule_appointment` qua MCP Server. |
| **3. Dynamic Decision** | 4 / 5 | Cố vấn trong bước đặt lịch được lấy từ Observation của bước tra cứu. |
| **4. Long Horizon Goal** | 4 / 5 | Agent giữ mục tiêu đặt lịch xuyên suốt nhiều hành động liên tiếp. |
| **TỔNG ĐIỂM AGENTIC FIT** | **18 / 20** | *Bài toán phù hợp triển khai Agentic System.* |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Dán 1 đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json` sinh ra từ phản hồi LLM API thật:

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu thông tin học vụ của sinh viên SV2026001.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "SV2026001"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "SV2026001",
      "data": {
        "full_name": "Nguyễn Văn An",
        "class": "AI-K4",
        "gpa": 3.85,
        "email": "an.nv@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "PGS.TS Nguyễn Văn A"
      }
    },
    "latency_ms": 4558.05
  },
  {
    "step": 2,
    "query": "Hãy tra cứu thông tin học vụ của sinh viên SV2026001.",
    "action_type": "FINAL_ANSWER",
    "thought": "Tổng hợp kết quả từ MCP Server thành công.",
    "output": "Kết quả tra cứu cho sinh viên SV2026001 (Nguyễn Văn An): Lớp AI-K4, GPA: 3.85, Email: an.nv@vinuni.edu.vn, Trạng thái: Đang học, Cố vấn: PGS.TS Nguyễn Văn A.",
    "latency_ms": 10.0
  }
]
```

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` và xác nhận Agent chạy mượt mà trên LLM API thật (Gemini/OpenAI).
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt (`academic_query` và `schedule_appointment`).
- **Bằng chứng Trace Waterfall:** Đã ghi nhận 10 sự kiện ReAct vào `docs/trace_waterfall.json` với độ trễ và chuỗi suy luận thực tế.
- **Kết quả đẩy Repo nộp bài:** [x] Mã nguồn và báo cáo đã sẵn sàng commit & push lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
