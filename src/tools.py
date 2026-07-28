"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Counselor Agent Tools)
Hệ thống công cụ phục vụ "Trợ Lý Khai Quật Nhân Cách Thứ 2 & Tư Vấn Tâm Lý".
"""

import re
from typing import Any, Dict, List, Optional, Union

# ==============================================================================
# BỘ DỮ LIỆU NỘI BỘ VÀ CẤU HÌNH (LOCAL DATASETS & CONFIG)
# ==============================================================================

# Danh mục đường dây nóng & tài nguồn tư vấn tâm lý chính thống tại Việt Nam
COUNSELING_RESOURCE_DATABASE: List[Dict[str, str]] = [
    {
        "name": "Tổng đài Quốc gia Bảo vệ Trẻ em",
        "phone": "111",
        "operating_hours": "24/7 (Miễn phí cước gọi)",
        "topic": "child_abuse",
        "description": "Tư vấn, hỗ trợ can thiệp cho trẻ em bị bạo hành, xâm hại và phòng chống bạo lực gia đình."
    },
    {
        "name": "Đường dây nóng Bệnh viện Tâm thần Ban ngày Mai Hương",
        "phone": "1800 599 920",
        "operating_hours": "08:00 - 21:00 hàng ngày",
        "topic": "depression",
        "description": "Tư vấn tâm lý, đánh giá & hỗ trợ người gặp trầm cảm, lo âu, rối loạn cảm xúc và tâm lý chung."
    },
    {
        "name": "Viện Sức khỏe Tâm thần - Bệnh viện Bạch Mai",
        "phone": "024 3869 3731 / 0904 865 153",
        "operating_hours": "24/7 (Cấp cứu tâm thần)",
        "topic": "emergency",
        "description": "Sơ cứu tâm lý khẩn cấp, tiếp nhận & điều trị các ca khủng hoảng tâm thần, nguy cơ tự sát."
    }
]

# Bảng ánh xạ chủ đề (Topic Alias Mapping) để tối ưu tra cứu
TOPIC_ALIAS_MAP: Dict[str, str] = {
    # Nhóm Bảo vệ trẻ em / Bạo lực gia đình
    "child_abuse": "child_abuse",
    "child": "child_abuse",
    "trẻ em": "child_abuse",
    "tre em": "child_abuse",
    "bạo lực gia đình": "child_abuse",
    "bao luc gia dinh": "child_abuse",
    "bạo lực": "child_abuse",
    "bao luc": "child_abuse",
    
    # Nhóm Trầm cảm / Tâm lý chung
    "depression": "depression",
    "trầm cảm": "depression",
    "tram cam": "depression",
    "tâm lý chung": "depression",
    "tam ly chung": "depression",
    "tâm lý": "depression",
    "tam ly": "depression",
    "lo âu": "depression",
    "lo au": "depression",
    
    # Nhóm Khẩn cấp / Sơ cứu tâm lý
    "emergency": "emergency",
    "khẩn cấp": "emergency",
    "khan cap": "emergency",
    "sơ cứu tâm lý": "emergency",
    "so cuu tam ly": "emergency",
    "sơ cứu": "emergency",
    "so cuu": "emergency",
    "tự tử": "emergency",
    "tu tu": "emergency",
    "nguy hiểm": "emergency"
}

# Danh sách regex các cụm từ lóng / nói quá an toàn (Safe Slang Masking Patterns)
# Giúp loại bỏ False Positive cho từ "chết" trong các ngữ cảnh đời thường
SAFE_SLANG_PATTERNS: List[str] = [
    r'\b(mệt|cười|vui|sợ|bận|nóng|lạnh|tức|thèm|đẹp|đau|sướng|thích|nản)\s+chết(\s+(đi\s+được|mất|được))?\b',
    r'\bchết\s+(cười|mê|mệt|ngất|điều)\b',
    r'\bchết\s+đi\s+được\b',
    r'\bchết\s+mất\b',
    r'\bsợ\s+chết\s+được\b',
    r'\bthèm\s+chết\s+được\b',
]


# ==============================================================================
# CÁC AGENT TOOLS CHÍNH
# ==============================================================================

def score_personality_test(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chấm điểm bài trắc nghiệm tính cách ngắn TIPI (Ten-Item Personality Inventory) và xác định xu hướng tính cách Big Five.
    
    Hàm tính toán thuần offline dựa trên 10 câu hỏi tiêu chuẩn với thang điểm từ 1 đến 7:
    - Q1: Hướng ngoại, nhiệt tình (Extraversion +)
    - Q2: Hay chỉ trích, dễ tranh cãi (Agreeableness -)
    - Q3: Đáng tin cậy, tự giác (Conscientiousness +)
    - Q4: Lo âu, dễ bị kích động (Neuroticism +)
    - Q5: Cởi mở với trải nghiệm mới, tư duy phong phú (Openness +)
    - Q6: Kín đáo, trầm lặng (Extraversion -)
    - Q7: Đồng cảm, ấm áp (Agreeableness +)
    - Q8: Bừa bộn, cẩu thả (Conscientiousness -)
    - Q9: Bình tĩnh, ổn định cảm xúc (Neuroticism -)
    - Q10: Thức thời, ít sáng tạo (Openness -)

    Args:
        answers (dict): Từ điển chứa các cặp key-value đại diện cho ID câu hỏi (Q1->Q10 hoặc 1->10)
                        và điểm số trả lời tương ứng (số nguyên từ 1 đến 7).
                        Ví dụ: {"Q1": 6, "Q2": 2, "Q3": 5, "Q4": 3, "Q5": 7, "Q6": 2, "Q7": 6, "Q8": 2, "Q9": 6, "Q10": 3}

    Returns:
        dict: Kết quả phân tích tính cách bao gồm:
            - "scores" (dict): Điểm trung bình (1.0 đến 7.0) cho từng nhóm Big Five:
                Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism.
            - "dominant_trait" (str): Tên nhóm tính cách có điểm số cao nhất.
            - "dominant_trait_label" (str): Nhãn mô tả tiếng Việt của nét tính cách nổi trội.
            - "summary" (str): Tóm tắt đánh giá ngắn gọn về xu hướng tính cách.

    Raises:
        ValueError: Nếu định dạng đầu vào không hợp lệ hoặc chứa điểm ngoài khoảng [1, 7].
    """
    try:
        if not isinstance(answers, dict) or not answers:
            return {
                "error": True,
                "message": "Đầu vào 'answers' phải là một dictionary không rỗng.",
                "scores": {},
                "dominant_trait": "Unknown",
                "dominant_trait_label": "Không xác định",
                "summary": "Không thể chấm điểm do dữ liệu đầu vào không hợp lệ."
            }

        norm_answers: Dict[int, float] = {}
        for k, v in answers.items():
            key_str = str(k).strip().upper()
            match = re.search(r'\d+', key_str)
            if not match:
                continue
            q_num = int(match.group(0))
            if 1 <= q_num <= 10:
                try:
                    val = float(v)
                    if not (1.0 <= val <= 7.0):
                        return {
                            "error": True,
                            "message": f"Điểm số cho câu Q{q_num} phải nằm trong khoảng từ 1 đến 7 (nhận được {v}).",
                            "scores": {},
                            "dominant_trait": "Unknown",
                            "dominant_trait_label": "Không xác định",
                            "summary": "Dữ liệu điểm số nằm ngoài phạm vi cho phép (1-7)."
                        }
                    norm_answers[q_num] = val
                except (ValueError, TypeError):
                    return {
                        "error": True,
                        "message": f"Điểm số cho câu Q{q_num} không đúng định dạng số.",
                        "scores": {},
                        "dominant_trait": "Unknown",
                        "dominant_trait_label": "Không xác định",
                        "summary": "Điểm số không đúng định dạng số."
                    }

        # Fallback điểm trung tính (4.0) cho các câu chưa trả lời
        for i in range(1, 11):
            if i not in norm_answers:
                norm_answers[i] = 4.0

        # Công thức chấm điểm TIPI chuẩn (Thang 1-7)
        extraversion = (norm_answers[1] + (8.0 - norm_answers[6])) / 2.0
        agreeableness = ((8.0 - norm_answers[2]) + norm_answers[7]) / 2.0
        conscientiousness = (norm_answers[3] + (8.0 - norm_answers[8])) / 2.0
        neuroticism = (norm_answers[4] + (8.0 - norm_answers[9])) / 2.0
        openness = (norm_answers[5] + (8.0 - norm_answers[10])) / 2.0

        scores = {
            "Extraversion": round(extraversion, 2),
            "Agreeableness": round(agreeableness, 2),
            "Conscientiousness": round(conscientiousness, 2),
            "Neuroticism": round(neuroticism, 2),
            "Openness": round(openness, 2)
        }

        trait_labels = {
            "Extraversion": "Hướng ngoại & Năng động",
            "Agreeableness": "Hòa nhã & Thân thiện",
            "Conscientiousness": "Tận tụy & Tự giác",
            "Neuroticism": "Nhạy cảm cảm xúc & Dễ căng thẳng",
            "Openness": "Cởi mở & Sáng tạo"
        }

        dominant_trait = max(scores, key=scores.get)
        dominant_label = trait_labels.get(dominant_trait, dominant_trait)

        summary = f"Nét tính cách nổi trội của bạn là '{dominant_label}' với điểm số {scores[dominant_trait]}/7.0."

        return {
            "error": False,
            "scores": scores,
            "dominant_trait": dominant_trait,
            "dominant_trait_label": dominant_label,
            "summary": summary
        }

    except Exception as e:
        return {
            "error": True,
            "message": f"Xảy ra lỗi trong quá trình xử lý: {str(e)}",
            "scores": {},
            "dominant_trait": "Unknown",
            "dominant_trait_label": "Không xác định",
            "summary": "Không thể chấm điểm bài trắc nghiệm."
        }


