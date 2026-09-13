"""
🚀 CORE AGENT APPLICATION (DAY 03: CHATBOT VS REACT AGENT)
Thực thi so sánh giữa Chatbot Baseline (Cấp 2) và ReAct Agent kết nối MCP Server (Cấp 3).
"""

import json
import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from mcp_server import MCPAcademicServer
from prompts import (
    CHATBOT_BASELINE_PROMPT,
    REACT_AGENT_SYSTEM_PROMPT,
    MAX_ITERATIONS
)
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Tải danh sách 5 test cases từ config/test_cases.json hoặc config/test_cases.example.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        example_path = os.path.join(base_dir, "config", "test_cases.example.json")
        if os.path.exists(example_path):
            print("⚠️ [CONFIG NOTICE]: Chưa thấy file 'config/test_cases.json'. Đang dùng mẫu 'config/test_cases.example.json'.")
            print("👉 Hãy chạy: copy config/test_cases.example.json config/test_cases.json và viết test cases theo đề tài của bạn!\n")
            config_path = example_path
        else:
            config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_waterfall_trace(trace_data: list):
    """Ghi vết log Waterfall Trace Log ra file docs/trace_waterfall.json"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "docs")
    os.makedirs(docs_dir, exist_ok=True)
    trace_path = os.path.join(docs_dir, "trace_waterfall.json")
    with open(trace_path, "w", encoding="utf-8") as f:
        json.dump(trace_data, f, ensure_ascii=False, indent=2)
    print(f"📊 [OBSERVABILITY]: Đã lưu {len(trace_data)} sự kiện Waterfall Trace tại '{trace_path}'!")


def run_baseline_chatbot(user_query: str, provider) -> list:
    """Chạy Chatbot gốc (Cấp 2) không có công cụ gọi Tool"""
    print(f"\n💬 [CHATBOT BASELINE - CẤP 2] Câu hỏi: {user_query}")
    start_time = time.time()
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    latency_ms = round((time.time() - start_time) * 1000, 2)
    print(f"🤖 Chatbot Cấp 2 phản hồi:\n{response}")
    return [{
        "step": 1,
        "query": user_query,
        "action_type": "BASELINE_TEXT_ONLY",
        "thought": "Hệ thống Cấp 2 (Chatbot Baseline): Không có Tool hay giao thức MCP. Chỉ dùng System Prompt tĩnh.",
        "output": response,
        "latency_ms": latency_ms
    }]


def run_react_agent(user_query: str, provider, mcp_server, max_iterations: int = None) -> list:
    """
    [REACT AGENT LOOP] Thực thi vòng lặp Thought -> Action -> Observation với MCP Server
    Có cơ chế Max Loop (Circuit Breaker) chống lặp vô tận.
    Trả về danh sách trace log của phiên thực thi.
    """
    if max_iterations is None:
        try:
            max_iterations = int(os.getenv("MAX_ITERATIONS", MAX_ITERATIONS))
        except (ValueError, TypeError):
            max_iterations = MAX_ITERATIONS

    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query} (Max Loop: {max_iterations})")
    
    step = 0
    trace_logs = []
    observations_history = []
    executed_tools = []
    tools_list = mcp_server.list_tools()
    request_prompt = user_query
    
    while step < max_iterations:
        step += 1
        step_start_time = time.time()
        print(f"\n--- 🔄 Vòng lặp ReAct Loop (Step {step}/{max_iterations}) ---")
        
        # Gọi LLM với Native Tool Calling Specs
        llm_response = provider.generate_with_tools(request_prompt, tools_list, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
        latency_ms = round((time.time() - step_start_time) * 1000, 2)
        
        thought = llm_response.get("thought", "Đang suy luận...")
        print(f"🧠 [Thought]: {thought}")
        
        # Trường hợp 1: LLM quyết định trả lời bằng văn bản trực tiếp
        if llm_response.get("type") == "text":
            final_content = llm_response.get("content", "")
            print(f"🏁 [Final Answer]: {final_content}")
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": thought,
                "output": final_content,
                "latency_ms": latency_ms
            })
            break
            
        # Trường hợp 2: LLM đề xuất gọi Tool (Action)
        elif llm_response.get("type") == "tool_call":
            tool_name = llm_response.get("tool_name")
            arguments = llm_response.get("arguments", {})
            
            print(f"🛠️ [Action Proposed]: {tool_name}({arguments})")
            
            # Thực thi Tool qua MCP Server
            mcp_result = mcp_server.call_tool(tool_name, arguments)
            obs_data = mcp_result.get("result", {})
            
            trace_logs.append({
                "step": step,
                "query": user_query,
                "action_type": "TOOL_EXECUTION",
                "tool_name": tool_name,
                "arguments": arguments,
                "observation": obs_data,
                "latency_ms": latency_ms
            })
            
            executed_tools.append(tool_name)
            observations_history.append({
                "tool": tool_name,
                "arguments": arguments,
                "observation": obs_data
            })

            if not obs_data:
                print(f"👁️ [Observation từ MCP Server]: {{}}")
                print(f"⚠️ [CHÚ Ý]: MCP Server trả về kết quả rỗng!")
            else:
                obs_str = json.dumps(obs_data, ensure_ascii=False)
                print(f"👁️ [Observation từ MCP Server]: {obs_str}")

            # Kiểm tra xem có cần tiếp tục chuỗi Multi-step hay không
            q_lower = user_query.lower()
            needs_scholarship = ("học bổng" in q_lower or "dean's list" in q_lower) and "check_scholarship_eligibility" not in executed_tools
            needs_course = ("môn" in q_lower or "tiên quyết" in q_lower or "đồ án" in q_lower) and "check_course_eligibility" not in executed_tools
            needs_booking = any(p in q_lower for p in ("đặt lịch", "lịch tư vấn", "đặt hẹn", "hẹn")) and "schedule_appointment" not in executed_tools

            # Nếu sinh viên không tồn tại thì dừng ngay
            if obs_data.get("status") == "NOT_FOUND":
                needs_scholarship = False
                needs_course = False
                needs_booking = False

            if (needs_scholarship or needs_course or needs_booking) and step < max_iterations:
                # Tìm tên cố vấn từ bước tra cứu sinh viên trước đó nếu có
                advisor_name = "PGS.TS Nguyễn Văn A"
                for o in observations_history:
                    if o["tool"] == "academic_query" and o["observation"].get("status") == "SUCCESS":
                        advisor_name = o["observation"].get("data", {}).get("advisor", advisor_name)

                request_prompt = (
                    f"Yêu cầu ban đầu của người dùng: {user_query}\n"
                    f"Lịch sử thực thi các bước trước: {json.dumps(observations_history, ensure_ascii=False)}\n"
                    f"Cố vấn học tập được xác nhận: {advisor_name}\n"
                    f"Hãy tiếp tục thực hiện bước tiếp theo còn lại trong yêu cầu."
                )
                print(f"🧠 [Thought]: Còn tác vụ tiếp theo trong chuỗi yêu cầu. Tiếp tục vòng lặp ReAct...")
                time.sleep(1.2)
                continue

            # Tổng hợp Final Answer khi đã hoàn tất tất cả các bước
            fallback_parts = []
            for item in observations_history:
                t = item["tool"]
                o = item["observation"]
                if t == "academic_query":
                    if o.get("status") == "SUCCESS" and "data" in o:
                        d = o["data"]
                        fallback_parts.append(
                            f"Sinh viên {o.get('student_id')} ({d.get('full_name')}): Lớp {d.get('class')}, "
                            f"GPA: {d.get('gpa')}, Cố vấn: {d.get('advisor')}."
                        )
                    elif o.get("status") == "NOT_FOUND":
                        fallback_parts.append(o.get("message", "Không tìm thấy sinh viên."))
                elif t == "check_scholarship_eligibility":
                    fallback_parts.append(o.get("message", "Đã kiểm tra học bổng."))
                elif t == "check_course_eligibility":
                    status_text = "Đủ điều kiện" if o.get("is_eligible") else "Chưa đủ điều kiện"
                    fallback_parts.append(f"Môn {o.get('course_code')} ({o.get('course_name')}): {status_text}. {o.get('details')}")
                elif t == "schedule_appointment":
                    fallback_parts.append(o.get("message", "Đã đặt lịch hẹn."))
                else:
                    fallback_parts.append(json.dumps(o, ensure_ascii=False))

            fallback_answer = "\n".join(fallback_parts)

            summary_prompt = (
                f"Câu hỏi ban đầu của sinh viên: {user_query}\n"
                f"Dữ liệu thực tế từ MCP Server qua các bước:\n"
                f"{json.dumps(observations_history, ensure_ascii=False, indent=2)}\n\n"
                f"Hãy đóng vai Trợ lý Tác tử Học vụ VinUni, sử dụng dữ liệu trên để trả lời sinh viên một cách tự nhiên, "
                f"chính xác, thân thiện và đầy đủ tất cả các ý trong câu hỏi. Tuyệt đối không bịa đặt thêm dữ liệu."
            )
            try:
                gemini_text = provider.generate(summary_prompt, system_prompt=REACT_AGENT_SYSTEM_PROMPT)
                if gemini_text and not gemini_text.startswith("[Gemini Error]") and not gemini_text.startswith("[Gemini Exception]"):
                    final_answer = gemini_text.strip()
                else:
                    final_answer = fallback_answer
            except Exception:
                final_answer = fallback_answer

            print(f"🧠 [Thought]: Đã nhận đủ dữ liệu từ MCP Server. Tổng hợp kết quả phản hồi.")
            print(f"🏁 [Final Answer]: {final_answer}")
            
            trace_logs.append({
                "step": step + 1,
                "query": user_query,
                "action_type": "FINAL_ANSWER",
                "thought": f"Tổng hợp kết quả từ {len(observations_history)} bước gọi tool MCP Server thành công.",
                "output": final_answer,
                "latency_ms": 10.0
            })
            break
    else:
        # Cơ chế Circuit Breaker khi vòng lặp chạm ngưỡng MAX_LOOP mà chưa có kết luận
        stop_msg = (
            f"⚠️ [CIRCUIT BREAKER - MAX LOOP REACHED]: Tác tử đã đạt giới hạn tối đa {max_iterations} vòng lặp ReAct. "
            f"Hệ thống tự động dừng để tránh lặp vô tận (Infinite Loop Guard) và bảo toàn tài nguyên token."
        )
        print(f"\n🛑 {stop_msg}")
        trace_logs.append({
            "step": step,
            "query": user_query,
            "action_type": "MAX_LOOP_TERMINATION",
            "thought": f"Đã chạm ngưỡng Max Loop = {max_iterations}. Kích hoạt ngắt mạch an toàn.",
            "output": stop_msg,
            "latency_ms": 0.0
        })

    return trace_logs


if __name__ == "__main__":
    print("==========================================================")
    print("🏫 VINUNI AI COURSE - DAY 03 LAB: CHATBOT VS REACT AGENT")
    print("==========================================================")
    
    provider = get_llm_provider()
    mcp_server = MCPAcademicServer()
    
    print(f"🔌 LLM Provider: {provider.__class__.__name__}")
    print(f"🌐 MCP Server: {mcp_server.server_name}\n")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases thử nghiệm.\n")

    # Phân tích tham số --level (Cấp 2: Chatbot | Cấp 3: ReAct Agent, mặc định là 3)
    cli_level = 3
    for idx, arg in enumerate(sys.argv):
        if arg in ["--level", "-lvl", "--ai-level"] and idx + 1 < len(sys.argv):
            if sys.argv[idx + 1] in ["2", "3"]:
                cli_level = int(sys.argv[idx + 1])
    current_level = cli_level

    # Phân tích tham số --max-loop từ dòng lệnh (mặc định 5, cho phép chọn từ 1 đến 5 hoặc hơn)
    cli_max_loop = None
    for idx, arg in enumerate(sys.argv):
        if arg in ["--max-loop", "--maxloop", "-l", "--max-iterations"] and idx + 1 < len(sys.argv):
            try:
                cli_max_loop = max(1, min(10, int(sys.argv[idx + 1])))
            except ValueError:
                pass
    
    current_max_loop = cli_max_loop or int(os.getenv("MAX_ITERATIONS", MAX_ITERATIONS))
    
    lvl_name = "Cấp 2: Chatbot Baseline (Không Tool)" if current_level == 2 else "Cấp 3: ReAct Agent (MCP-Enhanced)"
    print(f"🎚️ [AI LEVEL CONFIG]: Chế độ hoạt động = {lvl_name}")
    print(f"🛡️ [SAFETY CONFIG]: Max Loop Limit = {current_max_loop} iterations\n")
    
    query_arg = None
    for idx, arg in enumerate(sys.argv):
        if arg in ["-q", "--query"] and idx + 1 < len(sys.argv):
            query_arg = sys.argv[idx + 1]

    if query_arg:
        print(f"🎯 [QUERY MODE] Thực thi câu hỏi từ dòng lệnh:")
        if current_level == 2:
            logs = run_baseline_chatbot(query_arg, provider)
        else:
            logs = run_react_agent(query_arg, provider, mcp_server, max_iterations=current_max_loop)
        save_waterfall_trace(logs)
    elif "--interactive" in sys.argv:
        print("🎮 [INTERACTIVE MODE] Trò chuyện trực tiếp:")
        print("💡 Gợi ý câu lệnh & câu hỏi thử nghiệm:")
        print("   - Chuyển Cấp độ AI: gõ '/level 2' (Chatbot thuần) hoặc '/level 3' (ReAct Agent)")
        print("   - Đổi Max Loop (1 - 5): gõ '/maxloop 2' hoặc '/maxloop 3'")
        print("   - Câu hỏi chung: 'Quy chế học vụ VinUni yêu cầu bao nhiêu tín chỉ?'")
        print("   - Tra cứu học vụ: 'Hãy tra cứu thông tin học vụ của sinh viên 2A202602735'")
        print("   - Xét học bổng: 'Kiểm tra học bổng của sinh viên 2A202602735'")
        print("   - Đăng ký môn: 'Kiểm tra điều kiện học phần COMP3020 cho sinh viên 2A202602735'")
        print("   - Gõ 'exit' hoặc 'quit' để kết thúc phiên trò chuyện.\n")
        while True:
            try:
                user_input = input("👤 Sinh viên hỏi: ").strip()
                if not user_input or user_input.lower() in ["exit", "quit"]:
                    print("👋 Tạm biệt! Kết thúc phiên trò chuyện.")
                    break

                if user_input.lower().startswith("/level"):
                    parts = user_input.split()
                    if len(parts) >= 2 and parts[1] in ["2", "3"]:
                        current_level = int(parts[1])
                        print(f"🔄 Đã chuyển sang: {'Cấp 2: Chatbot Baseline' if current_level == 2 else 'Cấp 3: ReAct Agent'}")
                        continue

                if user_input.lower().startswith("/maxloop"):
                    parts = user_input.split()
                    if len(parts) >= 2:
                        try:
                            current_max_loop = max(1, min(10, int(parts[1])))
                            print(f"🔄 Đã cập nhật Max Loop: {current_max_loop}")
                        except ValueError:
                            print("⚠️ Vui lòng nhập số hợp lệ, ví dụ: /maxloop 3")
                        continue

                if current_level == 2:
                    logs = run_baseline_chatbot(user_input, provider)
                else:
                    logs = run_react_agent(user_input, provider, mcp_server, max_iterations=current_max_loop)
                save_waterfall_trace(logs)
                print("-" * 50)
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                break
    elif "--all" in sys.argv:
        print(f"🚀 [TEST SUITE MODE] Kiểm tra {len(tests)} Test Cases ({lvl_name} | Max Loop = {current_max_loop}):")
        completed_count = 0
        todo_count = 0
        all_traces = []
        
        for tc in tests:
            print(f"\n==================================================")
            print(f"🧪 [{tc['id']}] Loại test: {tc['type']} (Độ phức tạp: {tc['complexity']})")
            print(f"📌 Kỳ vọng: {tc['expected_behavior']}")
            
            if tc["question"].strip().startswith("TODO"):
                print(f"⏸️ [CHƯA KÍCH HOẠT - ĐANG LÀ TODO]:")
                print(f"   {tc['question']}")
                print(f"   👉 Hãy mở file 'config/test_cases.json' để viết câu hỏi thực tế cho Test Case này!")
                todo_count += 1
            else:
                if current_level == 2:
                    logs = run_baseline_chatbot(tc["question"], provider)
                else:
                    logs = run_react_agent(tc["question"], provider, mcp_server, max_iterations=current_max_loop)
                all_traces.extend(logs)
                completed_count += 1
                time.sleep(1.0)
                
        print(f"\n==================================================")
        print(f"📊 [KẾT QUẢ TEST SUITE]: Đã thực thi {completed_count}/{len(tests)} Test Cases | {todo_count} Test Cases đang chờ điền câu hỏi (TODO)")
        if all_traces:
            save_waterfall_trace(all_traces)
        print(f"💡 Để trò chuyện trực tiếp từng câu: Chạy 'python src/app.py --interactive'")
    else:
        # Chế độ mặc định khi chỉ gõ 'python src/app.py'
        print("ℹ️ HƯỚNG DẪN SỬ DỤNG CHƯƠNG TRÌNH:")
        print("  1. Chat trực tiếp liên tục:    python src/app.py --interactive")
        print("  2. Chọn Cấp độ (2 hoặc 3):      python src/app.py --level 2 --interactive")
        print("  3. Tùy chọn Max Loop (1-5):     python src/app.py --max-loop 2 --interactive")
        print("  4. Chạy toàn bộ Test Cases:     python src/app.py --all --level 3 --max-loop 5")
        print("  5. Chạy 1 câu hỏi cụ thể:       python src/app.py -q \"câu hỏi của bạn\"\n")
        
        sample_query = tests[1]["question"]
        if current_level == 2:
            logs = run_baseline_chatbot(sample_query, provider)
        else:
            logs = run_react_agent(sample_query, provider, mcp_server, max_iterations=current_max_loop)
        save_waterfall_trace(logs)
        print("\n💡 Hãy thử ngay lệnh: python src/app.py --interactive để chat trực tiếp!")
