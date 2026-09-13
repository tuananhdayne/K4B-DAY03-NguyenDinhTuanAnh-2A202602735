"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import re
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        prompt_lower = prompt.lower()
        if "mcp server" in prompt_lower or "dữ liệu thực tế" in prompt_lower or "tác tử học vụ vinuni" in prompt_lower:
            return ""

        if any(k in prompt_lower for k in ("sv", "2a", "gpa", "điểm", "học vụ", "cố vấn", "đặt lịch")):
            return (
                "Chào bạn! Tôi là Chatbot học vụ thuộc Đại học VinUni (Cấp 2 Baseline). "
                "Xin lưu ý rằng tôi KHÔNG có quyền truy cập vào cơ sở dữ liệu học vụ thời gian thực và "
                "KHÔNG có quyền đặt lịch hẹn. Tôi không thể tra cứu thông tin sinh viên hoặc đặt lịch tư vấn. "
                "Bạn vui lòng liên hệ trực tiếp phòng Đào tạo (Registrar Office) để được hỗ trợ."
            )
        return "Chào bạn! Tôi là Chatbot học vụ VinUni. Về quy chế cơ bản: Sinh viên cần hoàn thành từ 120-135 tín chỉ theo hệ thống ECTS và duy trì GPA tối thiểu 2.0 để tốt nghiệp."

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        student_match = re.search(r"\b(?:SV\d+|2A\d+)\b", prompt, re.IGNORECASE)
        student_id = student_match.group(0).upper() if student_match else "SV2026001"
        time_match = re.search(r"\b\d{1,2}:\d{2}\b", prompt)
        date_match = re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", prompt)
        datetime_str = (
            f"{time_match.group(0)} {date_match.group(0)}"
            if time_match and date_match
            else "14:00 20/09/2026"
        )
        advisor_name = next(
            (
                name
                for name in (
                    "GS.TS Vũ Hà Văn",
                    "PGS.TS Nguyễn Văn A", 
                    "TS. Lê Thị B", 
                    "TS. Phạm Bảo Sơn", 
                    "GS. Maurizio Cecconi", 
                    "PGS.TS Sunita Sah"
                )
                if name.lower() in prompt_lower
            ),
            None
        ) or ("GS.TS Vũ Hà Văn" if "2A202602735" in student_id else "PGS.TS Nguyễn Văn A")

        # Khai thác course code nếu có trong prompt
        course_match = re.search(r"\b(COMP3020|AI4010|MED2030|COMP2010|MATH1020)\b", prompt, re.IGNORECASE)
        course_code = course_match.group(0).upper() if course_match else "COMP3020"

        # Khai thác loại học bổng nếu có
        scholarship_type = "TALENT_SCHOLARSHIP" if ("tài năng" in prompt_lower or "talent" in prompt_lower) else "DEANS_LIST"

        # Kiểm tra lịch sử đã gọi các tools nào từ chuỗi JSON observations_history trong prompt
        has_academic_obs = '"tool": "academic_query"' in prompt or "'tool': 'academic_query'" in prompt
        has_scholarship_obs = '"tool": "check_scholarship_eligibility"' in prompt or "'tool': 'check_scholarship_eligibility'" in prompt
        has_course_obs = '"tool": "check_course_eligibility"' in prompt or "'tool': 'check_course_eligibility'" in prompt
        has_booking_obs = '"tool": "schedule_appointment"' in prompt or "'tool': 'schedule_appointment'" in prompt

        # Xử lý chuỗi Multi-step & Task Detection
        needs_academic = "tra cứu" in prompt_lower or "hồ sơ" in prompt_lower or "thông tin học vụ" in prompt_lower
        needs_scholarship = "học bổng" in prompt_lower or "dean's list" in prompt_lower
        needs_course = "tiên quyết" in prompt_lower or "môn" in prompt_lower or "đồ án" in prompt_lower or bool(course_match)
        needs_booking = "đặt lịch" in prompt_lower or "lịch tư vấn" in prompt_lower or "hẹn" in prompt_lower

        if needs_academic and not has_academic_obs:
            return {
                "type": "tool_call",
                "tool_name": "academic_query",
                "arguments": {"student_id": student_id},
                "thought": f"Tôi cần tra cứu hồ sơ học vụ của sinh viên {student_id} trước."
            }

        if needs_scholarship and not has_scholarship_obs:
            return {
                "type": "tool_call",
                "tool_name": "check_scholarship_eligibility",
                "arguments": {"student_id": student_id, "scholarship_type": scholarship_type},
                "thought": f"Tôi tiến hành thẩm định điều kiện học bổng {scholarship_type} cho sinh viên {student_id}."
            }

        if needs_course and not has_course_obs and ("đăng ký" in prompt_lower or "tiên quyết" in prompt_lower or "đồ án" in prompt_lower or "nguyện vọng" in prompt_lower):
            return {
                "type": "tool_call",
                "tool_name": "check_course_eligibility",
                "arguments": {"student_id": student_id, "course_code": course_code},
                "thought": f"Tôi kiểm tra điều kiện tiên quyết và tính khả dụng của môn {course_code} cho sinh viên {student_id}."
            }

        if needs_booking and not has_booking_obs:
            return {
                "type": "tool_call",
                "tool_name": "schedule_appointment",
                "arguments": {"student_id": student_id, "datetime_str": datetime_str, "advisor_name": advisor_name},
                "thought": f"Tất cả các điều kiện đã được xác minh. Tôi tiến hành đặt lịch hẹn tư vấn cho {student_id} với {advisor_name}."
            }

        if not (needs_academic or needs_scholarship or needs_course or needs_booking):
            return {
                "type": "text",
                "content": "[Mock Agent Response]: Xin chào! Tôi là Trợ lý Học vụ VinUni. Về quy chế cơ bản: Sinh viên cần hoàn thành tối thiểu 120 tín chỉ và duy trì GPA tối thiểu 2.0 để tốt nghiệp.",
                "thought": "Câu hỏi chung về quy chế học vụ, trả lời trực tiếp không cần gọi Tool."
            }

        return {
            "type": "text",
            "content": f"Đã hoàn tất toàn bộ quy trình xử lý cho sinh viên {student_id} qua MCP Server.",
            "thought": "Tất cả các bước yêu cầu đã được thực thi thành công. Xuất Final Answer."
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        from google import genai
        client = genai.Client(api_key=self.api_key)
        contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        for attempt in range(3):
            try:
                response = client.models.generate_content(model=self.model_name, contents=contents)
                return response.text or ""
            except Exception as e:
                err_msg = str(e)
                if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg) and attempt < 2:
                    wait_sec = 2.5 * (attempt + 1)
                    time.sleep(wait_sec)
                    continue
                print(f"⚠️ [Gemini API Note]: {err_msg[:60]}... Fallback về phản hồi Cấp 2.")
                return MockOfflineProvider().generate(prompt, system_prompt)
        return MockOfflineProvider().generate(prompt, system_prompt)

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)
        
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            
            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            response = None
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=config
                    )
                    break
                except Exception as api_err:
                    err_msg = str(api_err)
                    if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg) and attempt < 2:
                        wait_sec = 3.0 * (attempt + 1)
                        print(f"⏳ [Gemini Rate-Limit]: Chờ {wait_sec}s rồi thử lại với Gemini...")
                        time.sleep(wait_sec)
                        continue
                    raise api_err

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response and response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": (response.text if response else "") or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, prompt: str, tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(prompt, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()
    
    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
