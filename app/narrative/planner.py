"""Volume, arc, chapter, scene, and beat planning.

The deterministic planner composes an unofficial Volume 17 from unresolved plotlines.
It does not treat fan theories as canon. Uncertainties stay attached as alternatives.
"""

import uuid

from sqlalchemy.orm import Session

from app.core.disclaimer import DISCLAIMER
from app.db.models import OutlineNode, Plotline, Project

BLUEPRINT = [
    {
        "arc": "Mệnh lệnh và nỗi sợ Bảo vật thế giới",
        "chapters": [
            {
                "kind": "prologue",
                "title": "Lời mở — Mệnh lệnh còn nóng",
                "requires": ["ainz-performance", "theocracy-war"],
                "summary": "Ngay sau khi rời Ngục Băng, Ainz muốn trả đũa Thần quyền quốc Slane, nhưng Demiurge buộc cuộc chiến phải tính đến Bảo vật thế giới đã từng khuất phục Shalltear.",
                "scenes": [
                    {
                        "title": "Phòng làm việc sau cơn giận",
                        "viewpoint": "Ainz Ooal Gown",
                        "location": "Đại Lăng Nazarick",
                        "participants": ["Ainz Ooal Gown", "Albedo"],
                        "tone": "nén giận",
                        "objective": "Cho thấy Ainz ra lệnh tổng động viên mà vẫn phải diễn vai một quân vương không run.",
                        "outcome": "Albedo nhận lệnh dừng mọi hoạt động ngoài phòng thủ.",
                        "events": ["Ainz ra lệnh đình chỉ mọi hoạt động không phục vụ phòng thủ Đại Lăng Nazarick."],
                    },
                    {
                        "title": "Câu hỏi mà chiến thắng cũ không trả lời",
                        "viewpoint": "Demiurge",
                        "location": "Đại Lăng Nazarick",
                        "participants": ["Demiurge", "Ainz Ooal Gown", "Cocytus"],
                        "tone": "lạnh và chính xác",
                        "objective": "Đặt Bảo vật thế giới thành ràng buộc chiến lược, không phải một lời nhắc cho có.",
                        "outcome": "Phương án đánh dàn trải bị gạt sang nhánh dự phòng.",
                        "events": ["Demiurge nêu rủi ro Bảo vật thế giới từng dùng để điều khiển Shalltear."],
                    },
                ],
            },
            {
                "kind": "chapter",
                "title": "Chương 1 — Vết thương của Shalltear",
                "requires": ["shalltear-trust", "theocracy-war"],
                "summary": "Shalltear biết cuộc chiến này bắt đầu từ nỗi nhục của chính mình. Cô muốn được dùng, nhưng không muốn được an ủi.",
                "scenes": [
                    {
                        "title": "Người từng bị gọi tên",
                        "viewpoint": "Shalltear Bloodfallen",
                        "location": "Đại Lăng Nazarick",
                        "participants": ["Shalltear Bloodfallen", "Aura Bella Fiora"],
                        "tone": "tủi và sắc",
                        "objective": "Viết Shalltear như một tướng lĩnh mang mặc cảm, không như một nạn nhân cần diễn thuyết.",
                        "outcome": "Shalltear xin một nhiệm vụ có giới hạn rõ, thay vì một lời hứa trả thù vô hạn.",
                        "events": ["Shalltear nhận ra Thần quyền quốc Slane là phía đã điều khiển mình."],
                    }
                ],
            },
        ],
    },
    {
        "arc": "Bàn cờ quanh cuộc chiến sắp tới",
        "chapters": [
            {
                "kind": "chapter",
                "title": "Chương 2 — Các nước nghe thấy tiếng thu quân",
                "requires": ["neighbors-reaction"],
                "summary": "Đế quốc Baharuth, phần còn lại của Thánh quốc và những kẻ theo dõi Long vương Bạch kim phải đoán vì sao Vương quốc Pháp thuật đột ngột im mọi việc khác.",
                "scenes": [
                    {
                        "title": "Sứ quán không nhận được câu trả lời",
                        "viewpoint": "Jircniv Rune Farlord El Nix",
                        "location": "Đế quốc Baharuth",
                        "participants": ["Jircniv Rune Farlord El Nix"],
                        "tone": "cảnh giác",
                        "objective": "Cho thấy một đồng minh yếu hơn không được thông báo toàn bộ sự thật.",
                        "outcome": "Jircniv quyết định chuẩn bị mà không đứng về phía Thần quyền quốc.",
                        "events": ["Jircniv nhận thấy Vương quốc Pháp thuật đình chỉ các hoạt động đối ngoại thường lệ."],
                    }
                ],
            }
        ],
    },
    {
        "arc": "Rừng elf và người tù",
        "chapters": [
            {
                "kind": "chapter",
                "title": "Chương 3 — Ngôi trống và Ngục Băng",
                "requires": ["elf-vacuum", "antilene-captive"],
                "summary": "Cái chết của Decem để lại một vương quốc không còn vua, trong khi Antilene sống và đang bị hỏi về Hắc điển.",
                "scenes": [
                    {
                        "title": "Kho báu không phải là một vương quốc",
                        "viewpoint": "Aura Bella Fiora",
                        "location": "Vương quốc Elf",
                        "participants": ["Aura Bella Fiora", "Mare Bello Fiore"],
                        "tone": "tỉnh và hơi mệt",
                        "objective": "Xử lý khoảng trống quyền lực mà không biến người elf thành đạo cụ.",
                        "outcome": "Aura từ chối một cuộc thanh trừng không cần thiết.",
                        "events": ["Aura xác nhận Decem Hougan đã chết và vương quốc elf không còn người trị vì."],
                    },
                    {
                        "title": "Điều Antilene còn giữ",
                        "viewpoint": "Ainz Ooal Gown",
                        "location": "Ngục Băng",
                        "participants": ["Ainz Ooal Gown", "Antilene Heran Fouche"],
                        "tone": "ghê lạnh",
                        "objective": "Thẩm vấn phục vụ thông tin, không phục vụ sự tàn ác vô mục đích.",
                        "outcome": "Ainz có thêm một mảnh về Hắc điển nhưng chưa có vị trí Bảo vật thế giới.",
                        "events": ["Antilene vẫn còn sống trong Ngục Băng và chưa khai vị trí Bảo vật thế giới."],
                    },
                ],
            },
            {
                "kind": "interlude",
                "title": "Chương giữa — Công việc Albedo không ghi vào biên bản",
                "requires": ["albedo-secret"],
                "summary": "Lệnh điều động toàn bộ thủ hộ tầng suýt kéo đơn vị bí mật của Albedo ra ánh sáng. Cô che nó thêm một lần, và biết là không che được mãi.",
                "scenes": [
                    {
                        "title": "Danh sách không được trình",
                        "viewpoint": "Albedo",
                        "location": "Đại Lăng Nazarick",
                        "participants": ["Albedo"],
                        "tone": "kín và nguy hiểm",
                        "objective": "Giữ bí mật của Albedo ngoài tầm Ainz, đúng trạng thái hiểu biết đã có.",
                        "outcome": "Albedo hoãn một cuộc truy tìm Đấng Tối Cao khác, chứ không hủy nó.",
                        "events": ["Albedo giấu Ainz việc đơn vị bí mật của cô đang tìm dấu vết các Đấng Tối Cao khác."],
                    }
                ],
            },
        ],
    },
    {
        "arc": "Chiến dịch có giới hạn",
        "chapters": [
            {
                "kind": "chapter",
                "title": "Chương 4 — Mặt tiền của cuộc chiến",
                "requires": ["theocracy-war", "ainz-performance"],
                "summary": "Nazarick mở một chiến dịch thăm dò nhằm tìm Bảo vật thế giới và Hắc điển, thay vì san phẳng Thần quyền quốc trong một đêm.",
                "scenes": [
                    {
                        "title": "Kế hoạch ba bước",
                        "viewpoint": "Demiurge",
                        "location": "Đại Lăng Nazarick",
                        "participants": ["Demiurge", "Albedo", "Cocytus", "Shalltear Bloodfallen"],
                        "tone": "căng như dây cung",
                        "objective": "Chốt mục tiêu quân sự có thể thất bại một phần.",
                        "outcome": "Cocytus nhận một mặt trận giới hạn, không phải quyền được thắng bằng mọi giá.",
                        "events": ["Hội đồng chọn chiến dịch nhiều giai đoạn thay vì hủy diệt ngay lập tức."],
                    }
                ],
            },
            {
                "kind": "chapter",
                "title": "Chương 5 — Máu không phải là bản đồ",
                "requires": ["theocracy-war"],
                "summary": "Đòn thăm dò lấy được tin và trả một cái giá. Bảo vật thế giới vẫn chưa nằm trong tay Nazarick.",
                "scenes": [
                    {
                        "title": "Bản đồ thiếu một tên",
                        "viewpoint": "Cocytus",
                        "location": "Biên giới Thần quyền quốc Slane",
                        "participants": ["Cocytus", "Shalltear Bloodfallen"],
                        "tone": "gắng gượng và tỉnh",
                        "objective": "Một trận đánh hợp logic, có thương vong về phía lực lượng phụ và không có leo thang sức mạnh.",
                        "outcome": "Nazarick rút sau khi xác nhận Hắc điển đã di chuyển Bảo vật thế giới.",
                        "events": ["Lực lượng thăm dò xác nhận Bảo vật thế giới đã được chuyển khỏi vị trí cũ và rút lui."],
                    }
                ],
            },
            {
                "kind": "epilogue",
                "title": "Lời kết — Việc để dành cho một tập sau",
                "requires": ["theocracy-war", "albedo-secret"],
                "summary": "Cuộc chiến đã bắt đầu thật sự và chưa xong. Albedo vẫn giữ bí mật. Các nước láng giềng đã hiểu rằng đây không phải một cuộc cãi vã biên giới.",
                "scenes": [
                    {
                        "title": "Báo cáo không có chiến thắng trọn vẹn",
                        "viewpoint": "Ainz Ooal Gown",
                        "location": "Đại Lăng Nazarick",
                        "participants": ["Ainz Ooal Gown", "Albedo", "Demiurge"],
                        "tone": "mệt và quyết",
                        "objective": "Kết một tập truyện bằng hệ quả, không bằng một lời hứa tiêu diệt tất cả.",
                        "outcome": "Ainz chấp nhận chiến dịch dài hơi. Độc giả thấy cửa mở cho một tập tưởng tượng tiếp theo.",
                        "events": ["Ainz giữ lệnh chiến tranh nhưng chấp nhận rằng Thần quyền quốc Slane chưa bị đánh bại."],
                    }
                ],
            },
        ],
    },
]


