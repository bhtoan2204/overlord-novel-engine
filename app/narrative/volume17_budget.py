"""Volume 17 word budget. Chapter, part, scene, and beat targets sum exactly."""

VOLUME_TARGET = 200_000

# kind, title, requires, words, parts as (title, viewpoint, location, conflict, outcome, words)
CHAPTERS = [
    (
        "prologue",
        "Lời mở — Lệnh đã ban",
        ["theocracy-war", "ainz-performance"],
        [
            ("Phòng làm việc sau cơn giận", "Ainz Ooal Gown", "phòng làm việc", "Ainz giữ nguyên lệnh chuẩn bị tiêu diệt Thần quyền quốc Slane.", "Lệnh không bị thu hẹp thành một đợt trinh sát.", 4000),
            ("Shalltear nghe nguyên cớ", "Shalltear Bloodfallen", "hành lang tầng chín", "Shalltear biết chiến dịch bắt đầu vì cô từng bị điều khiển.", "Không có lời tha thứ dễ.", 4000),
        ],
    ),
    (
        "chapter",
        "Chương 1 — Nazarick xuất quân",
        ["theocracy-war", "shalltear-trust"],
        [
            ("Demiurge vẽ chiến dịch nhiều bước", "Demiurge", "phòng kế hoạch", "Demiurge nói rõ Nazarick chưa biết hết Bảo vật thế giới của Thần quyền quốc Slane.", "Kế hoạch thừa nhận lỗ hổng, không giả vờ đã biết hết.", 3200),
            ("Albedo nhận việc tình báo", "Albedo", "văn phòng thủ hộ", "Albedo nhận nhiệm vụ tìm Downfall of Castle and Country.", "Đơn vị bí mật không được nhắc với Ainz.", 3200),
            ("Cocytus nhận luật rút lui", "Cocytus", "sân luyện tầng năm", "Cocytus nhận lệnh rút khi thấy dấu hiệu Bảo vật thế giới.", "Mặt trận có giới hạn, không phải cuộc tàn sát.", 3200),
            ("Aura và Mare mở đường", "Aura Bella Fiora", "rừng rìa lãnh thổ", "Aura Bella Fiora đánh dấu đường tiếp tế chứ không mở cuộc tàn sát.", "Đường đi được vẽ trước khi có trận.", 3200),
            ("Shalltear không được dẫn mũi", "Shalltear Bloodfallen", "phòng ngai", "Ainz không cho Shalltear Bloodfallen dẫn mũi nhọn.", "Cô vẫn là Thủ hộ tầng, không phải mũi giáo.", 3200),
            ("Pandora's Actor giữ kinh đô", "Pandora's Actor", "phòng gương", "Pandora's Actor nhận vai giữ lễ ở kinh đô trong lúc Ainz chỉ huy.", "Mặt chính trị trong nước không đổ vì chiến dịch.", 6000),
        ],
    ),
    (
        "chapter",
        "Chương 2 — Thần quyền quốc nghe tiếng bước",
        ["theocracy-war"],
        [
            ("Đền không ngủ", "giáo sĩ trực", "thánh điện trung ương", "Giáo sĩ trực kết luận không thể thắng Nazarick bằng một trận tay đôi.", "Họ không có ảo tưởng về một trận cân sức.", 3200),
            ("Hắc điển giữ món đồ ở hậu phương", "chỉ huy Hắc điển", "doanh trại Hắc điển", "Chỉ huy Hắc điển giữ món đồ điều khiển ở hậu phương.", "Hắc điển sẵn sàng nhưng không tự sát.", 3200),
            ("Chuông chiến tranh trước đường sơ tán", "thị dân", "phố dưới thánh điện", "Thị dân nghe chuông chiến tranh mà chưa có đường sơ tán.", "Nỗi sợ đến trước quân địch.", 3200),
            ("Hội đồng hoãn Bảo vật thế giới", "thượng tế", "phòng hội đồng", "Thượng tế hoãn việc dùng lại Bảo vật thế giới vì sợ phản tác dụng.", "Quyết định dùng món đồ bị trì hoãn.", 3200),
            ("Cửa khẩu phía nam đóng", "chỉ huy biên phòng", "cửa khẩu phía nam", "Chỉ huy biên phòng đóng cửa khẩu phía nam.", "Thương nhân bị kẹt cùng với tin chiến tranh.", 3200),
            ("Lời thần không còn một miệng", "thượng tế", "phòng hội đồng", "Các phe trong giáo hội tranh nhau việc thần có đòi hỏi hủy diệt hay cố thủ.", "Trung ương mất một mệnh lệnh duy nhất trước khi quân đến.", 6000),
        ],
    ),
    (
        "chapter",
        "Chương 3 — Tìm món đồ, không tìm vinh quang",
        ["albedo-secret", "antilene-captive"],
        [
            ("Câu hỏi trong Ngục Băng", "Albedo", "Ngục Băng", "Antilene không khai ra vị trí Downfall of Castle and Country.", "Người tù không trở thành nguồn sự thật toàn năng.", 3200),
            ("Việc Albedo không nói", "Albedo", "văn phòng thủ hộ", "Albedo không nhắc đơn vị bí mật với Ainz Ooal Gown.", "Ainz vẫn không biết đơn vị đó.", 3200),
            ("Demiurge thiếu một mảnh", "Demiurge", "phòng kế hoạch", "Demiurge nhận ra mình thiếu dữ liệu mà Albedo chưa đưa.", "Hắn không trở thành người biết hết.", 3200),
            ("Kho phụ được khoanh", "Nabe", "thị trấn biên giới", "Nabe khoanh vùng một kho phụ chứ không tìm thấy Downfall of Castle and Country.", "Một địa điểm bị loại, món đồ chính còn thiếu.", 3200),
            ("Câu hỏi của sứ giả", "Ainz Ooal Gown", "phòng khách ngoại giao", "Sứ giả hỏi liệu Thần quyền quốc Slane có còn tồn tại sau chiến dịch.", "Ainz trả lời nửa thật.", 3200),
            ("Địa điểm trống", "Demiurge", "bàn báo cáo", "Demiurge báo địa điểm nghi ngờ không chứa Bảo vật thế giới.", "Chiến dịch phải đổi mũi.", 6000),
        ],
    ),
    (
        "interlude",
        "Chương xen — Hai người không nói hết",
        ["shalltear-trust", "albedo-secret"],
        [
            ("Shalltear nhìn bản đồ từ ban công", "Shalltear Bloodfallen", "ban công Đại Lăng Nazarick", "Shalltear Bloodfallen ở lại Đại Lăng Nazarick trong lúc trận đầu được vẽ.", "Nỗi nhục không thành phản loạn.", 4000),
            ("Khoảng Albedo vẫn giữ", "Albedo", "văn phòng thủ hộ", "Albedo sắp xếp tình báo mà vẫn giấu việc riêng khỏi cả Demiurge.", "Hai kế hoạch cùng chạy và không trùng khít.", 4000),
        ],
    ),
    (
        "chapter",
        "Chương 4 — Những trận không phải kết thúc",
        ["neighbors-reaction", "theocracy-war"],
        [
            ("Cửa khẩu vỡ rồi dừng", "Cocytus", "cửa khẩu phía nam", "Cocytus chiếm cửa khẩu rồi dừng vì chưa thấy dấu hiệu Bảo vật thế giới.", "Thị trấn phía sau không bị biến thành mục tiêu.", 3200),
            ("Rút để khỏi lộ món đồ", "chỉ huy biên phòng", "đồn phía nam", "Chỉ huy biên phòng rút lui để khỏi lộ món đồ điều khiển.", "Quân Slane thấy sức mạnh chênh lệch và không thắng tay đôi.", 3200),
            ("Một nước đóng cửa", "sứ giả", "triều đình láng giềng", "Sứ giả báo nước mình trung lập và đóng cửa.", "Không có liên minh với Thần quyền quốc Slane.", 3200),
            ("Hình phạt, không phải chinh phục vô hạn", "Ainz Ooal Gown", "phòng khách", "Ainz nói với triều thần rằng đây là hình phạt, không phải chinh phục vô hạn.", "Ông không lộ sự hoảng bên trong.", 3200),
            ("Sai tốc độ rút", "Demiurge", "bàn bản đồ", "Demiurge thừa nhận đã tính sai tốc độ rút của Thần quyền quốc Slane.", "Lỗi được nói ra, không bị biến thành thảm họa.", 3200),
            ("Cái giá trong kinh đô", "Sebas Tian", "kinh đô Vương quốc Pháp thuật", "Sebas Tian thấy chiến dịch đầu tiên đổi cách dân chúng nhìn Pháp vương.", "Ổn định trong nước trở thành một mặt trận riêng.", 6000),
        ],
    ),
    (
        "chapter",
        "Chương 5 — Hắc điển",
        ["theocracy-war", "shalltear-trust"],
        [
            ("Đêm món đồ suýt rời kho", "chỉ huy Hắc điển", "hầm thánh", "Chỉ huy Hắc điển chưa dám đưa Downfall of Castle and Country ra trận, rồi Shalltear Bloodfallen không lao vào khi thấy dấu hiệu Bảo vật thế giới, và hướng kho bị lộ.", "Bước ngoặt là món đồ và sự kiềm chế, không phải một trận đấu ngang tài.", 10000),
            ("Albedo đưa hướng, không đưa bí mật", "Albedo", "bàn tình báo", "Albedo đưa cho Demiurge hướng kho, không đưa bí mật riêng.", "Demiurge có đủ dữ liệu cho bước kế và vẫn không biết hết.", 3500),
            ("Không xóa mọi thành phố", "Ainz Ooal Gown", "bàn bản đồ", "Ainz chọn đánh sụp chính quyền trung ương thay vì xóa mọi thành phố.", "Mục tiêu vẫn là sự sụp đổ của chính quyền.", 3500),
            ("Hắc điển vỡ đội hình", "chỉ huy Hắc điển", "hành lang hầm", "Chỉ huy Hắc điển bỏ đội hình để giấu món đồ.", "Họ không còn một mặt trận để phản công.", 3500),
            ("Shalltear không được nhát cuối", "Shalltear Bloodfallen", "đồi thông", "Shalltear Bloodfallen rời đồi thông mà không được giao việc kết liễu.", "Việc cô bị điều khiển năm xưa không được trả bằng một nhát kiếm.", 3500),
        ],
    ),
    (
        "chapter",
        "Chương 6 — Phòng tuyến gãy",
        ["theocracy-war"],
        [
            ("Kho phụ thất thủ", "Cocytus", "kho phụ", "Cocytus chiếm kho phụ và không thấy Downfall of Castle and Country.", "Một phần thánh tích bị thu, món đồ chính vẫn thiếu.", 3200),
            ("Mất liên lạc phía nam", "thượng tế", "phòng hội đồng", "Thượng tế mất liên lạc với cửa khẩu phía nam.", "Mệnh lệnh trung ương bắt đầu mâu thuẫn.", 3200),
            ("Dân rút, không bị săn", "thị dân", "phố dưới", "Thị dân sơ tán mà không bị Nazarick đuổi theo.", "Sơ tán quá muộn nhưng không thành mục tiêu.", 3200),
            ("Mare khóa đường", "Mare Bello Fiore", "đường núi", "Mare Bello Fiore khóa đường tiếp tế.", "Phòng tuyến đói thông tin trước khi đói lương.", 3200),
            ("Chính quyền mất thống nhất", "Demiurge", "bàn bản đồ", "Demiurge kết luận chính quyền trung ương đã mất thống nhất.", "Ainz chấp nhận bước vào thánh điện.", 3200),
            ("Nước ngoài viết như thể Slane đang tắt", "sứ giả", "triều đình láng giềng", "Sứ giả soạn công hàm theo giả định Thần quyền quốc Slane không còn giữ được biên giới.", "Áp lực chính trị đến trước khi thánh điện sụp.", 6000),
        ],
    ),
    (
        "chapter",
        "Chương 7 — Thánh điện không còn là một nước",
        ["theocracy-war", "antilene-captive"],
        [
            ("Cửa thánh điện", "Ainz Ooal Gown", "sân thánh điện", "Ainz vào thánh điện trung ương để kết thúc chính quyền, không để mở một tập sau.", "Mục tiêu của tập được thực hiện tại đây.", 3200),
            ("Hội đồng không còn đầu hàng được", "thượng tế", "phòng hội đồng", "Thượng tế không còn giữ được hội đồng.", "Một phần bỏ chạy, một phần ở lại.", 3200),
            ("Thu Downfall of Castle and Country", "Albedo", "hầm thánh", "Albedo thu Downfall of Castle and Country trước khi nó được kích hoạt.", "Món đồ không được dùng thêm lần nữa trong tập này.", 6000),
            ("Shalltear đứng ngoài cửa", "Shalltear Bloodfallen", "sân thánh điện", "Shalltear Bloodfallen chứng kiến chính quyền sụp mà không được giao nhát cuối.", "Ainz không biến điều đó thành bài học rẻ.", 3200),
            ("Antilene vẫn trong băng", "Antilene", "Ngục Băng", "Antilene vẫn ở trong Ngục Băng sau khi Thần quyền quốc Slane sụp.", "Cô không được thả như phần thưởng.", 3200),
            ("Những người từng ra lệnh", "thượng tế", "hành lang thánh điện", "Những người từng ra lệnh hoặc bỏ chạy hoặc bị giữ, và các thành phố không bị xóa trong một đêm.", "Sụp đổ là sụp đổ của chính quyền, không phải của mọi đường phố.", 3200),
        ],
    ),
    (
        "chapter",
        "Chương 8 — Cái giá của một vùng trống",
        ["neighbors-reaction", "elf-vacuum"],
        [
            ("Sebas nghe tin sụp", "Sebas Tian", "kinh đô", "Sebas Tian nghe tin chính quyền Slane đã sụp.", "Chiến thắng được kể có kiểm soát.", 4000),
            ("Dân chạy, không phải quân", "Aura Bella Fiora", "rừng phía đông", "Aura Bella Fiora gặp dân chạy nạn chứ không gặp một đội quân.", "Cô không mở một cuộc săn.", 4000),
            ("Khoảng trống tộc elf còn đó", "Mare Bello Fiore", "bìa rừng elf", "Mare Bello Fiore thấy khoảng trống quyền lực tộc elf vẫn còn.", "Chiến tranh mới không lập một vua elf.", 4000),
            ("Công nhận một nước đã mất", "Ainz Ooal Gown", "phòng khách", "Sứ giả công nhận Thần quyền quốc Slane không còn là một nước.", "Công nhận thực tế không được gọi là hòa bình.", 4000),
            ("Việc mới không phải chiến dịch còn dang", "Demiurge", "phòng kế hoạch", "Demiurge ghi vùng trống quyền lực là xung đột mới, không phải chiến dịch còn dang.", "Tập này đã xong chiến dịch Slane.", 4000),
        ],
    ),
    (
        "epilogue",
        "Lời kết — Thế giới đã thấy",
        ["theocracy-war", "ainz-performance"],
        [
            ("Ainz sau buổi triều", "Ainz Ooal Gown", "phòng làm việc", "Ainz xác nhận Thần quyền quốc Slane đã bị đánh bại trong tập này.", "Lệnh của ông đã đi đến cùng trong tập 17.", 4000),
            ("Không có câu tha, có một bức thư", "Shalltear Bloodfallen", "hành lang", "Shalltear Bloodfallen không nhận được lời tha thứ, và Albedo nhận công hàm của một nước đang tính lại vị trí của mình.", "Chiến thắng không khép thế giới, nhưng khép chiến dịch này.", 4000),
        ],
    ),
]