def detect_crisis_signal(text: str) -> Dict[str, Any]:
    """
    Phát hiện các tín hiệu khủng hoảng tâm lý nghiêm trọng (tự tử, tự hại, bạo hành, trầm cảm nặng) trong tin nhắn của người dùng.
    
    Hàm sử dụng hoàn toàn logic khớp từ khóa và biểu thức chính quy (Regex / Keyword Rule-based) thuần tính toán,
    LOẠI BỎ FALSE POSITIVE (các cụm từ lóng tiếng Việt như 'mệt chết đi được', 'cười chết mất') và TUYỆT ĐỐI KHÔNG sử dụng LLM.

    Args:
        text (str): Văn bản tin nhắn thô nhập từ người dùng.

    Returns:
        dict: Kết quả phát hiện tín hiệu khủng hoảng gồm:
            - "has_crisis" (bool): True nếu phát hiện tín hiệu khủng hoảng nghiêm trọng (Severity Level >= 2 hoặc 3), ngược lại False.
            - "severity_level" (int): Mức độ nghiêm trọng từ 0 đến 3:
                + 0: An toàn (Không có tín hiệu).
                + 1: Cảnh báo nhẹ (Bày tỏ mệt mỏi, áp lực đời sống, từ lóng đời thường).
                + 2: Báo động trung bình (Tuyệt vọng, bạo hành, trầm cảm nặng).
                + 3: Nguy hiểm khẩn cấp (Tự tử, làm hại bản thân, cắt tay, uống thuốc ngủ, nhảy cầu, kết thúc mọi thứ).
            - "matched_keywords" (list[str]): Danh sách các từ khóa nguy cơ đã khớp trong văn bản.
            - "action_recommendation" (str): Khuyến nghị hành động ứng phó ban đầu.
    """
    try:
        if not isinstance(text, str) or not text.strip():
            return {
                "has_crisis": False,
                "severity_level": 0,
                "matched_keywords": [],
                "action_recommendation": "Thông điệp rỗng hoặc không hợp lệ."
            }

        text_lower = text.lower().strip()

        # BƯỚC XỬ LÝ FALSE POSITIVE: Khử các cụm từ lóng / nói quá mang nghĩa đời thường
        sanitized_text = text_lower
        for pattern in SAFE_SLANG_PATTERNS:
            sanitized_text = re.sub(pattern, ' ', sanitized_text)

        # Định nghĩa bộ từ khóa nguy cơ theo từng cấp độ nghiêm trọng
        # Cấp độ 3: Nguy hiểm khẩn cấp (Tự tử, tự hại, uống thuốc ngủ, kết thúc cuộc đời)
        level_3_keywords = [
            "tự tử", "không muốn sống", "làm hại bản thân", "nhảy cầu",
            "cắt tay", "uống thuốc ngủ", "kết thúc cuộc đời", "kết thúc mọi thứ",
            "tự sát", "kết liễu", "muốn chết", "tìm đến cái chết", "chết đi cho xong"
        ]
        # Kiểm tra từ "chết" đứng độc lập sau khi đã lọc slang
        if re.search(r'\bchết\b', sanitized_text):
            level_3_keywords.append("chết")

        # Cấp độ 2: Báo động trung bình (Tuyệt vọng, bạo hành, trầm cảm nặng)
        level_2_keywords = [
            "tuyệt vọng", "trầm cảm nặng", "bạo hành", "bị đánh đập",
            "bị hành hạ", "kiệt sức rồi", "muốn biến mất"
        ]

        # Cấp độ 1: Cảnh báo nhẹ / Tâm lý mệt mỏi đời thường
        level_1_keywords = [
            "chán đời", "bất lực", "mệt mỏi", "bế tắc", "áp lực", "nản"
        ]

        matched_l3 = [kw for kw in level_3_keywords if kw in sanitized_text]
        matched_l2 = [kw for kw in level_2_keywords if kw in sanitized_text]
        matched_l1 = [kw for kw in level_1_keywords if kw in text_lower] # Giữ l1 từ text gốc để nhận diện mệt mỏi

        if matched_l3:
            severity = 3
            recommendation = "KÍCH HOẠT QUY TRÌNH BẢO VỆ KHẨN CẤP: Kết nối ngay lập tức với các đường dây nóng hỗ trợ sơ cứu tâm lý khẩn cấp (111 hoặc 024 3869 3731)."
        elif matched_l2:
            severity = 2
            recommendation = "CẢNH BÁO CAO: Cung cấp thông tin các cơ sở tư vấn tâm lý, lắng nghe sâu và khuyến khích người dùng liên hệ chuyên gia."
        elif matched_l1:
            severity = 1
            recommendation = "CHÚ Ý: Thấu hiểu cảm xúc tiêu cực của người dùng, đưa ra các lời khuyên giải tỏa căng thẳng nhẹ nhàng."
        else:
            severity = 0
            recommendation = "AN TOÀN: Không phát hiện tín hiệu khủng hoảng tâm lý nghiêm trọng."

        # has_crisis chỉ đặt True khi ở mức Báo động (Level 2) hoặc Khẩn cấp (Level 3)
        has_crisis = severity >= 2
        all_matched = matched_l3 if severity == 3 else (matched_l2 if severity == 2 else matched_l1)

        return {
            "has_crisis": has_crisis,
            "severity_level": severity,
            "matched_keywords": list(set(all_matched)),
            "action_recommendation": recommendation
        }

    except Exception as e:
        return {
            "has_crisis": False,
            "severity_level": 0,
            "matched_keywords": [],
            "action_recommendation": f"Lỗi trong quá trình kiểm tra tín hiệu khủng hoảng: {str(e)}"
        }


