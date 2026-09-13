# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Nguyễn Đình Tuấn Anh  
> **Mã Sinh Viên / Mã Học viên:** 2A202602735  
> **Chủ đề Lựa chọn:** Trợ lý Tác tử Học vụ VinUni: Tra cứu sinh viên, Thẩm định học bổng, Điều kiện môn học & Đặt lịch tư vấn Cố vấn  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | **5 / 5** | Chuỗi tác vụ đa bước phức tạp (TC04: 2 bước; TC06: 3 bước; TC08: 4 bước liên hoàn) từ tra cứu hồ sơ -> xét học bổng -> thẩm định điều kiện tiên quyết môn học -> tự động đặt lịch hẹn. |
| **2. Tool Interaction** | **5 / 5** | Tác tử tích hợp bộ 4 công cụ chuẩn MCP (`academic_query`, `check_scholarship_eligibility`, `check_course_eligibility`, `schedule_appointment`) qua giao thức JSON-RPC 2.0. |
| **3. Dynamic Decision** | **5 / 5** | Dữ liệu đầu vào của các bước sau (tên cố vấn, tình trạng học phí, môn tiên quyết bị thiếu) phụ thuộc 100% vào Observation trả về từ bước trước, có rẽ nhánh linh hoạt. |
| **4. Long Horizon Goal** | **5 / 5** | Duy trì mục tiêu tổng thể xuyên suốt đến 4-5 vòng lặp ReAct liên tiếp, có cơ chế ngắt mạch an toàn Circuit Breaker (`--max-loop 1..5`) chống lặp vô tận. |
| **TỔNG ĐIỂM AGENTIC FIT** | **20 / 20** | **XUẤT SẮC: Hệ thống đạt độ phù hợp tối đa cho Agentic Workflow.** |

---

## 2. HỆ THỐNG SƠ ĐỒ KIẾN TRÚC & QUY TRÌNH TÁC TỬ (DIAGRAMS)

### 2.1. Sơ đồ Kiến trúc Tổng thể Hệ thống (System Architecture)

```mermaid
graph TD
    subgraph ClientLayer ["1. Tầng Giao diện & Tương tác (Client Layer)"]
        UI["🖥️ Web Dashboard<br/>(Chat, ReAct Trace, Database & Diagram Viewer)"]
        CLI["💻 CLI Terminal<br/>(--interactive, --all, -q, --level, --max-loop)"]
    end

    subgraph AgenticCore ["2. Tầng Tác tử ReAct Agent (Level 3 Engine)"]
        Controller["🧠 ReAct Loop Controller<br/>(Thought ➔ Action ➔ Observation)"]
        LLM["🔌 LLM Provider Adapter<br/>(Google Gemini API 2.5 Flash / Exponential Backoff)"]
        CB["🛡️ Circuit Breaker Guard<br/>(Max Loop 1 - 5 Iterations Limit)"]
        Controller <--> LLM
        Controller --> CB
    end

    subgraph MCPProtocol ["3. Giao thức Model Context Protocol (MCP JSON-RPC 2.0)"]
        Server["🔌 MCPAcademicServer<br/>(src/mcp_server.py)"]
        Router["🔀 Tool Dispatch Router<br/>(src/tools.py)"]
        Server --> Router
    end

    subgraph ToolSuite ["4. Bộ Công cụ MCP Đào tạo VinUni (4 Native Tools)"]
        T1["📋 academic_query<br/>(Tra cứu hồ sơ & GPA sinh viên)"]
        T2["🎓 check_scholarship_eligibility<br/>(Xét học bổng Dean's List / Tài năng)"]
        T3["📚 check_course_eligibility<br/>(Thẩm định điều kiện tiên quyết môn)"]
        T4["📅 schedule_appointment<br/>(Đặt lịch hẹn với Cố vấn học tập)"]
        Router --> T1
        Router --> T2
        Router --> T3
        Router --> T4
    end

    subgraph StorageLayer ["5. Cơ sở Dữ liệu Đào tạo VinUni (Data Layer)"]
        DB_Students[("👥 Student Records DB<br/>(2A202602735, SV2026001 - 005)")]
        DB_Courses[("📖 Courses Catalog DB<br/>(COMP3020, AI4010, MED2030)")]
        T1 & T2 & T4 --> DB_Students
        T3 --> DB_Courses
    end

    UI --> Controller
    CLI --> Controller
    Controller -- "call_tool(name, args)" --> Server
    Server -- "jsonrpc 2.0 result" --> Controller
```

---

