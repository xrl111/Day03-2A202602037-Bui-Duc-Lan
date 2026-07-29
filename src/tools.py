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


def score_clinical_assessment(test_type: str, answers: Dict[str, int]) -> Dict[str, Any]:
    """
    Chấm điểm bài test tâm lý lâm sàng ngắn (PHQ-9 cho Trầm cảm hoặc GAD-7 cho Lo âu) và phân loại mức độ nghiêm trọng.
    
    Hàm tính toán thuần offline dựa trên quy tắc chấm điểm tiêu chuẩn:
    - PHQ-9 (Max 27đ): 0-4 (Bình thường), 5-9 (Nhẹ), 10-14 (Vừa), 15-19 (Nặng), 20-27 (Rất nặng)
    - GAD-7 (Max 21đ): 0-4 (Bình thường), 5-9 (Nhẹ), 10-14 (Vừa), 15-21 (Nặng)

    Args:
        test_type (str): Chuỗi nhận diện loại test ("PHQ-9" hoặc "GAD-7").
        answers (dict): Dictionary chứa mã câu hỏi (ví dụ "q1", "q2") và điểm số từng câu (số nguyên từ 0 đến 3).

    Returns:
        dict: Kết quả đánh giá bao gồm:
            - "test_type" (str): Tên loại bài test đã chấm ("PHQ-9" hoặc "GAD-7").
            - "total_score" (int): Tổng điểm số đạt được.
            - "max_score" (int): Điểm tối đa của bài test (27 với PHQ-9, 21 với GAD-7).
            - "severity" (str): Phân loại mức độ nghiêm trọng bằng tiếng Việt.
            - "summary" (str): Tóm tắt kết quả đánh giá ngắn gọn.
            - "error" (bool): Cờ báo lỗi (True nếu đầu vào không hợp lệ).
            - "message" (str, optional): Thông báo chi tiết nếu xảy ra lỗi.
    """
    try:
        if not isinstance(test_type, str) or not test_type.strip():
            return {
                "error": True,
                "message": "Tên bài test ('test_type') không hợp lệ.",
                "test_type": "Unknown",
                "total_score": 0,
                "max_score": 0,
                "severity": "Không xác định",
                "summary": "Không thể chấm điểm do thiếu thông tin loại bài test."
            }

        norm_type = test_type.strip().upper()
        if norm_type in ["PHQ-9", "PHQ9"]:
            test_name = "PHQ-9"
            max_score = 27
        elif norm_type in ["GAD-7", "GAD7"]:
            test_name = "GAD-7"
            max_score = 21
        else:
            return {
                "error": True,
                "message": f"Loại bài test '{test_type}' không được hỗ trợ. Chỉ hỗ trợ 'PHQ-9' hoặc 'GAD-7'.",
                "test_type": test_type,
                "total_score": 0,
                "max_score": 0,
                "severity": "Không xác định",
                "summary": "Loại bài test không nằm trong danh mục hỗ trợ."
            }

        if not isinstance(answers, dict) or not answers:
            return {
                "error": True,
                "message": "Đầu vào 'answers' phải là một dictionary chứa câu trả lời và điểm số.",
                "test_type": test_name,
                "total_score": 0,
                "max_score": max_score,
                "severity": "Không xác định",
                "summary": "Dữ liệu câu trả lời bị rỗng hoặc sai định dạng."
            }

        total_score = 0
        for q_id, val in answers.items():
            try:
                score_val = int(val)
                if not (0 <= score_val <= 3):
                    return {
                        "error": True,
                        "message": f"Điểm số cho câu '{q_id}' phải là số nguyên từ 0 đến 3 (nhận được {val}).",
                        "test_type": test_name,
                        "total_score": 0,
                        "max_score": max_score,
                        "severity": "Không xác định",
                        "summary": f"Điểm số của câu '{q_id}' nằm ngoài khoảng [0, 3]."
                    }
                total_score += score_val
            except (ValueError, TypeError):
                return {
                    "error": True,
                    "message": f"Điểm số cho câu '{q_id}' không đúng định dạng số nguyên.",
                    "test_type": test_name,
                    "total_score": 0,
                    "max_score": max_score,
                    "severity": "Không xác định",
                    "summary": f"Câu '{q_id}' chứa điểm số không đúng định dạng."
                }

        # Phân loại mức độ nghiêm trọng (Severity Classification)
        severity = "Bình thường"
        if test_name == "PHQ-9":
            if 0 <= total_score <= 4:
                severity = "Bình thường"
            elif 5 <= total_score <= 9:
                severity = "Nhẹ"
            elif 10 <= total_score <= 14:
                severity = "Vừa"
            elif 15 <= total_score <= 19:
                severity = "Nặng"
            elif 20 <= total_score <= 27:
                severity = "Rất nặng"
        elif test_name == "GAD-7":
            if 0 <= total_score <= 4:
                severity = "Bình thường"
            elif 5 <= total_score <= 9:
                severity = "Nhẹ"
            elif 10 <= total_score <= 14:
                severity = "Vừa"
            elif 15 <= total_score <= 21:
                severity = "Nặng"

        summary = f"Đánh giá lâm sàng {test_name}: Tổng điểm {total_score}/{max_score} - Mức độ: {severity}."

        return {
            "error": False,
            "test_type": test_name,
            "total_score": total_score,
            "max_score": max_score,
            "severity": severity,
            "summary": summary
        }

    except Exception as e:
        return {
            "error": True,
            "message": f"Lỗi trong quá trình tính điểm đánh giá lâm sàng: {str(e)}",
            "test_type": test_type if isinstance(test_type, str) else "Unknown",
            "total_score": 0,
            "max_score": 0,
            "severity": "Không xác định",
            "summary": "Không thể xử lý bài test lâm sàng."
        }


