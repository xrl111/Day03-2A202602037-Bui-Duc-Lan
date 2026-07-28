"""
🧠 PROMPTS & SAFEGUARDS (Dành cho Role 3: Prompt & Safeguard Engineer)
Nơi cấu hình System Prompt và Phanh An Toàn (Guardrails) cho AI.
Chủ đề: Trợ Lý Khai Quật Nhân Cách Thứ 2 & Tư Vấn Tâm Lý
"""

import unicodedata

# Baseline Chatbot Prompt (Chỉ dùng LLM thông thường, không có Tool)
CHATBOT_BASELINE_PROMPT = """Bạn là một Chatbot tư vấn tâm lý thông thường.
Nhiệm vụ: trò chuyện thân thiện, lắng nghe và đưa ra lời khuyên tâm lý chung
dựa trên kiến thức có sẵn của bạn (không tra cứu, không ghi nhớ gì thêm).

Giới hạn của bạn (cứ trả lời tự nhiên, không cần liệt kê những giới hạn này ra):
- Bạn không có bài trắc nghiệm tính cách nào để chấm điểm, chỉ có thể phỏng đoán qua lời văn.
- Bạn không nhớ được các lượt hội thoại trước, mỗi câu hỏi coi như độc lập.
- Bạn không có danh sách hotline/chuyên gia thật để giới thiệu.
- Bạn không phải bác sĩ tâm lý, không được chẩn đoán bệnh.
"""

# ReAct Agent Prompt (Ép LLM suy luận theo chuỗi Thought -> Action)
REACT_SYSTEM_PROMPT = """Bạn là một ReAct Agent hỗ trợ khai quật nhân cách & tư vấn tâm lý.

Danh sách công cụ bạn có thể sử dụng:
1. score_personality_test[answers]: Chấm điểm bộ câu trả lời trắc nghiệm tính cách, trả về xu hướng nhân cách.
2. lookup_counseling_resource[topic]: Tra cứu hotline/tài nguyên tư vấn tâm lý phù hợp với chủ đề.

QUY TẮC BẮT BUỘC: Khi trả lời, bạn PHẢI tuân theo định dạng từng dòng như sau:

Thought: Suy luận của bạn về bước tiếp theo cần làm.
Action: tên_công_cụ[tham_số]
(Sau đó dừng lại chờ hệ thống trả về kết quả Observation)

Khi đã có đủ thông tin để trả lời người dùng, hãy dùng định dạng:
Thought: Tôi đã có đủ thông tin để trả lời.
Final Answer: <câu trả lời, LUÔN kèm 1 câu disclaimer rằng đây không phải chẩn đoán y khoa>

QUY TẮC AN TOÀN:
- Không tự ý kết luận một "chẩn đoán" tâm lý chắc chắn, chỉ nêu xu hướng tham khảo.
- Nếu người dùng thể hiện dấu hiệu nguy hiểm, luôn ưu tiên gọi lookup_counseling_resource
  và đưa hotline lên đầu Final Answer.

BẮT ĐẦU:
"""

# 🛡️ GUARDRAILS CONFIGURATION (PHANH AN TOÀN)
MAX_ITERATIONS = 3  # Giới hạn tối đa 3 vòng lặp Thought-Action để tránh lặp vô tận
TIMEOUT_SECONDS = 10  # Timeout cho mỗi lần gọi tool

# Phanh cứng cấp code — app.py PHẢI gọi contains_crisis_signal() TRƯỚC khi vào vòng lặp
# ReAct, không phó thác việc phát hiện khủng hoảng cho LLM.
# Lưu keyword ở dạng đã bỏ dấu để so khớp không phân biệt dấu/hoa-thường/viết tắt không dấu.
CRISIS_KEYWORDS = [
    "tu tu", "tu sat", "khong muon song", "tu hai",
    "ket thuc cuoc doi", "bien mat mai mai", "muon chet",
    "khong con y nghia", "suicide", "kill myself", "end my life",
]
CRISIS_RESPONSE = (
    "⚠️ Nếu bạn đang gặp khủng hoảng tâm lý nghiêm trọng, hãy liên hệ ngay: "
    "Đường dây nóng Ngày mai 1800-599-920 hoặc gọi 111. "
    "Bạn không đơn độc, hãy tìm người thân/chuyên gia ở gần để được hỗ trợ trực tiếp."
)


def _strip_diacritics(text: str) -> str:
    """Bỏ dấu tiếng Việt để so khớp bền hơn (VD 'không muốn sống' == 'khong muon song')."""
    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def contains_crisis_signal(text: str) -> bool:
    """Kiểm tra rule-based (không qua LLM) xem câu hỏi có dấu hiệu khủng hoảng không."""
    normalized = _strip_diacritics(text)
    return any(keyword in normalized for keyword in CRISIS_KEYWORDS)


# Phanh cho trường hợp LLM trả lời sai định dạng ReAct (không có Action: lẫn Final Answer:).
# app.py nên gọi is_valid_react_step() sau mỗi lần LLM sinh output; nếu False, dùng
# MALFORMED_OUTPUT_FALLBACK thay vì cố parse tiếp (tránh crash hoặc lặp vô nghĩa).
MALFORMED_OUTPUT_FALLBACK = (
    "Xin lỗi, tôi chưa xử lý được yêu cầu này một cách an toàn. "
    "Bạn có thể diễn đạt lại câu hỏi rõ ràng hơn được không?"
)


def is_valid_react_step(text: str) -> bool:
    """Kiểm tra output của LLM có đúng định dạng Action:/Final Answer: theo REACT_SYSTEM_PROMPT không."""
    return ("Action:" in text) or ("Final Answer:" in text)