def lookup_counseling_resource(topic: str = "general") -> List[Dict[str, str]]:
    """
    Tra cứu danh mục đường dây nóng (Hotline) và tài nguyên tư vấn tâm lý uy tín tại Việt Nam theo chủ đề.
    
    Hàm sử dụng ánh xạ Dictionary (Topic Alias Mapping) tối ưu để tra cứu nhanh chóng và chính xác.

    Args:
        topic (str, optional): Chủ đề cần tra cứu. Hỗ trợ các từ khóa:
            - "child_abuse" / "bạo lực gia đình" / "trẻ em": Tổng đài Bảo vệ Trẻ em & Phòng chống bạo lực.
            - "depression" / "trầm cảm" / "tâm lý chung": Tư vấn trầm cảm & hỗ trợ tâm lý cộng đồng.
            - "emergency" / "khẩn cấp" / "sơ cứu tâm lý": Sơ cứu tâm lý & điều trị khủng hoảng sức khỏe tâm thần.
            - "general" / "chung" (Mặc định): Trả về toàn bộ danh mục tài nguyên khả dụng.

    Returns:
        list[dict]: Danh sách các đường dây nóng phù hợp, mỗi tài nguyên bao gồm:
            - "name" (str): Tên tổ chức / cơ sở hỗ trợ.
            - "phone" (str): Số điện thoại đường dây nóng.
            - "operating_hours" (str): Khung giờ hoạt động.
            - "topic" (str): Phân loại chủ đề.
            - "description" (str): Mô tả chi tiết dịch vụ hỗ trợ.
    """
    try:
        if not topic or not isinstance(topic, str):
            return COUNSELING_RESOURCE_DATABASE

        topic_clean = topic.strip().lower()

        # Trả về toàn bộ nếu người dùng yêu cầu chung hoặc tất cả
        if topic_clean in ["general", "chung", "all", "tất cả"]:
            return COUNSELING_RESOURCE_DATABASE

        # Ánh xạ topic alias về topic ID chuẩn
        target_topic_id = TOPIC_ALIAS_MAP.get(topic_clean)

        # Fallback: Tra cứu mờ (substring match) nếu không khớp exact key
        if not target_topic_id:
            for alias, mapped_id in TOPIC_ALIAS_MAP.items():
                if alias in topic_clean:
                    target_topic_id = mapped_id
                    break

        if target_topic_id:
            filtered = [res for res in COUNSELING_RESOURCE_DATABASE if res["topic"] == target_topic_id]
            if filtered:
                return filtered

        # Nếu không khớp chủ đề nào, trả về toàn bộ dữ liệu làm fallback an toàn
        return COUNSELING_RESOURCE_DATABASE

    except Exception as e:
        return [
            {
                "name": "Lỗi tra cứu tài nguyên",
                "phone": "N/A",
                "operating_hours": "N/A",
                "topic": "error",
                "description": f"Không thể lấy danh sách tài nguyên: {str(e)}"
            }
        ]