def suggest_grounding_technique(state: str) -> Dict[str, str]:
    """
    Đề xuất kỹ thuật trị liệu "nối đất" (grounding) ngay lập tức khi phát hiện người dùng bị lo âu, hoảng loạn hoặc căng thẳng.
    
    Hàm sử dụng logic khớp từ khóa offline (Rule-based Keyword Match):
    - Chứa "hoảng loạn" / "panic": Kỹ thuật 5-4-3-2-1
    - Chứa "lo âu" / "căng thẳng": Kỹ thuật thở hộp (Box Breathing)
    - Khác: Kỹ thuật nhận thức cơ thể (Body Scan)

    Args:
        state (str): Chuỗi mô tả trạng thái của người dùng (ví dụ: "hoảng loạn", "lo âu", "căng thẳng").

    Returns:
        dict: Thông tin kỹ thuật trị liệu đề xuất bao gồm:
            - "technique_name" (str): Tên kỹ thuật trị liệu.
            - "instructions" (str): Hướng dẫn thực hiện chi tiết từng bước bằng tiếng Việt.
            - "target_state" (str): Trạng thái ứng phó được nhận diện.
    """
    try:
        if not isinstance(state, str) or not state.strip():
            state_clean = ""
        else:
            state_clean = state.lower().strip()

        if "hoảng loạn" in state_clean or "panic" in state_clean:
            technique_name = "Kỹ thuật Nối đất 5-4-3-2-1 (5-4-3-2-1 Grounding Technique)"
            instructions = (
                "Hãy dừng lại, quan sát xung quanh và thực hiện theo 5 bước:\n"
                "1. Nhận biết 5 thứ bạn nhìn thấy xung quanh.\n"
                "2. Nhận biết 4 thứ bạn có thể chạm vào ngay lúc này.\n"
                "3. Nhận biết 3 âm thanh bạn lắng nghe được.\n"
                "4. Nhận biết 2 mùi hương bạn ngửi thấy.\n"
                "5. Nhận biết 1 vị bạn cảm nhận được trên lưỡi.\n"
                "Hít thở sâu và chậm rãi sau mỗi bước để lấy lại sự bình tĩnh."
            )
            target_state = "hoảng loạn"
        elif "lo âu" in state_clean or "căng thẳng" in state_clean or "anxiety" in state_clean or "stress" in state_clean:
            technique_name = "Kỹ thuật Thở hộp (Box Breathing)"
            instructions = (
                "Thực hiện chu kỳ thở 4 thì để cân bằng hệ thần kinh:\n"
                "1. Hít vào từ từ qua mũi trong 4 giây.\n"
                "2. Giữ hơi thở lại trong 4 giây.\n"
                "3. Thở ra chậm rãi qua miệng trong 4 giây.\n"
                "4. Giữ phổi rỗng trong 4 giây.\n"
                "Lặp lại chu kỳ từ 4 đến 6 lần."
            )
            target_state = "lo âu / căng thẳng"
        else:
            technique_name = "Kỹ thuật Nhận thức Cơ thể (Body Scan)"
            instructions = (
                "Thực hiện thư giãn và kết nối với cơ thể:\n"
                "1. Nhắm mắt nhẹ nhàng và cảm nhận đôi bàn chân đang tiếp xúc chắc chắn với mặt đất.\n"
                "2. Thả lỏng toàn bộ cơ vai, cổ và khuôn mặt.\n"
                "3. Tập trung sự chú ý vào nhịp thở tự nhiên lên xuống ở vùng bụng.\n"
                "4. Lần lượt quét qua các phần cơ thể và giải phóng mọi cảm giác căng cứng theo mỗi nhịp thở ra."
            )
            target_state = "mặc định / nhận thức chung"

        return {
            "technique_name": technique_name,
            "instructions": instructions,
            "target_state": target_state
        }

    except Exception as e:
        return {
            "technique_name": "Kỹ thuật Thở sâu cơ bản",
            "instructions": f"Hít vào thật sâu và thở ra từ từ để giải tỏa áp lực. (Chi tiết lỗi: {str(e)})",
            "target_state": "lỗi xử lý"
        }


