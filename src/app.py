"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS
from prompts import (
    CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS,
    contains_crisis_signal, CRISIS_RESPONSE, is_valid_react_step, MALFORMED_OUTPUT_FALLBACK
)
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    
    # 1. Phanh cứng cấp code: Kiểm tra tín hiệu khủng hoảng ngay từ đầu
    if contains_crisis_signal(user_query):
        print("\n🛡️ GUARDRAIL TRIGGERED: Phát hiện tín hiệu khủng hoảng!")
        print(f"🏁 Final Answer: {CRISIS_RESPONSE}")
        return

    step = 0
    # Khởi tạo history với System Prompt và User Query
    history = REACT_SYSTEM_PROMPT + f"\nUser: {user_query}\n"
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM sinh suy luận/hành động
        response = provider.generate(history)
        print(f"{response}")
        
        # 2. Kiểm tra định dạng an toàn
        if not is_valid_react_step(response):
            print("\n🛡️ GUARDRAIL TRIGGERED: LLM sinh sai định dạng (thiếu Action/Final Answer).")
            print(f"🏁 Final Answer: {MALFORMED_OUTPUT_FALLBACK}")
            break
            
        history += response + "\n"
        
        # 3. Kiểm tra xem đã có Final Answer chưa
        if "Final Answer:" in response:
            print("\n✅ Agent đã tìm được câu trả lời cuối cùng.")
            break
            
        # 4. Parse Action và thực thi Tool
        import re
        action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", response, re.DOTALL)
        if action_match:
            tool_name = action_match.group(1).strip()
            tool_args_str = action_match.group(2).strip()
            
            print(f"\n🛠️ Đang gọi Tool: {tool_name} với tham số: {tool_args_str}")
            
            if tool_name in AVAILABLE_TOOLS:
                tool_func = AVAILABLE_TOOLS[tool_name]
                try:
                    # Parse tham số: nếu giống dict thì load json, nếu không truyền chuỗi
                    try:
                        args = json.loads(tool_args_str)
                        if isinstance(args, dict):
                            obs = tool_func(args)
                        else:
                            obs = tool_func(tool_args_str)
                    except json.JSONDecodeError:
                        obs = tool_func(tool_args_str)
                    
                    obs_str = f"Observation: {obs}"
                except Exception as e:
                    obs_str = f"Observation: LỖI KHI GỌI TOOL - {str(e)}"
            else:
                obs_str = f"Observation: LỖI - Tool '{tool_name}' không tồn tại. Vui lòng chọn trong {list(AVAILABLE_TOOLS.keys())}."
            
            print(f"👁️ {obs_str}")
            history += obs_str + "\n"
        else:
            obs_str = "Observation: Vui lòng cung cấp 'Action:' hợp lệ hoặc 'Final Answer:'."
            history += obs_str + "\n"
            
    if step >= MAX_ITERATIONS:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    if "--interactive" in sys.argv or "-i" in sys.argv:
        print("\n" + "="*50)
        print("🗣️ CHẾ ĐỘ CHAT TƯƠNG TÁC TRỰC TIẾP VỚI REACT AGENT")
        print("Nhập 'exit' hoặc 'quit' để thoát.")
        print("="*50)
        
        while True:
            try:
                user_query = input("\n👤 Bạn: ").strip()
                if not user_query:
                    continue
                if user_query.lower() in ['exit', 'quit']:
                    print("👋 Tạm biệt!")
                    break
                run_react_agent(user_query, provider)
            except KeyboardInterrupt:
                print("\n👋 Tạm biệt!")
                break
            except Exception as e:
                print(f"\n❌ Đã xảy ra lỗi: {str(e)}")
        
        sys.exit(0)
        
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Chạy thử câu test số 3
    sample_query = tests[2]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
