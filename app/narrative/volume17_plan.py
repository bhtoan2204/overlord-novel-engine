"""Fan-fiction plan: the Slane Theocracy falls in this volume, not in a later one."""


def _scene(title, viewpoint, location, participants, tone, objective, outcome, event):
    return {
        "title": title,
        "viewpoint": viewpoint,
        "location": location,
        "participants": participants,
        "tone": tone,
        "objective": objective,
        "outcome": outcome,
        "events": [event],
    }


def _chapter(title, summary, kind, requires, caused_by, scenes):
    return {
        "title": title,
        "summary": summary,
        "kind": kind,
        "requires": requires,
        "caused_by": caused_by,
        "uncertainties": [],
        "scenes": scenes,
    }


BLUEPRINT = [
    {
        "arc": "Quyết định chiến tranh",
        "chapters": [
            _chapter(
                "Lời mở — Lệnh đã ban",
                "Ainz giữ lệnh chuẩn bị tiêu diệt Thần quyền quốc Slane, và Nazarick phải biến lệnh đó thành một chiến dịch có thể chịu được Bảo vật thế giới.",
                "prologue",
                ["theocracy-war", "ainz-performance"],
                "Ainz đã biết Thần quyền quốc Slane đứng sau việc Shalltear bị điều khiển.",
                [
                    _scene("Phòng làm việc sau cơn giận", "Ainz Ooal Gown", "phòng làm việc của Ainz", ["Ainz Ooal Gown", "Albedo", "Demiurge"], "lạnh", "Ainz xác nhận lệnh chiến tranh.", "Lệnh tiêu diệt được giữ nguyên.", "Ainz giữ nguyên lệnh chuẩn bị tiêu diệt Thần quyền quốc Slane."),
                    _scene("Câu hỏi Shalltear không dám hỏi", "Shalltear Bloodfallen", "hành lang tầng chín", ["Shalltear Bloodfallen", "Ainz Ooal Gown"], "day dứt", "Shalltear nghe mình là nguyên cớ chiến tranh.", "Shalltear không được hứa tha thứ dễ dàng.", "Shalltear biết chiến dịch bắt đầu vì cô từng bị điều khiển."),
                    _scene("Demiurge vẽ chiến dịch", "Demiurge", "phòng kế hoạch", ["Demiurge", "Albedo"], "tính toán", "Demiurge lập chiến dịch nhiều bước, không phải một đêm hủy diệt.", "Kế hoạch thừa nhận khoảng trống về Bảo vật thế giới.", "Demiurge nói rõ Nazarick chưa biết hết Bảo vật thế giới còn lại của Thần quyền quốc Slane."),
                    _scene("Albedo nhận việc tình báo", "Albedo", "văn phòng thủ hộ", ["Albedo", "Demiurge"], "kín", "Albedo điều mạng lưới mà không để Ainz thấy đơn vị bí mật.", "Mệnh lệnh tình báo được giao.", "Albedo nhận nhiệm vụ tìm Downfall of Castle and Country và các Bảo vật thế giới khác."),
                ],
            ),
        ],
    },
    {
        "arc": "Chuẩn bị và phòng thủ",
        "chapters": [
            _chapter(
                "Nazarick xuất quân",
                "Các Thủ hộ tầng nhận nhiệm vụ có giới hạn. Sức mạnh không phải vấn đề. Vấn đề là món đồ có thể cướp quyền điều khiển.",
                "chapter",
                ["shalltear-trust", "theocracy-war"],
                "Lệnh chiến tranh đã được xác nhận.",
                [
                    _scene("Cocytus nhận mặt trận", "Cocytus", "sân luyện tầng năm", ["Cocytus", "Ainz Ooal Gown"], "nghiêm", "Cocytus được giao một mặt trận có luật rút lui.", "Cocytus chấp nhận không truy đuổi nếu có dấu hiệu Bảo vật thế giới.", "Cocytus nhận lệnh rút khi thấy dấu hiệu Bảo vật thế giới."),
                    _scene("Aura và Mare mở đường", "Aura Bella Fiora", "rừng rìa lãnh thổ", ["Aura Bella Fiora", "Mare Bello Fiore"], "căng", "Hai đứa trẻ chuẩn bị trinh sát, không phải tàn sát.", "Đường tiếp tế được vẽ.", "Aura Bella Fiora đánh dấu đường tiếp tế chứ không mở cuộc tàn sát."),
                    _scene("Sebas ở kinh đô", "Sebas Tian", "kinh đô Vương quốc Pháp thuật", ["Sebas Tian", "Ainz Ooal Gown"], "điềm tĩnh", "Sebas giữ mặt chính trị trong nước.", "Dân chúng chưa được kể toàn bộ chiến tranh.", "Sebas Tian được lệnh giữ sự ổn định ở kinh đô."),
                    _scene("Shalltear xin một nhiệm vụ có giới hạn", "Shalltear Bloodfallen", "phòng ngai", ["Shalltear Bloodfallen", "Ainz Ooal Gown", "Albedo"], "căng", "Shalltear muốn ra trận nhưng bị giới hạn.", "Cô không được dẫn mũi nhọn.", "Ainz không cho Shalltear Bloodfallen dẫn mũi nhọn."),
                    _scene("Pandora's Actor đóng vai Pháp vương", "Pandora's Actor", "phòng gương", ["Pandora's Actor", "Ainz Ooal Gown"], "diễn", "Một bản sao giữ nghi lễ trong nước.", "Ainz thật được rảnh để chỉ huy.", "Pandora's Actor nhận vai giữ lễ ở kinh đô."),
                    _scene("Kho chưa kiểm được", "Demiurge", "kho hồ sơ", ["Demiurge", "Albedo"], "dè chừng", "Danh sách Bảo vật thế giới vẫn thủng.", "Kế hoạch ghi rõ các lỗ hổng.", "Demiurge ghi các lỗ hổng tình báo vào kế hoạch, không giả vờ đã biết hết."),
                ],
            ),
            _chapter(
                "Thần quyền quốc nghe tiếng bước",
                "Slane nhận ra Vương quốc Pháp thuật không còn chờ. Họ chuẩn bị bằng đức tin, quân đội và món đồ họ không dám dùng bừa.",
                "chapter",
                ["theocracy-war"],
                "Nazarick đã bắt đầu chuẩn bị công khai hơn.",
                [
                    _scene("Đền không ngủ", "giáo sĩ trực", "thánh điện trung ương", ["giáo sĩ trực"], "sợ", "Giới chức hiểu kẻ thù không phải một nước người.", "Họ không có ảo tưởng thắng tay đôi.", "Giáo sĩ trực kết luận không thể thắng Nazarick bằng một trận tay đôi."),
                    _scene("Hắc điển được gọi", "chỉ huy Hắc điển", "doanh trại Hắc điển", ["chỉ huy Hắc điển"], "nặng", "Hắc điển nhận lệnh sẵn sàng, không phải tự sát.", "Họ giữ món đồ nguy hiểm ở hậu phương.", "Chỉ huy Hắc điển giữ món đồ điều khiển ở hậu phương."),
                    _scene("Dân thành nghe chuông", "thị dân", "phố dưới thánh điện", ["thị dân"], "hoang mang", "Tin chiến tranh xuống phố trước khi có kế hoạch sơ tán.", "Sợ hãi bắt đầu trước quân địch.", "Thị dân nghe chuông chiến tranh mà chưa có đường sơ tán."),
                    _scene("Giáo hội tranh nhau lời thần", "thượng tế", "phòng hội đồng", ["thượng tế"], "chia rẽ", "Nội bộ không thống nhất có nên dùng lại Bảo vật thế giới.", "Quyết định bị hoãn vì sợ phản tác dụng.", "Thượng tế hoãn việc dùng lại Bảo vật thế giới vì sợ phản tác dụng."),
                    _scene("Biên giới đóng cửa", "chỉ huy biên phòng", "cửa khẩu phía nam", ["chỉ huy biên phòng"], "gấp", "Biên giới siết lại.", "Thương nhân bị kẹt.", "Chỉ huy biên phòng đóng cửa khẩu phía nam."),
                ],
            ),
        ],
    },
    {
        "arc": "Tình báo và những trận đầu",
        "chapters": [
            _chapter(
                "Tìm món đồ, không tìm vinh quang",
                "Albedo tìm Downfall of Castle and Country. Demiurge không được biết mọi bí mật của cô.",
                "chapter",
                ["albedo-secret", "antilene-captive"],
                "Chiến dịch cần vị trí các Bảo vật thế giới.",
                [
                    _scene("Câu hỏi với người trong băng", "Albedo", "Ngục Băng", ["Albedo", "Antilene"], "lạnh", "Albedo hỏi Antilene về Hắc điển mà không tra tấn cho vui.", "Antilene không bị biến thành nguồn sự thật toàn năng.", "Antilene không khai ra vị trí Downfall of Castle and Country."),
                    _scene("Mạng lưới ngoài lăng", "Albedo", "văn phòng thủ hộ", ["Albedo"], "kín", "Cô điều tra mà giữ đơn vị bí mật ngoài tầm Ainz.", "Ainz không thấy tên đơn vị đó.", "Albedo không nhắc đơn vị bí mật với Ainz Ooal Gown."),
                    _scene("Demiurge thiếu một mảnh", "Demiurge", "phòng kế hoạch", ["Demiurge"], "khó chịu", "Kế hoạch của Demiurge có lỗ hổng vì Albedo giấu.", "Hắn không trở thành người biết hết.", "Demiurge nhận ra mình thiếu dữ liệu mà Albedo chưa đưa."),
                    _scene("Bản đồ đức tin", "Nabe", "thị trấn biên giới", ["Nabe"], "im", "Nabe theo dấu một linh mục chạy trốn.", "Một kho phụ được khoanh vùng.", "Nabe khoanh vùng một kho phụ chứ không tìm thấy Downfall of Castle and Country."),
                    _scene("Tin đồn từ nước láng giềng", "Ainz Ooal Gown", "phòng khách ngoại giao", ["Ainz Ooal Gown", "sứ giả"], "chính trị", "Một nước hỏi Vương quốc Pháp thuật sắp làm gì.", "Ainz trả lời nửa thật.", "Sứ giả hỏi liệu Thần quyền quốc Slane có còn tồn tại sau chiến dịch."),
                    _scene("Kho trống", "Demiurge", "báo cáo đêm", ["Demiurge", "Albedo"], "căng", "Một địa điểm nghi ngờ hóa ra trống.", "Chiến dịch phải đổi mũi.", "Demiurge báo địa điểm nghi ngờ không chứa Bảo vật thế giới."),
                ],
            ),
            _chapter(
                "Những trận không phải là kết thúc",
                "Va chạm đầu tiên làm lộ tính toán sai của cả hai bên, chưa hạ được thánh điện.",
                "chapter",
                ["neighbors-reaction", "theocracy-war"],
                "Tình báo chưa khóa được món đồ.",
                [
                    _scene("Cửa khẩu vỡ", "Cocytus", "cửa khẩu phía nam", ["Cocytus"], "thẳng", "Cocytus chiếm cửa khẩu và dừng đúng lệnh.", "Không có cuộc tàn sát thị trấn phía sau.", "Cocytus chiếm cửa khẩu rồi dừng vì chưa thấy dấu hiệu Bảo vật thế giới."),
                    _scene("Phép thuật kinh hoàng và một cái bẫy không nổ", "chỉ huy biên phòng", "đồn phía nam", ["chỉ huy biên phòng"], "tuyệt vọng", "Quân Slane thấy sức mạnh chênh lệch.", "Họ rút để giữ món đồ, không phải để thắng.", "Chỉ huy biên phòng rút lui để khỏi lộ món đồ điều khiển."),
                    _scene("Nước láng giềng đóng cửa", "sứ giả", "triều đình láng giềng", ["sứ giả"], "sợ", "Một nước từ chối cho quân nào đi qua.", "Họ không liên minh với Slane.", "Sứ giả báo nước mình trung lập và đóng cửa."),
                    _scene("Ainz diễn trước triều thần", "Ainz Ooal Gown", "phòng khách", ["Ainz Ooal Gown", "triều thần"], "diễn", "Ainz giải thích chiến tranh như một hình phạt có chủ đích.", "Ông không lộ sự hoảng bên trong.", "Ainz nói với triều thần rằng đây là hình phạt, không phải chinh phục vô hạn."),
                    _scene("Shalltear nhìn bản đồ từ xa", "Shalltear Bloodfallen", "ban công lăng", ["Shalltear Bloodfallen"], "tủi", "Cô thấy chiến dịch đi mà không có mình ở mũi.", "Nỗi nhục không biến thành phản loạn.", "Shalltear Bloodfallen ở lại Đại Lăng Nazarick trong trận đầu."),
                    _scene("Sai một nhịp", "Demiurge", "bàn bản đồ", ["Demiurge", "Ainz Ooal Gown"], "căng", "Demiurge nhận một tính toán sai về tốc độ rút của Slane.", "Ainz không biến lỗi đó thành thảm họa.", "Demiurge thừa nhận đã tính sai tốc độ rút của Thần quyền quốc Slane."),
                ],
            ),
        ],
    },
    {
        "arc": "Hắc điển và sụp đổ",
        "chapters": [
            _chapter(
                "Hắc điển",
                "Bước ngoặt là món đồ và những người được giao giữ nó, không phải một trận đấu ngang tài.",
                "chapter",
                ["theocracy-war", "shalltear-trust"],
                "Trận đầu chưa chạm thánh điện.",
                [
                    _scene("Đêm trước khi món đồ rời kho", "chỉ huy Hắc điển", "hầm thánh", ["chỉ huy Hắc điển"], "nặng", "Hắc điển bàn có mang Downfall of Castle and Country ra trận hay không.", "Họ sợ dùng nó vào kẻ đã từng gãy một lần.", "Chỉ huy Hắc điển chưa dám đưa Downfall of Castle and Country ra trận."),
                    _scene("Shalltear được gọi, với một sợi xích", "Ainz Ooal Gown", "phòng ngai", ["Ainz Ooal Gown", "Shalltear Bloodfallen", "Albedo"], "căng", "Ainz cho Shalltear một việc hẹp vì cô là người hiểu nỗi sợ bị điều khiển.", "Cô đi cùng điều kiện rút ngay.", "Ainz giao Shalltear Bloodfallen một nhiệm vụ hẹp với điều kiện rút ngay."),
                    _scene("Gặp nhau không phải để so kiếm", "Shalltear Bloodfallen", "đồi thông", ["Shalltear Bloodfallen", "chỉ huy Hắc điển"], "lạnh", "Hai bên gặp nhau. Shalltear không lao vào.", "Hắc điển thấy cô không còn là con rối lần trước.", "Shalltear Bloodfallen không lao vào khi thấy dấu hiệu Bảo vật thế giới."),
                    _scene("Món đồ được giấu lần nữa", "chỉ huy Hắc điển", "hầm phụ", ["chỉ huy Hắc điển"], "tuyệt vọng", "Việc không dùng món đồ cũng là một thất bại, vì Nazarick vẫn tiến.", "Kho chính bị lộ gián tiếp.", "Chỉ huy Hắc điển rút khỏi đồi thông và để lộ hướng kho."),
                    _scene("Albedo khóa hướng", "Albedo", "bàn tình báo", ["Albedo", "Demiurge"], "sắc", "Hai người ghép hướng kho, dù Albedo vẫn giấu một việc khác.", "Demiurge có đủ dữ liệu cho bước kế.", "Albedo đưa cho Demiurge hướng kho, không đưa bí mật riêng."),
                    _scene("Ainz quyết định không hủy cả nước trong một đêm", "Ainz Ooal Gown", "bàn bản đồ", ["Ainz Ooal Gown", "Demiurge"], "nặng", "Ông chọn siết trung tâm quyền lực thay vì xóa mọi thành phố.", "Mục tiêu vẫn là sự sụp đổ của chính quyền.", "Ainz chọn đánh sụp chính quyền trung ương thay vì xóa mọi thành phố."),
                ],
            ),
            _chapter(
                "Phòng tuyến gãy",
                "Khi kho và đường rút không còn, quân Slane không còn cách giữ một mặt trận.",
                "chapter",
                ["theocracy-war"],
                "Hướng kho đã lộ.",
                [
                    _scene("Kho phụ thất thủ", "Cocytus", "kho phụ", ["Cocytus"], "thẳng", "Cocytus lấy kho phụ. Món đồ chính không ở đó.", "Một phần thánh tích bị thu.", "Cocytus chiếm kho phụ và không thấy Downfall of Castle and Country."),
                    _scene("Thánh điện mất liên lạc với biên giới", "thượng tế", "phòng hội đồng", ["thượng tế"], "vỡ", "Trung ương mất tin từ phía nam.", "Mệnh lệnh bắt đầu mâu thuẫn.", "Thượng tế mất liên lạc với cửa khẩu phía nam."),
                    _scene("Đường rút của dân", "thị dân", "phố dưới", ["thị dân"], "hoảng", "Sơ tán bắt đầu quá muộn.", "Nazarick không biến cuộc sơ tán thành mục tiêu.", "Thị dân sơ tán mà không bị Nazarick đuổi theo."),
                    _scene("Hắc điển vỡ đội hình", "chỉ huy Hắc điển", "hành lang hầm", ["chỉ huy Hắc điển"], "tuyệt vọng", "Đội tinh nhuệ không còn mặt trận để giữ.", "Họ chuyển sang giấu món đồ, không phản công.", "Chỉ huy Hắc điển bỏ đội hình để giấu món đồ."),
                    _scene("Mare khóa đường tiếp tế", "Mare Bello Fiore", "đường núi", ["Mare Bello Fiore", "Aura Bella Fiora"], "im", "Hai anh em khóa đường mà không san phẳng làng.", "Phòng tuyến đói thông tin trước khi đói lương.", "Mare Bello Fiore khóa đường tiếp tế."),
                    _scene("Demiurge nhìn thấy điểm gãy", "Demiurge", "bàn bản đồ", ["Demiurge", "Ainz Ooal Gown"], "tính toán", "Hắn chỉ ra chính quyền đã không còn ra một mệnh lệnh thống nhất.", "Ainz chấp nhận bước vào thánh điện.", "Demiurge kết luận chính quyền trung ương đã mất thống nhất."),
                ],
            ),
            _chapter(
                "Thánh điện không còn là một nước",
                "Chính quyền Slane sụp. Món đồ nguy hiểm bị thu hoặc bị chôn cùng với người giữ nó. Đây là hồi kết của chiến dịch, không phải lời hứa cho tập sau.",
                "chapter",
                ["theocracy-war", "antilene-captive"],
                "Phòng tuyến đã gãy.",
                [
                    _scene("Cửa thánh điện", "Ainz Ooal Gown", "sân thánh điện", ["Ainz Ooal Gown", "Albedo", "Demiurge"], "lạnh", "Ainz vào trung tâm với một mục tiêu chính trị.", "Ông không biến đây thành màn tàn sát vô danh.", "Ainz vào thánh điện trung ương để kết thúc chính quyền, không để mở một tập sau."),
                    _scene("Hội đồng vỡ", "thượng tế", "phòng hội đồng", ["thượng tế"], "sụp", "Những người ra lệnh không còn thống nhất cả việc đầu hàng.", "Một phần bỏ chạy, một phần ở lại.", "Thượng tế không còn giữ được hội đồng."),
                    _scene("Món đồ cuối", "Albedo", "hầm thánh", ["Albedo", "chỉ huy Hắc điển"], "sắc", "Albedo tìm thấy nơi giấu Downfall of Castle and Country.", "Món đồ không được dùng thêm lần nữa trong tập này.", "Albedo thu Downfall of Castle and Country trước khi nó được kích hoạt."),
                    _scene("Shalltear đứng ngoài cửa", "Shalltear Bloodfallen", "sân thánh điện", ["Shalltear Bloodfallen", "Ainz Ooal Gown"], "nặng", "Cô thấy nguyên cớ của mình kết thúc mà không được là người kết liễu.", "Ainz không biến đó thành bài học rẻ tiền.", "Shalltear Bloodfallen chứng kiến chính quyền sụp mà không được giao nhát cuối."),
                    _scene("Antilene nghe tin nước mình", "Antilene", "Ngục Băng", ["Antilene", "Albedo"], "rỗng", "Tin đến chỗ người đang bị giam. Cô không được thả như phần thưởng.", "Số phận cô vẫn là tù nhân.", "Antilene vẫn ở trong Ngục Băng sau khi Thần quyền quốc Slane sụp."),
                ],
            ),
        ],
    },
    {
        "arc": "Sau khi một cường quốc biến mất",
        "chapters": [
            _chapter(
                "Cái giá của một vùng trống",
                "Xóa một chính quyền không tạo ra hòa bình. Nó tạo ra khoảng trống, người chạy nạn và những nước đang tính nước đi kế.",
                "chapter",
                ["neighbors-reaction", "elf-vacuum"],
                "Thần quyền quốc Slane đã mất chính quyền trung ương.",
                [
                    _scene("Kinh đô Pháp thuật nghe chuông khác", "Sebas Tian", "kinh đô", ["Sebas Tian"], "điềm", "Trong nước, chiến thắng được kể có kiểm soát.", "Sebas thấy khoảng trống phía sau lời tuyên bố.", "Sebas Tian nghe tin chính quyền Slane đã sụp."),
                    _scene("Người chạy về phía rừng", "Aura Bella Fiora", "rừng phía đông", ["Aura Bella Fiora"], "cảnh giác", "Dòng người chạy không phải quân.", "Aura không mở một cuộc săn.", "Aura Bella Fiora gặp dân chạy nạn chứ không gặp một đội quân."),
                    _scene("Khoảng trống của tộc elf", "Mare Bello Fiore", "bìa rừng elf", ["Mare Bello Fiore"], "lặng", "Cái chết của Decem vẫn để lại một khoảng trống, và chiến tranh mới không lấp nó.", "Không có vua elf mới trong cảnh này.", "Mare Bello Fiore thấy khoảng trống quyền lực tộc elf vẫn còn."),
                    _scene("Một nước viết công hàm", "Ainz Ooal Gown", "phòng khách", ["Ainz Ooal Gown", "sứ giả"], "chính trị", "Nước láng giềng công nhận thực tế mới mà không gọi đó là hòa bình.", "Ainz nhận ra chiến thắng mở ra câu hỏi kế tiếp.", "Sứ giả công nhận Thần quyền quốc Slane không còn là một nước."),
                    _scene("Demiurge ghi những việc chưa xong", "Demiurge", "phòng kế hoạch", ["Demiurge", "Albedo"], "tỉnh", "Hắn liệt kê xung đột mới: vùng trống, món đồ đã thu, và việc Albedo vẫn giữ một khoảng tối.", "Tập này đã xong chiến dịch, chưa xong thế giới.", "Demiurge ghi vùng trống quyền lực là xung đột mới, không phải chiến dịch còn dang."),
                ],
            ),
            _chapter(
                "Lời kết — Thế giới đã thấy",
                "Các nước khác nhìn một cường quốc biến mất và hiểu Vương quốc Pháp thuật làm được việc đó.",
                "epilogue",
                ["theocracy-war", "ainz-performance"],
                "Chính quyền Slane đã sụp trong tập này.",
                [
                    _scene("Ainz một mình sau buổi triều", "Ainz Ooal Gown", "phòng làm việc", ["Ainz Ooal Gown"], "rỗng", "Ông biết mình đã đi đến cùng lệnh của mình.", "Sự diễn trước thuộc hạ chưa hết.", "Ainz xác nhận Thần quyền quốc Slane đã bị đánh bại trong tập này."),
                    _scene("Shalltear không được một câu tha", "Shalltear Bloodfallen", "hành lang", ["Shalltear Bloodfallen"], "day dứt", "Không có cảnh hòa giải dễ. Cô vẫn là Thủ hộ tầng.", "Vết cũ còn đó sau chiến thắng.", "Shalltear Bloodfallen không nhận được lời tha thứ."),
                    _scene("Bức thư từ một triều đình xa", "Albedo", "văn phòng", ["Albedo"], "kín", "Một nước khác bắt đầu tính cách sống cạnh người thắng.", "Xung đột kế tiếp được gợi, không được mở trận.", "Albedo nhận công hàm của một nước đang tính lại vị trí của mình."),
                ],
            ),
        ],
    },
]