### 2.2. Sơ đồ Luồng Thực thi Đa bước (Multi-step Waterfall Sequence Diagram - TC06)

```mermaid
sequenceDiagram
    autonumber
    actor SinhVien as 👤 Sinh viên (Tuấn Anh 2A202602735)
    participant Agent as 🤖 ReAct Agent (src/app.py)
    participant MCP as 🔌 MCP Server (src/mcp_server.py)
    participant Tools as 🛠️ VinUni Tools (src/tools.py)
    participant LLM as 🧠 Gemini LLM (Google API)

    SinhVien->>Agent: "Tra cứu hồ sơ 2A202602735, xét học bổng Dean's List, và đặt lịch hẹn cố vấn lúc 14:00 ngày 20/09/2026"
    
    rect rgb(235, 248, 255)
    Note over Agent,LLM: Vòng 1: Tra cứu hồ sơ & Nhận diện Cố vấn học tập
    Agent->>LLM: Gửi Prompt + Danh sách 4 MCP Tools Schema
    LLM-->>Agent: Action Proposed: academic_query(student_id="2A202602735")
    Agent->>MCP: call_tool("academic_query", {"student_id": "2A202602735"})
    MCP->>Tools: execute_academic_query("2A202602735")
    Tools-->>MCP: {status: "SUCCESS", gpa: 3.92, advisor: "GS.TS Vũ Hà Văn"}
    MCP-->>Agent: JSON-RPC 2.0 (Observation 1)
    end

    rect rgb(255, 250, 235)
    Note over Agent,LLM: Vòng 2: Thẩm định Tiêu chuẩn Học bổng Dean's List
    Agent->>LLM: Gửi Prompt tiếp nối + Observation 1
    LLM-->>Agent: Action Proposed: check_scholarship_eligibility(student_id="2A202602735", scholarship_type="DEANS_LIST")
    Agent->>MCP: call_tool("check_scholarship_eligibility", {...})
    MCP->>Tools: execute_scholarship_eligibility(...)
    Tools-->>MCP: {status: "SUCCESS", is_eligible: true, award: "Dean's List", gpa: 3.92}
    MCP-->>Agent: JSON-RPC 2.0 (Observation 2)
    end

    rect rgb(235, 255, 240)
    Note over Agent,LLM: Vòng 3: Tự động Đặt lịch hẹn Cố vấn học tập
    Agent->>LLM: Gửi Prompt tiếp nối + Observation 1 & 2
    LLM-->>Agent: Action Proposed: schedule_appointment(student_id="2A202602735", datetime="14:00 20/09/2026", advisor="GS.TS Vũ Hà Văn")
    Agent->>MCP: call_tool("schedule_appointment", {...})
    MCP->>Tools: execute_schedule_appointment(...)
    Tools-->>MCP: {status: "SUCCESS", booking_id: "BK-2A202602735-99"}
    MCP-->>Agent: JSON-RPC 2.0 (Observation 3)
    end

    rect rgb(245, 240, 255)
    Note over Agent,LLM: Vòng 4: Tổng hợp Phản hồi Hoàn chỉnh (Final Answer)
    Agent->>LLM: Synthesis Prompt + Toàn bộ 3 Observations
    LLM-->>Agent: Câu trả lời tự nhiên, thân thiện và chính xác
    Agent-->>SinhVien: Trả lời kết quả GPA 3.92, đạt Dean's List & Xác nhận lịch hẹn thành công
    end
```

---

## 3. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (TEST CASE ĐA BƯỚC TC06)

Dán trích xuất chuỗi 3 bước liên hoàn thực tế từ file `docs/trace_waterfall.json`:

```json
[
  {
    "step": 1,
    "query": "Hãy tra cứu học vụ của sinh viên 2A202602735, xét xem sinh viên có đủ điều kiện nhận Học bổng Dean's List không, và đặt lịch hẹn tư vấn với cố vấn học tập của sinh viên vào lúc 14:00 ngày 20/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "academic_query",
    "arguments": {
      "student_id": "2A202602735"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "2A202602735",
      "data": {
        "full_name": "Nguyễn Đình Tuấn Anh",
        "class": "AI-K4B",
        "gpa": 3.92,
        "email": "anh.ndt@vinuni.edu.vn",
        "status": "Đang học",
        "advisor": "GS.TS Vũ Hà Văn",
        "credits_completed": 105,
        "completed_courses": ["COMP1010", "COMP2010", "MATH1020", "COMP3020"],
        "disciplinary_record": "Xuất sắc"
      }
    },
    "latency_ms": 12.5
  },
  {
    "step": 2,
    "query": "Hãy tra cứu học vụ của sinh viên 2A202602735, xét xem sinh viên có đủ điều kiện nhận Học bổng Dean's List không, và đặt lịch hẹn tư vấn với cố vấn học tập của sinh viên vào lúc 14:00 ngày 20/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "check_scholarship_eligibility",
    "arguments": {
      "student_id": "2A202602735",
      "scholarship_type": "DEANS_LIST"
    },
    "observation": {
      "status": "SUCCESS",
      "student_id": "2A202602735",
      "student_name": "Nguyễn Đình Tuấn Anh",
      "scholarship_type": "DEANS_LIST",
      "is_eligible": true,
      "award_level": "Danh sách Danh dự Dean's List (Khen thưởng Viện trưởng)",
      "current_gpa": 3.92,
      "disciplinary_record": "Xuất sắc",
      "message": "Sinh viên Nguyễn Đình Tuấn Anh (GPA 3.92, Điểm rèn luyện: Xuất sắc) ĐẠT tiêu chuẩn Dean's List."
    },
    "latency_ms": 11.2
  },
  {
    "step": 3,
    "query": "Hãy tra cứu học vụ của sinh viên 2A202602735, xét xem sinh viên có đủ điều kiện nhận Học bổng Dean's List không, và đặt lịch hẹn tư vấn với cố vấn học tập của sinh viên vào lúc 14:00 ngày 20/09/2026.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "schedule_appointment",
    "arguments": {
      "student_id": "2A202602735",
      "datetime_str": "14:00 20/09/2026",
      "advisor_name": "GS.TS Vũ Hà Văn"
    },
    "observation": {
      "status": "SUCCESS",
      "booking_id": "BK-2A202602735-99",
      "student_id": "2A202602735",
      "datetime": "14:00 20/09/2026",
      "advisor": "GS.TS Vũ Hà Văn",
      "message": "Đặt lịch thành công cho sinh viên 2A202602735 với GS.TS Vũ Hà Văn vào lúc 14:00 20/09/2026."
    },
    "latency_ms": 10.8
  },
  {
    "step": 4,
    "query": "Hãy tra cứu học vụ của sinh viên 2A202602735, xét xem sinh viên có đủ điều kiện nhận Học bổng Dean's List không, và đặt lịch hẹn tư vấn với cố vấn học tập của sinh viên vào lúc 14:00 ngày 20/09/2026.",
    "action_type": "FINAL_ANSWER",
    "thought": "Tổng hợp kết quả từ 3 bước gọi tool MCP Server thành công.",
    "output": "Sinh viên 2A202602735 (Nguyễn Đình Tuấn Anh): Lớp AI-K4B, GPA: 3.92, Cố vấn: GS.TS Vũ Hà Văn.\nSinh viên Nguyễn Đình Tuấn Anh (GPA 3.92, Điểm rèn luyện: Xuất sắc) ĐẠT tiêu chuẩn Dean's List.\nĐặt lịch thành công cho sinh viên 2A202602735 với GS.TS Vũ Hà Văn vào lúc 14:00 20/09/2026.",
    "latency_ms": 10.0
  }
]
```

---

## 4. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] **Hệ thống 4 MCP Tools hoàn chỉnh:** `academic_query`, `schedule_appointment`, `check_course_eligibility`, `check_scholarship_eligibility`.
- [x] **Bộ 3 Sơ đồ Kiến trúc & Luồng Tác tử (Diagrams):** Đã trực quan hóa bằng Mermaid trong báo cáo và tích hợp tab Diagram trên Giao diện Web.
- [x] **Bộ Test Cases nâng cao (8/8 Test Cases):** Hoàn thành từ TC01 đến TC08 (bao gồm các ca kiểm thử đa bước Long-Horizon 3-4 bước).
- [x] **Bộ chuyển đổi Cấp 2 / Cấp 3 & Circuit Breaker (Max Loop 1 - 5):** Hoạt động chính xác trên cả CLI và Web UI.
- [x] **Quan sát học sâu (Trace Waterfall Log):** Đã ghi vết chi tiết vào `docs/trace_waterfall.json`.
- [x] **Kết quả đẩy Repo nộp bài:** Mã nguồn đã sẵn sàng commit & push lên GitHub cá nhân.

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân `https://github.com/tuananhdayne/K4B-DAY03-NguyenDinhTuanAnh-2A202602735` và nộp lên hệ thống LMS VLearn!