def analyze_cognitive_distortion(text: str) -> Dict[str, Any]:
    """
    Nhận diện sơ bộ các méo mó nhận thức (Cognitive Distortions) trong lời kể của người dùng.
    
    Hàm tính toán offline dựa trên từ khóa và biểu thức chính quy (Regex/Keyword Rule-based):
    - Tư duy trắng đen (All-or-Nothing): "không bao giờ", "chắc chắn thất bại", "chẳng ra gì", "luôn luôn sai"
    - Đọc tâm trí (Mind Reading): "chắc chắn họ nghĩ", "ai cũng thấy", "họ đang cười nhạo"
    - Câu lệnh Phải (Should Statements): "đáng lẽ ra phải", "tôi phải", "nhất định phải"

    Args:
        text (str): Đoạn văn bản / lời kể thô nhập từ người dùng.

    Returns:
        dict: Kết quả phân tích bao gồm:
            - "has_distortion" (bool): True nếu phát hiện ít nhất một méo mó nhận thức.
            - "detected" (list[dict]): Danh sách các lỗi nhận diện được, mỗi lỗi gồm:
                + "type" (str): Tên phân loại méo mó nhận thức.
                + "matched_phrase" (str): Cụm từ phát hiện được.
                + "reframe" (str): Câu hỏi / Lời gợi ý phản tư giúp Agent hướng dẫn user tái cấu trúc nhận thức.
    """
    try:
        if not isinstance(text, str) or not text.strip():
            return {
                "has_distortion": False,
                "detected": []
            }

        text_lower = text.lower()
        detected_list: List[Dict[str, str]] = []

        # 1. Tư duy trắng đen (All-or-Nothing Thinking)
        all_or_nothing_patterns = [
            ("không bao giờ", "không bao giờ"),
            ("chắc chắn thất bại", "chắc chắn thất bại"),
            ("chẳng ra gì", "chẳng ra gì"),
            ("luôn luôn sai", "luôn luôn sai"),
            ("luôn sai", "luôn sai"),
            ("hoàn toàn thất bại", "hoàn toàn thất bại")
        ]
        for pattern, matched_kw in all_or_nothing_patterns:
            if pattern in text_lower:
                detected_list.append({
                    "type": "Tư duy trắng đen (All-or-Nothing Thinking)",
                    "matched_phrase": matched_kw,
                    "reframe": "Có thực sự là 'hoàn toàn' hay 'không bao giờ' không? Liệu có trường hợp ngoại lệ nào hoặc khoảng xám nào ở giữa không?"
                })
                break # Mỗi loại chỉ lấy 1 khớp đại diện

        # 2. Đọc tâm trí (Mind Reading)
        mind_reading_patterns = [
            ("chắc chắn họ nghĩ", "chắc chắn họ nghĩ"),
            ("ai cũng thấy", "ai cũng thấy"),
            ("họ đang cười nhạo", "họ đang cười nhạo"),
            ("mọi người đều nghĩ", "mọi người đều nghĩ"),
            ("họ xem thường", "họ xem thường")
        ]
        for pattern, matched_kw in mind_reading_patterns:
            if pattern in text_lower:
                detected_list.append({
                    "type": "Đọc tâm trí (Mind Reading)",
                    "matched_phrase": matched_kw,
                    "reframe": "Bạn có bằng chứng rõ ràng và khách quan cho thấy họ đang nghĩ như vậy không, hay đó chỉ là suy đoán của bản thân?"
                })
                break

        # 3. Câu lệnh Phải (Should Statements)
        should_patterns = [
            ("đáng lẽ ra phải", "đáng lẽ ra phải"),
            ("đáng lẽ phải", "đáng lẽ phải"),
            ("tôi phải", "tôi phải"),
            ("nhất định phải", "nhất định phải"),
            ("bắt buộc phải", "bắt buộc phải")
        ]
        for pattern, matched_kw in should_patterns:
            if pattern in text_lower:
                detected_list.append({
                    "type": "Câu lệnh Phải (Should Statements)",
                    "matched_phrase": matched_kw,
                    "reframe": "Thay vì đặt áp lực bằng từ 'phải', nếu thay bằng 'tôi mong muốn' hoặc 'tôi ưu tiên' thì cảm xúc của bạn sẽ thay đổi thế nào?"
                })
                break

        return {
            "has_distortion": len(detected_list) > 0,
            "detected": detected_list
        }

    except Exception as e:
        return {
            "has_distortion": False,
            "detected": [],
            "error_message": f"Lỗi phân tích méo mó nhận thức: {str(e)}"
        }