def split_exact(total: int, count: int) -> list[int]:
    count = max(1, count)
    base, remainder = divmod(int(total), count)
    return [base + (1 if index < remainder else 0) for index in range(count)]


def scene_count_for(words: int) -> int:
    if words >= 8000:
        return 8
    if words >= 5000:
        return 6
    return 4


def beat_count_for(words: int) -> int:
    count = max(1, round(words / 250)) if words else 1
    while count > 1 and words / count > 350:
        count += 1
    while count > 1 and words / count < 150:
        count -= 1
    return count


def _scenes(part_title: str, viewpoint: str, location: str, conflict: str, outcome: str, words: int) -> list[dict]:
    phases = ["Mở việc", "Đối thoại hoặc hành động", "Quyết định", "Hệ quả", "Diễn biến thêm", "Bước chuyển", "Hệ quả phụ", "Chốt phần"]
    sizes = split_exact(words, scene_count_for(words))
    scenes = []
    for index, size in enumerate(sizes, start=1):
        phase = phases[index - 1]
        beat_sizes = split_exact(size, beat_count_for(size))
        beats = []
        for beat_index, beat_words in enumerate(beat_sizes, start=1):
            beats.append(
                {
                    "title": f"{part_title} — nhịp {index}.{beat_index}",
                    "action": f"{viewpoint} tại {location}, nhịp {index}.{beat_index} của «{part_title}»: {conflict}",
                    "purpose": phase,
                    "new_information": conflict if beat_index == len(beat_sizes) else f"Nhịp {beat_index} của {part_title} thêm một hệ quả chưa viết.",
                    "objective": outcome if beat_index == len(beat_sizes) else phase,
                    "target_words": beat_words,
                }
            )
        scenes.append(
            {
                "title": f"{part_title} — {phase}",
                "viewpoint": viewpoint,
                "location": location,
                "objective": f"{phase}: {conflict}",
                "outcome": outcome,
                "events": [conflict],
                "target_words": size,
                "beats": beats,
            }
        )
    return scenes


