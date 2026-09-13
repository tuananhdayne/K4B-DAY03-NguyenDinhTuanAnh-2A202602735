"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
"""

import json
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Đã được định nghĩa mẫu sẵn cho Học viên tham khảo
    {
        "name": "academic_query",
        "description": "Tra cứu hồ sơ và thông tin học vụ của sinh viên VinUni bằng mã sinh viên.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần tra cứu (ví dụ: 'SV2026001')"
                }
            },
            "required": ["student_id"]
        }
    },
    
    # --------------------------------------------------------------------------
    # TODO 1.2: HỌC VIÊN HOÀN THIỆN TOOL SCHEMA CHO 'schedule_appointment'
    # 🎯 YÊU CẦU THIẾT KẾ SCHEMA (JSON SCHEMA STANDARD):
    # 1. Tool dùng để đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.
    # 2. Thiết kế các tham số (properties) để LLM trích xuất:
    #    - student_id (string): Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')
    #    - datetime_str (string): Thời gian hẹn (ví dụ: '14:00 15/09/2026')
    #    - advisor_name (string): Tên cố vấn học tập
    # 3. Khai báo danh sách các trường bắt buộc (required).
    # --------------------------------------------------------------------------
    {
        "name": "schedule_appointment",
        "description": "Đặt lịch hẹn tư vấn học vụ với Cố vấn học tập VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần đặt lịch (ví dụ: 'SV2026001')"
                },
                "datetime_str": {
                    "type": "string",
                    "description": "Thời gian hẹn, ví dụ: '14:00 15/09/2026'"
                },
                "advisor_name": {
                    "type": "string",
                    "description": "Tên cố vấn học tập cần đặt lịch"
                }
            },
            "required": ["student_id", "datetime_str", "advisor_name"]
        }
    },

    # Tool 3: Kiểm tra điều kiện tiên quyết môn học & học phần VinUni
    {
        "name": "check_course_eligibility",
        "description": "Kiểm tra điều kiện tiên quyết (prerequisites), số tín chỉ và tính khả dụng để đăng ký môn học tại VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần kiểm tra điều kiện (ví dụ: '2A202602735' hoặc 'SV2026001')"
                },
                "course_code": {
                    "type": "string",
                    "description": "Mã môn học cần đăng ký (ví dụ: 'COMP3020', 'AI4010', 'MED2030')"
                }
            },
            "required": ["student_id", "course_code"]
        }
    },

    # Tool 4: Thẩm định và xét duyệt điều kiện nhận Học bổng VinUni & Dean's List
    {
        "name": "check_scholarship_eligibility",
        "description": "Thẩm định tiêu chuẩn và xét điều kiện nhận Học bổng Tài năng (Talent Scholarship) hoặc Danh sách Danh dự Dean's List VinUni.",
        "parameters": {
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "string",
                    "description": "Mã sinh viên cần xét học bổng (ví dụ: '2A202602735' hoặc 'SV2026001')"
                },
                "scholarship_type": {
                    "type": "string",
                    "description": "Loại học bổng cần xét: 'DEANS_LIST', 'TALENT_SCHOLARSHIP', hoặc 'NEED_BASED'",
                    "enum": ["DEANS_LIST", "TALENT_SCHOLARSHIP", "NEED_BASED"]
                }
            },
            "required": ["student_id", "scholarship_type"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER - SSOT)
# ==============================================================================

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_JSON_PATH = os.path.join(BASE_DIR, "data", "mock_database.json")
WEB_JS_PATH = os.path.join(BASE_DIR, "web", "data.js")

def load_unified_database():
    """Tải cơ sở dữ liệu học vụ từ Single Source of Truth (data/mock_database.json)"""
    if os.path.exists(DB_JSON_PATH):
        try:
            with open(DB_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("students", {}), data.get("courses", {}), data.get("scholarships", {})
        except Exception as e:
            print(f"⚠️ [DATABASE ERROR]: Không thể đọc {DB_JSON_PATH}: {e}")
    return {}, {}, {}

def sync_database_to_web():
    """Tự động đồng bộ Single Source of Truth sang web/data.js để frontend luôn nhất quán 100%"""
    if os.path.exists(DB_JSON_PATH):
        try:
            with open(DB_JSON_PATH, "r", encoding="utf-8") as f:
                db_data = json.load(f)
            os.makedirs(os.path.dirname(WEB_JS_PATH), exist_ok=True)
            with open(WEB_JS_PATH, "w", encoding="utf-8") as f:
                f.write("// 📦 AUTO-GENERATED FROM data/mock_database.json (SINGLE SOURCE OF TRUTH)\n")
                f.write("// DO NOT EDIT MANUALLY - EDIT data/mock_database.json INSTEAD\n")
                f.write("window.VINUNI_DATABASE = ")
                json.dump(db_data, f, ensure_ascii=False, indent=2)
                f.write(";\n")
        except Exception as e:
            print(f"⚠️ [DATABASE SYNC WARNING]: Lỗi đồng bộ web/data.js: {e}")

# Khởi tạo Single Source of Truth
MOCK_DATABASE, MOCK_COURSES, MOCK_SCHOLARSHIPS = load_unified_database()
sync_database_to_web()


def execute_academic_query(student_id: str) -> str:
    """Thực thi tra cứu học vụ theo mã sinh viên"""
    student = MOCK_DATABASE.get(student_id.strip().upper())
    if student:
        return json.dumps({
            "status": "SUCCESS",
            "student_id": student_id,
            "data": student
        }, ensure_ascii=False)
    else:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy dữ liệu sinh viên có mã '{student_id}'"
        }, ensure_ascii=False)


def execute_schedule_appointment(student_id: str, datetime_str: str, advisor_name: str = "PGS.TS Nguyễn Văn A") -> str:
    """Thực thi đặt lịch hẹn tư vấn học vụ"""
    return json.dumps({
        "status": "SUCCESS",
        "booking_id": f"BK-{student_id}-99",
        "student_id": student_id,
        "datetime": datetime_str,
        "advisor": advisor_name,
        "message": f"Đặt lịch thành công cho sinh viên {student_id} với {advisor_name} vào lúc {datetime_str}."
    }, ensure_ascii=False)


def execute_course_eligibility(student_id: str, course_code: str) -> str:
    """Thực thi kiểm tra điều kiện tiên quyết và tính khả dụng của môn học"""
    s_id = student_id.strip().upper()
    c_code = course_code.strip().upper()
    student = MOCK_DATABASE.get(s_id)
    if not student:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy sinh viên có mã '{student_id}' để kiểm tra điều kiện môn học."
        }, ensure_ascii=False)
    
    course = MOCK_COURSES.get(c_code)
    if not course:
        return json.dumps({
            "status": "COURSE_NOT_FOUND",
            "message": f"Không tìm thấy học phần có mã '{course_code}' trong danh mục môn học VinUni."
        }, ensure_ascii=False)
    
    completed_courses = student.get("completed_courses", [])
    missing_prereqs = [p for p in course.get("prerequisites", []) if p not in completed_courses]
    min_gpa = course.get("min_gpa", 0.0)
    gpa_pass = student.get("gpa", 0.0) >= min_gpa
    min_credits = course.get("min_credits", 0)
    credits_pass = student.get("credits_completed", 0) >= min_credits
    slots = course.get("available_slots", 0)
    slot_available = slots > 0
    
    is_eligible = (len(missing_prereqs) == 0) and gpa_pass and credits_pass and slot_available
    
    reasons = []
    if missing_prereqs:
        reasons.append(f"Chưa hoàn thành môn tiên quyết: {', '.join(missing_prereqs)}")
    if not gpa_pass:
        reasons.append(f"GPA hiện tại ({student.get('gpa')}) chưa đạt yêu cầu tối thiểu ({min_gpa})")
    if not credits_pass:
        reasons.append(f"Số tín chỉ tích lũy ({student.get('credits_completed')}) chưa đủ ({min_credits} tín chỉ)")
    if not slot_available:
        reasons.append("Lớp học phần đã hết chỗ")

    return json.dumps({
        "status": "SUCCESS",
        "student_id": s_id,
        "student_name": student.get("full_name"),
        "course_code": c_code,
        "course_name": course.get("name"),
        "instructor": course.get("instructor"),
        "credits": course.get("credits"),
        "is_eligible": is_eligible,
        "available_slots": slots,
        "missing_prerequisites": missing_prereqs,
        "details": "Đủ điều kiện đăng ký môn học này." if is_eligible else "Không đủ điều kiện: " + "; ".join(reasons)
    }, ensure_ascii=False)


def execute_scholarship_eligibility(student_id: str, scholarship_type: str = "DEANS_LIST") -> str:
    """Thực thi thẩm định tiêu chuẩn học bổng sinh viên VinUni"""
    s_id = student_id.strip().upper()
    student = MOCK_DATABASE.get(s_id)
    if not student:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy sinh viên có mã '{student_id}' để xét học bổng."
        }, ensure_ascii=False)
    
    gpa = student.get("gpa", 0.0)
    credits_completed = student.get("credits_completed", 0)
    disc = student.get("disciplinary_record", "Tốt")
    stype = scholarship_type.strip().upper()

    if stype == "TALENT_SCHOLARSHIP":
        if gpa >= 3.85 and credits_completed >= 60:
            eligible = True
            level = "Học bổng Tài năng VinUni Toàn phần (100% Học phí)"
            msg = f"Sinh viên {student.get('full_name')} (GPA {gpa}) ĐỦ ĐIỀU KIỆN nhận {level}."
        elif gpa >= 3.75:
            eligible = True
            level = "Học bổng Tài năng Bán phần (50% Học phí)"
            msg = f"Sinh viên {student.get('full_name')} (GPA {gpa}) ĐỦ ĐIỀU KIỆN nhận {level}."
        else:
            eligible = False
            level = "Không đạt"
            msg = f"Sinh viên {student.get('full_name')} có GPA {gpa} (yêu cầu tối thiểu 3.75 cho Học bổng Tài năng)."
    else:  # DEANS_LIST
        if gpa >= 3.70 and disc in ["Tốt", "Xuất sắc"]:
            eligible = True
            level = "Danh sách Danh dự Dean's List (Khen thưởng Viện trưởng)"
            msg = f"Sinh viên {student.get('full_name')} (GPA {gpa}, Điểm rèn luyện: {disc}) ĐẠT tiêu chuẩn Dean's List."
        else:
            eligible = False
            level = "Chưa đạt"
            msg = f"Sinh viên {student.get('full_name')} có GPA {gpa} (yêu cầu Dean's List là GPA >= 3.70)."

    return json.dumps({
        "status": "SUCCESS",
        "student_id": s_id,
        "student_name": student.get("full_name"),
        "scholarship_type": stype,
        "is_eligible": eligible,
        "award_level": level,
        "current_gpa": gpa,
        "disciplinary_record": disc,
        "message": msg
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "academic_query": execute_academic_query,
    "schedule_appointment": execute_schedule_appointment,
    "check_course_eligibility": execute_course_eligibility,
    "check_scholarship_eligibility": execute_scholarship_eligibility
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