def _id() -> str:
    return str(uuid.uuid4())


def _available_keys(session: Session) -> dict[str, Plotline]:
    rows = session.query(Plotline).filter(Plotline.timeline == "main", Plotline.current_status != "resolved").all()
    return {row.plotline_key: row for row in rows}


def build_deterministic_tree(session: Session, target_words: int) -> dict:
    available = _available_keys(session)
    if not available:
        raise ValueError("No unresolved main-timeline plotlines are available. Import authorized notes first.")
    scene_blueprints = []
    arcs = []
    previous_chapter = None
    for arc in BLUEPRINT:
        chapters = []
        for chapter in arc["chapters"]:
            if not all(key in available for key in chapter["requires"]):
                continue
            uncertainties = []
            for key in chapter["requires"]:
                uncertainties.extend(available[key].uncertainties or [])
            caused_by = previous_chapter
            chapters.append({**chapter, "uncertainties": uncertainties, "caused_by": caused_by})
            previous_chapter = chapter["title"]
            scene_blueprints.extend(chapter["scenes"])
        if chapters:
            arcs.append({"title": arc["arc"], "chapters": chapters})
    if not arcs:
        raise ValueError("Plotlines do not cover any Volume 17 chapter. Import the study notes or add the missing keys.")
    per_scene = max(700, min(2200, target_words // max(1, len(scene_blueprints))))
    alternatives = [
        "Nhánh bị loại trong bản thảo này: hủy diệt Thần quyền quốc Slane ngay trong một đêm. Nhánh đó bỏ qua rủi ro Bảo vật thế giới và làm mất phần chính trị.",
        "Chưa có cứ liệu về việc Long vương Bạch kim có can thiệp. Nếu can thiệp, đó là biến số của tập sau, không phải việc đã xảy ra.",
    ]
    for row in available.values():
        for item in row.uncertainties or []:
            if item not in alternatives:
                alternatives.append(item)
    return {
        "title": "Overlord — Tập 17 (fanfiction không chính thức)",
        "premise": (
            "Ngay sau Tập 16, Ainz đã biết Thần quyền quốc Slane đứng sau việc Shalltear bị điều khiển "
            "và đã ra lệnh chuẩn bị tiêu diệt họ. Bản thảo này không coi lệnh đó là một trận kết thúc. "
            "Nazarick phải đánh một chiến dịch có giới hạn, vì Bảo vật thế giới vẫn còn ngoài tầm tay, "
            "các nước láng giềng đang nhìn, và Albedo đang giữ một bí mật mà Ainz không biết."
        ),
        "disclaimer": DISCLAIMER,
        "alternatives": alternatives,
        "target_words": per_scene * len(scene_blueprints),
        "words_per_scene": per_scene,
        "arcs": arcs,
    }


def replace_outline(session: Session, project: Project, tree: dict) -> None:
    session.query(OutlineNode).filter(OutlineNode.project_id == project.id).delete()
    volume_id = _id()
    session.add(
        OutlineNode(
            id=volume_id,
            project_id=project.id,
            parent_id=None,
            level="volume",
            ordinal=17,
            title=tree["title"],
            summary=tree["premise"],
            payload={
                "disclaimer": tree["disclaimer"],
                "alternatives": tree["alternatives"],
                "target_words": tree["target_words"],
                "selected_branch": "staged-campaign",
            },
        )
    )
    for arc_index, arc in enumerate(tree["arcs"], start=1):
        arc_id = _id()
        session.add(
            OutlineNode(
                id=arc_id,
                project_id=project.id,
                parent_id=volume_id,
                level="arc",
                ordinal=arc_index,
                title=arc["title"],
                summary=arc["chapters"][0]["summary"],
                payload={"caused_by": arc["chapters"][0].get("caused_by")},
            )
        )
        for chapter_index, chapter in enumerate(arc["chapters"], start=1):
            chapter_id = _id()
            session.add(
                OutlineNode(
                    id=chapter_id,
                    project_id=project.id,
                    parent_id=arc_id,
                    level="chapter",
                    ordinal=chapter_index,
                    title=chapter["title"],
                    summary=chapter["summary"],
                    payload={
                        "kind": chapter["kind"],
                        "caused_by": chapter.get("caused_by"),
                        "alternatives": chapter.get("uncertainties") or [],
                        "plotlines": chapter["requires"],
                    },
                )
            )
            for scene_index, scene in enumerate(chapter["scenes"], start=1):
                scene_id = _id()
                session.add(
                    OutlineNode(
                        id=scene_id,
                        project_id=project.id,
                        parent_id=chapter_id,
                        level="scene",
                        ordinal=scene_index,
                        title=scene["title"],
                        summary=scene["objective"],
                        payload={
                            "viewpoint_character": scene["viewpoint"],
                            "location": scene["location"],
                            "participating_characters": scene["participants"],
                            "required_events": scene["events"],
                            "emotional_tone": scene["tone"],
                            "scene_objective": scene["objective"],
                            "desired_outcome": scene["outcome"],
                            "target_word_count": tree["words_per_scene"],
                            "caused_by": chapter.get("caused_by"),
                        },
                    )
                )
                for beat_index, event in enumerate(scene["events"], start=1):
                    session.add(
                        OutlineNode(
                            id=_id(),
                            project_id=project.id,
                            parent_id=scene_id,
                            level="beat",
                            ordinal=beat_index,
                            title=f"Nhịp {beat_index}",
                            summary=event,
                            payload={"required": True},
                        )
                    )