def planned_volume() -> dict:
    arcs = [
        {"title": "Quyết định", "chapters": []},
        {"title": "Chuẩn bị", "chapters": []},
        {"title": "Tình báo và trận đầu", "chapters": []},
        {"title": "Sụp đổ", "chapters": []},
        {"title": "Sau chiến dịch", "chapters": []},
    ]
    arc_for = {
        "Lời mở — Lệnh đã ban": 0,
        "Chương 1 — Nazarick xuất quân": 1,
        "Chương 2 — Thần quyền quốc nghe tiếng bước": 1,
        "Chương 3 — Tìm món đồ, không tìm vinh quang": 2,
        "Chương xen — Hai người không nói hết": 2,
        "Chương 4 — Những trận không phải kết thúc": 2,
        "Chương 5 — Hắc điển": 3,
        "Chương 6 — Phòng tuyến gãy": 3,
        "Chương 7 — Thánh điện không còn là một nước": 3,
        "Chương 8 — Cái giá của một vùng trống": 4,
        "Lời kết — Thế giới đã thấy": 4,
    }
    for kind, title, requires, parts in CHAPTERS:
        built_parts = []
        for part_title, viewpoint, location, conflict, outcome, words in parts:
            built_parts.append(
                {
                    "title": part_title,
                    "viewpoint": viewpoint,
                    "location": location,
                    "conflict": conflict,
                    "outcome": outcome,
                    "target_words": words,
                    "short_transition": False,
                    "scenes": _scenes(part_title, viewpoint, location, conflict, outcome, words),
                }
            )
        arcs[arc_for[title]]["chapters"].append(
            {
                "kind": kind,
                "title": title,
                "summary": parts[0][3],
                "requires": requires,
                "target_words": sum(part[5] for part in parts),
                "parts": built_parts,
            }
        )
    return {"target_words": VOLUME_TARGET, "arcs": [arc for arc in arcs if arc["chapters"]]}