# ==============================================================================
# AGENT TOOL REGISTRY (ROLE 2)
# ==============================================================================
AVAILABLE_TOOLS = {
    "score_personality_test": score_personality_test,
    "detect_crisis_signal": detect_crisis_signal,
    "lookup_counseling_resource": lookup_counseling_resource,
    "score_clinical_assessment": score_clinical_assessment,
    "suggest_grounding_technique": suggest_grounding_technique,
    "analyze_cognitive_distortion": analyze_cognitive_distortion,
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

    print("\n--- Test 4: score_clinical_assessment (PHQ-9) ---")
    phq9_answers = {"q1": 2, "q2": 3, "q3": 1, "q4": 2, "q5": 3, "q6": 2, "q7": 1, "q8": 2, "q9": 1}
    res4 = score_clinical_assessment("PHQ-9", phq9_answers)
    print(f"Test PHQ-9 Input: {phq9_answers}")
    print(f"Output: total_score={res4['total_score']}/{res4['max_score']}, severity='{res4['severity']}', error={res4['error']}")
    print(f"Summary: {res4['summary']}")

    print("\n--- Test 5: score_clinical_assessment (GAD-7) ---")
    gad7_answers = {"q1": 1, "q2": 1, "q3": 0, "q4": 1, "q5": 2, "q6": 0, "q7": 1}
    res5 = score_clinical_assessment("GAD-7", gad7_answers)
    print(f"Test GAD-7 Input: {gad7_answers}")
    print(f"Output: total_score={res5['total_score']}/{res5['max_score']}, severity='{res5['severity']}', error={res5['error']}")
    print(f"Summary: {res5['summary']}")

    print("\n--- Test 6: suggest_grounding_technique ('hoảng loạn') ---")
    res6 = suggest_grounding_technique("Tôi đang thấy rất hoảng loạn và khó thở")
    print(f"Technique: {res6['technique_name']} (Target: {res6['target_state']})")
    print(f"Instructions:\n{res6['instructions']}")

    print("\n--- Test 7: suggest_grounding_technique ('lo âu') ---")
    res7 = suggest_grounding_technique("Tôi cảm thấy lo âu và căng thẳng áp lực công việc")
    print(f"Technique: {res7['technique_name']} (Target: {res7['target_state']})")

    print("\n--- Test 8: analyze_cognitive_distortion ---")
    test8_input = "Tôi làm việc này chắc chắn thất bại rồi, ai cũng thấy tôi tệ hại. Đáng lẽ ra phải làm tốt hơn."
    res8 = analyze_cognitive_distortion(test8_input)
    print(f"Input: '{test8_input}'")
    print(f"has_distortion: {res8['has_distortion']}")
    for item in res8['detected']:
        print(f" - [{item['type']}] Khớp cụm từ: '{item['matched_phrase']}'")
        print(f"   Reframe: {item['reframe']}")

    print("==================================================")