# ==============================================================================
# AGENT TOOL REGISTRY (ROLE 2)
# ==============================================================================
AVAILABLE_TOOLS = {
    "score_personality_test": score_personality_test,
    "detect_crisis_signal": detect_crisis_signal,
    "lookup_counseling_resource": lookup_counseling_resource,
}


# ==============================================================================
# KHỐI TỰ KIỂM THỬ (SELF-TESTING SUITE)
# ==============================================================================
if __name__ == "__main__":
    import sys
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    print("==================================================")
    print("🧪 SELF-TESTING AGENT TOOLS (Role 2 - Counselor Agent)")
    print("==================================================")
    
    print("\n--- Test 1: detect_crisis_signal (False Positive Slang) ---")
    test1_input = "Nay sếp mắng mệt chết đi được, nản thật."
    res1 = detect_crisis_signal(test1_input)
    print(f"Input:  '{test1_input}'")
    print(f"Output: severity_level={res1['severity_level']}, has_crisis={res1['has_crisis']}, keywords={res1['matched_keywords']}")

    print("\n--- Test 2: detect_crisis_signal (True Crisis Level 3) ---")
    test2_input = "Tôi thực sự tuyệt vọng và muốn uống thuốc ngủ để kết thúc mọi thứ."
    res2 = detect_crisis_signal(test2_input)
    print(f"Input:  '{test2_input}'")
    print(f"Output: severity_level={res2['severity_level']}, has_crisis={res2['has_crisis']}, keywords={res2['matched_keywords']}")

    print("\n--- Test 3: lookup_counseling_resource ('tâm lý chung') ---")
    test3_input = "tâm lý chung"
    res3 = lookup_counseling_resource(test3_input)
    print(f"Input:  '{test3_input}'")
    print(f"Output: Tìm thấy {len(res3)} tài nguyên:")
    for item in res3:
        print(f" - {item['name']} | Hotline: {item['phone']} | Giờ: {item['operating_hours']}")
    print("==================================================")