def budget_audit(tree: dict) -> list[str]:
    """Return human-readable mismatches. An empty list means the sums agree."""
    problems = []
    volume_sum = 0
    for arc in tree["arcs"]:
        for chapter in arc["chapters"]:
            part_sum = sum(part["target_words"] for part in chapter["parts"])
            volume_sum += part_sum
            if part_sum != chapter["target_words"]:
                problems.append(f"{chapter['title']}: parts {part_sum} != chapter {chapter['target_words']}")
            for part in chapter["parts"]:
                scene_sum = sum(scene["target_words"] for scene in part["scenes"])
                if scene_sum != part["target_words"]:
                    problems.append(f"{part['title']}: scenes {scene_sum} != part {part['target_words']}")
                for scene in part["scenes"]:
                    beat_sum = sum(beat["target_words"] for beat in scene["beats"])
                    if beat_sum != scene["target_words"]:
                        problems.append(f"{scene['title']}: beats {beat_sum} != scene {scene['target_words']}")
                    for beat in scene["beats"]:
                        if not 150 <= beat["target_words"] <= 350:
                            problems.append(f"{beat['title']}: beat {beat['target_words']} outside 150–350")
    if volume_sum != tree["target_words"]:
        problems.append(f"allocated {volume_sum} != volume target {tree['target_words']}")
    return problems
