Tài liệu Hệ thống Công cụ (Tool Registry) - Role 2

Tài liệu này giải thích chi tiết 6 công cụ (tools) được định nghĩa trong file tools.py dành cho "Trợ Lý Khai Quật Nhân Cách Thứ 2 & Tư Vấn Tâm Lý". Tất cả các công cụ này được thiết kế theo nguyên tắc Rule-based (Dựa trên luật), Deterministic (Có tính xác định) và Offline 100% (Không phụ thuộc LLM/API ngoài) để đảm bảo an toàn, bảo mật và tốc độ phản hồi tức thì.

1. Công cụ Khai quật & Đánh giá (Assessment Tools)

Nhóm công cụ này giúp thu thập dữ liệu định lượng và phân loại trạng thái tâm lý/nhân cách của người dùng.

1.1. score_personality_test

Mục đích: Chấm điểm bài trắc nghiệm tính cách ngắn TIPI (Ten-Item Personality Inventory).

Chức năng: Xử lý câu trả lời cho 10 câu hỏi (thang điểm 1-7), bao gồm cả việc đảo ngược điểm (reverse-scoring) đối với các câu hỏi tiêu cực.

Đầu ra: Điểm số chi tiết cho 5 nhóm tính cách Big Five (Hướng ngoại, Hòa nhã, Tận tụy, Nhạy cảm cảm xúc, Cởi mở) và chỉ ra nét tính cách nổi trội nhất.

Xử lý ngoại lệ: Tự động điền điểm trung tính (4.0) nếu người dùng bỏ sót câu hỏi.

1.2. score_clinical_assessment

Mục đích: Chấm điểm các bài kiểm tra tâm lý lâm sàng ngắn (PHQ-9 cho Trầm cảm và GAD-7 cho Lo âu).

Chức năng: Cộng dồn điểm số từ các câu trả lời (thang điểm 0-3) và đối chiếu với các mốc chuẩn y khoa.

Đầu ra: Tổng điểm và phân loại mức độ nghiêm trọng (Bình thường, Nhẹ, Vừa, Nặng, Rất nặng).

2. Công cụ An toàn & Can thiệp (Safety & Intervention Tools)

Nhóm công cụ này chịu trách nhiệm phát hiện nguy hiểm và cung cấp các biện pháp sơ cứu tâm lý.

2.1. detect_crisis_signal (Đặc biệt Quan trọng)

Mục đích: Đóng vai trò là "lưới an toàn" (Safety Net), quét mọi tin nhắn của người dùng để tìm tín hiệu khủng hoảng (tự sát, bạo hành).

Logic (Chống False Positive):

Bước 1: Dùng Regex (danh sách SAFE_SLANG_PATTERNS) để loại bỏ các từ lóng vô hại chứa từ nhạy cảm (ví dụ: "mệt chết đi được", "cười chết mất").

Bước 2: Đối chiếu văn bản còn lại với 3 cấp độ từ khóa:

Cấp độ 3 (Khẩn cấp): Các từ khóa về hành động thực tế (tự tử, nhảy cầu, uống thuốc ngủ).

Cấp độ 2 (Báo động): Các từ khóa về tình trạng tồi tệ (tuyệt vọng, bạo hành).

Cấp độ 1 (Cảnh báo): Các từ khóa biểu đạt sự mệt mỏi (bế tắc, chán đời).

Đầu ra: Mức độ nghiêm trọng (0-3) và cờ has_crisis (được bật khi ở mức 2 hoặc 3), kèm theo khuyến nghị hành động cho Agent.

2.2. suggest_grounding_technique

Mục đích: Cung cấp ngay lập tức các bài tập xoa dịu khi người dùng báo cáo trạng thái căng thẳng, lo âu hoặc hoảng loạn.

Cơ chế: Nhận diện từ khóa trong chuỗi trạng thái (state) do Agent truyền vào.

Nếu có "hoảng loạn": Trả về Kỹ thuật Nối đất 5-4-3-2-1.

Nếu có "lo âu/căng thẳng": Trả về Kỹ thuật Thở hộp (Box Breathing).

Mặc định: Kỹ thuật Nhận thức Cơ thể (Body Scan).

3. Công cụ Phân tích Nhận thức & Hỗ trợ (Cognitive & Support Tools)

3.1. analyze_cognitive_distortion

Mục đích: Nhận diện các "Méo mó nhận thức" (Cognitive Distortions) thường gặp qua lời nói của người dùng.

Cơ chế quét (Regex/Keyword):

Tìm các mẫu "Tư duy trắng đen" (VD: "không bao giờ", "luôn luôn").

Tìm các mẫu "Đọc tâm trí" (VD: "chắc chắn họ nghĩ").

Tìm các mẫu "Câu lệnh Phải" (VD: "đáng lẽ ra phải").

Đầu ra: Danh sách các lỗi tư duy mắc phải và một câu hỏi/gợi ý "phản tư" (reframe) để Agent có thể dùng phản hồi lại người dùng, giúp họ nhìn nhận vấn đề khách quan hơn.

3.2. lookup_counseling_resource

Mục đích: Cung cấp thông tin liên hệ của các cơ sở y tế, đường dây nóng hỗ trợ tâm lý uy tín tại Việt Nam.

Cơ chế: Dùng Dictionary Mapping (TOPIC_ALIAS_MAP) để chuẩn hóa từ khóa tìm kiếm (VD: gõ "trẻ em" hay "bạo lực" đều quy về chủ đề child_abuse). Sau đó, lọc dữ liệu từ database nội bộ cứng (COUNSELING_RESOURCE_DATABASE).

Đầu ra: Danh sách các tổ chức, số điện thoại, giờ hoạt động và mô tả chi tiết phù hợp với chủ đề cần tìm. Nếu không rõ chủ đề, công cụ trả về toàn bộ danh bạ.

Tài liệu này được tạo tự động nhằm hỗ trợ quá trình tích hợp ReAct Agent hoặc Function Calling.