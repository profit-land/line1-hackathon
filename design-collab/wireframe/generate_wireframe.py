"""그림책 표현 학습 와이어프레임 v3
- 파란 '→ ID' 안내 태그 제거, 모든 버튼/카드를 실제 클릭 동작으로 전환
- 화면 전환은 숨겨진 radio input + label(for=) 방식 (CSS :checked ~ 선택자) 사용.
  처음에 href="#ID" 앵커로 만들었다가, srcdoc 문서 안에서 fragment 링크를 누르면
  브라우저가 "문서 주소"를 부모 페이지 주소로 취급해 실제 사이트로 통째로 이동해버리는
  버그를 발견해서 (iframe 밖으로 튕겨나감), 네비게이션이 전혀 발생하지 않는
  radio+label 체크박스 트릭으로 교체함. Design Collab 미리보기 iframe이
  sandbox="allow-same-origin" 라서 <script> 는 애초에 동작하지 않음.
- 35개 화면을 한 번들에 모두 넣고, 페이지(= 화면)별로 해당 라디오만 기본 checked.
- 기존 프로젝트(3)의 기존 page id들을 그대로 PUT으로 갱신 (URL의 ?page=15 등이 안 깨지게)
"""
import json
import sys
import urllib.request

API = "http://localhost:5002"
PROJECT_ID = 3

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Malgun Gothic','Apple SD Gothic Neo',sans-serif;background:#e9ecef;color:#212529;font-size:14px;line-height:1.45}
.scr-radio{display:none}
.scr{display:none}
.stage{display:flex;gap:28px;justify-content:center;align-items:flex-start;flex-wrap:wrap;padding:28px 16px}
.phone{width:390px;height:780px;background:#fff;border:2px solid #343a40;border-radius:30px;overflow:hidden;display:flex;flex-direction:column;box-shadow:0 8px 24px rgba(0,0,0,.12);position:relative}
.status{height:30px;display:flex;justify-content:space-between;padding:10px 20px 0;font-size:11px;color:#868e96;flex:none}
.hdr{min-height:48px;display:flex;align-items:center;gap:8px;padding:0 14px;border-bottom:1px solid #dee2e6;font-weight:700;font-size:15px;flex:none}
.hdr .back{color:#495057;font-weight:400;font-size:18px;cursor:pointer;user-select:none}
.hdr .right{margin-left:auto;font-weight:400;font-size:12px;color:#868e96}
.content{flex:1;padding:16px;display:flex;flex-direction:column;gap:12px;overflow-y:auto;min-height:0}
.tabbar{height:60px;border-top:1px solid #dee2e6;display:flex;background:#f8f9fa;flex:none}
.tabitem{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:11px;color:#868e96;gap:3px;cursor:pointer;user-select:none}
.tabitem i{width:20px;height:20px;border:2px solid #ced4da;border-radius:6px;display:block}
.tabitem.on{color:#212529;font-weight:700}
.tabitem.on i{background:#495057;border-color:#495057}
.ph{position:relative;background:#f1f3f5;border:1px solid #adb5bd;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#868e96;font-size:12px;text-align:center;
background-image:linear-gradient(to top right,transparent calc(50% - .5px),#ced4da calc(50%),transparent calc(50% + .5px)),linear-gradient(to bottom right,transparent calc(50% - .5px),#ced4da calc(50%),transparent calc(50% + .5px))}
.ph span{background:#f1f3f5;padding:2px 8px;border-radius:6px}
.ph.dark{background-color:#495057;border-color:#343a40;color:#dee2e6}
.ph.dark span{background:#495057}
.btn{display:block;position:relative;background:#343a40;color:#fff;border-radius:10px;padding:13px;text-align:center;font-weight:700;cursor:default;border:none;font-family:inherit;font-size:14px;width:100%}
label.btn{cursor:pointer;user-select:none}
.btn.o{background:#fff;color:#343a40;border:1.5px solid #343a40}
.btn.g{background:#f1f3f5;color:#495057;border:1px solid #ced4da;font-weight:400}
.btn.s{padding:8px 12px;font-size:12px;border-radius:8px;display:inline-block;width:auto}
.btn.off{background:#ced4da;color:#868e96;cursor:default}
.row{display:flex;gap:8px;align-items:center}
.card{display:block;position:relative;border:1px solid #ced4da;border-radius:12px;padding:12px;background:#fff;width:100%;text-align:left;font-family:inherit;font-size:14px;cursor:default}
label.card{cursor:pointer;user-select:none}
label.card:hover,label.btn:hover{filter:brightness(0.97)}
.card.sel{border:2px solid #343a40;background:#f8f9fa}
.card h4{font-size:14px;margin-bottom:4px}
.muted{color:#868e96;font-size:12px}
.chip{display:inline-block;border:1px solid #ced4da;border-radius:99px;padding:3px 10px;font-size:12px;color:#495057;background:#fff}
.chip.on{background:#343a40;color:#fff;border-color:#343a40}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.h{font-weight:700;font-size:13px;color:#495057;margin-top:4px}
.big{font-size:22px;font-weight:800}
.banner{border-radius:10px;padding:10px 12px;font-size:12px;background:#f1f3f5;border:1px dashed #adb5bd;color:#495057}
.banner.warn{background:#fff5f5;border:1px solid #ffa8a8;color:#c92a2a}
.banner.ok{background:#ebfbee;border:1px solid #8ce99a;color:#2b8a3e}
.input{border:1.5px solid #adb5bd;border-radius:10px;padding:12px;color:#212529;background:#fff;min-height:44px;width:100%;font-family:inherit;font-size:14px}
.input.ta{min-height:110px;resize:vertical}
.input::placeholder{color:#868e96}
.send-row{display:flex;align-items:center;gap:8px}
.send-row .input{min-height:40px;padding:9px 14px;border-radius:999px}
.send-btn{width:40px;height:40px;border-radius:50%;background:#343a40;color:#fff;flex:none;display:flex;align-items:center;justify-content:center;font-size:16px;cursor:pointer;user-select:none}
.send-btn.off{background:#ced4da;color:#868e96;cursor:default}
.input:disabled{background:#f1f3f5;color:#868e96}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.hl{background:#ffec99;border-radius:3px;padding:0 2px;font-weight:700}
.bub{max-width:78%;padding:10px 12px;border-radius:14px;font-size:13px}
.bub.ai{background:#f1f3f5;border:1px solid #dee2e6;align-self:flex-start;border-bottom-left-radius:4px}
.bub.me{background:#343a40;color:#fff;align-self:flex-end;border-bottom-right-radius:4px}
.who{font-size:11px;color:#868e96;margin-bottom:2px}
.dots span{display:inline-block;width:7px;height:7px;border-radius:50%;background:#adb5bd;margin-right:4px}
.skel{height:12px;border-radius:6px;background:#e9ecef;margin-bottom:8px}
.steps{display:flex;gap:6px;font-size:11px;color:#868e96}
.steps b{flex:1;text-align:center;padding:6px 0;border-radius:6px;background:#f1f3f5;font-weight:400}
.steps b.on{background:#343a40;color:#fff;font-weight:700}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{border:1px solid #ced4da;padding:7px;text-align:left;vertical-align:top}
th{background:#f1f3f5}
.sp{flex:1}
.ico{width:30px;height:30px;border-radius:50%;background:#343a40;color:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;flex:none;cursor:default}
.bm-check{display:none}
.bm{font-size:18px;opacity:.3;cursor:pointer;user-select:none;line-height:1;display:inline-block}
.bm-check:checked + .bm{opacity:1}
.bm-corner{position:absolute;top:8px;right:8px}
.floatbar{position:sticky;bottom:-16px;left:0;right:0;margin:4px -16px -16px;padding:12px 16px calc(12px + env(safe-area-inset-bottom,0px));background:#fff;border-top:1px solid #dee2e6}
.floatbar .btn{padding:14px}
"""

TABS = ["홈", "단어 탐색", "복습", "내 정보"]
TAB_TARGET = {"홈": "B-1", "단어 탐색": "C-1", "복습": "G-1", "내 정보": "H-1"}

ALL_SIDS = []  # 라디오/표시 규칙 생성을 위해 수집


def _reg(sid):
    if sid not in ALL_SIDS:
        ALL_SIDS.append(sid)
    return sid


def btn(text, to=None, kind=""):
    if to:
        _reg(to)
        return f'<label class="btn {kind}" for="go-{to}">{text}</label>'
    return f'<div class="btn {kind}">{text}</div>'


def ph(label, h=140, dark=False):
    return f'<div class="ph{" dark" if dark else ""}" style="height:{h}px"><span>{label}</span></div>'


def chips(items, on=0):
    return '<div class="chips">' + "".join(
        f'<span class="chip{" on" if i == on else ""}">{t}</span>' for i, t in enumerate(items)) + "</div>"


def card(inner, to=None, sel=False):
    cls = "card" + (" sel" if sel else "")
    if to:
        _reg(to)
        return f'<label class="{cls}" for="go-{to}">{inner}</label>'
    return f'<div class="{cls}">{inner}</div>'


def banner(text, kind=""):
    return f'<div class="banner {kind}">{text}</div>'


def steps(active):
    names = ["① 단어", "② 문장", "③ 대화"]
    return '<div class="steps">' + "".join(
        f'<b class="{"on" if i == active else ""}">{n}</b>' for i, n in enumerate(names)) + "</div>"


def screen(sid, name, purpose, enter, goes, body, tab=None, title=None, back=False, back_to=None,
           status=None, right=None):
    hdr = ""
    if title is not None:
        if back and back_to:
            _reg(back_to)
            b = f'<label class="back" for="go-{back_to}">‹</label>'
        elif back:
            b = '<span class="back">‹</span>'
        else:
            b = ""
        r = f'<span class="right">{right}</span>' if right else ""
        hdr = f'<div class="hdr">{b}{title}{r}</div>'
    tabbar = ""
    if tab is not None:
        items = "".join(
            f'<label class="tabitem{" on" if t == tab else ""}" for="go-{_reg(TAB_TARGET[t])}"><i></i>{t}</label>'
            for t in TABS)
        tabbar = f'<div class="tabbar">{items}</div>'
    return f"""<section id="{sid}" class="scr"><div class="stage">
<div class="phone"><div class="status"><span>9:41</span><span>● ● ▮</span></div>{hdr}
<div class="content">{body}</div>{tabbar}</div>
</div></section>"""


# ─── 샘플 콘텐츠 ─────────────────────────────────────────────────────────────
W = "두근두근"
SENT = f'토끼는 당근을 보고 가슴이 <span class="hl">{W}</span>했어요.'
CHILD = "민준"  # A-2에서 입력한 아이 이름 예시 — 대화창에는 'AI' 대신 이 이름이 표시됨


def word_card(key, w, ko_mean, vi_mean, bookmarked=False, target="D-1"):
    chk = " checked" if bookmarked else ""
    inner = f'{ph("자체 제작 이미지", 70)}<h4 style="margin-top:8px">{w}</h4><div class="muted">{ko_mean}</div><div class="muted">{vi_mean}</div>'
    return f"""<div class="card">
<label for="go-{target}" style="display:block;cursor:pointer;user-select:none">{inner}</label>
<input type="checkbox" class="bm-check" id="bm-{key}"{chk}>
<label class="bm bm-corner" for="bm-{key}" title="복습에 저장">🔖</label>
</div>"""


def rnd(n, align="left"):
    ta = "text-align:right" if align == "right" else ""
    return f'<div class="muted" style="font-size:11px;{ta}">{n}회</div>'


def chat_base(extra=""):
    return f"""
<div class="row"><span class="chip">오늘의 표현 · {W}</span><span class="chip on">사용 1회</span></div>
<div class="bub ai"><div class="who">{CHILD} (AI 역할)</div>아빠! 토끼가 당근 봤어. 토끼 가슴이 막 뛰어!</div>
<div class="bub me">토끼가 왜 {W}할까?</div>
<div class="bub ai"><div class="who">{CHILD}</div>당근이 너무 좋아서! 나도 {W}!</div>
{extra}<div class="sp"></div>"""


def input_bar(disabled=False):
    ph_text = "답을 기다리는 중…" if disabled else "아이에게 말해 보세요"
    dis = " disabled" if disabled else ""
    btn_cls = "send-btn off" if disabled else "send-btn"
    return f"""<div class="send-row"><input type="text" class="input" placeholder="{ph_text}"{dis}><div class="{btn_cls}" title="보내기">➤</div></div>"""


SCREENS = []  # (menu, id, name, html)


def add(menu, sid, name, *a, **k):
    _reg(sid)
    SCREENS.append((menu, sid, f"{sid} {name}", screen(sid, name, *a, **k)))


M_A, M_B, M_C, M_D, M_E, M_F, M_G, M_H, M_Z = (
    "A 시작", "B 홈", "C 단어 탐색", "D 단어 학습", "E 문장 연습", "F 대화 연습", "G 복습", "H 내 정보", "Z 공통 예외")

# ── A 시작 ──────────────────────────────────────────────────────────────────
add(M_A, "A-1", "스플래시 / 서비스 소개",
    "서비스 가치를 한 문장으로 전달하고 시작을 유도", "앱 첫 실행", ["시작하기 → A-2 설명 언어 선택"],
    f"""<div class="sp"></div>{ph("로고 (서비스명 미정)", 120)}
<div class="big" style="text-align:center">(서비스명 미정)</div>
<div style="text-align:center;color:#495057">그림책 속 한국어 표현,<br>쉽게 이해하고 아이와 함께 말해 봐요</div>
<div class="sp"></div>{btn("시작하기", "A-2")}""",
    status=["그림책 일러스트 영역 제거"])

add(M_A, "A-2", "설명 언어 선택 + 아이 이름",
    "표현 설명을 받을 부모의 모국어와 아이 이름을 한 화면에서 입력. 내 정보(H-1)에서 언어만 바꾸러 올 때도 이 화면을 재사용",
    "A-1에서 시작하기 / H-1 '설명 언어'에서도 진입", ["다음 → A-4 데이터 이용 안내"],
    f"""{banner("언어를 선택하세요")}
{card('<h4>Tiếng Việt</h4><div class="muted">베트남어</div>', sel=True)}
{card('<h4>中文</h4><div class="muted">중국어</div>')}
{card('<h4>ภาษาไทย</h4><div class="muted">태국어</div>')}
<div class="h">아이 이름</div><div class="input">예: 민준</div>
<div class="sp"></div>{btn("다음", "A-4")}""",
    title="설명 언어 선택", back=True, back_to="A-1",
    status=["상단 안내 문구를 '언어를 선택하세요'로 교체", "태국어의 '시연 확장 언어' 설명 제거",
            "A-3(아이 정보) 페이지를 없애고, 아이 이름 입력란만 이 화면 하단으로 이동 — 나이·어려운 점 선택은 제거",
            "로그인·회원가입 없이 기기에 설정만 저장 (이번 와이어프레임 범위 밖)",
            "H-1 '설명 언어'에서도 이 화면으로 진입 — 와이어프레임 단순화를 위해 같은 화면 재사용 (뒤로가기는 항상 A-1로 고정)"])

add(M_A, "A-4", "데이터 이용 안내",
    "사진·저작권 관련 처리 방식을 시작 전에 투명하게 안내", "A-2에서 다음 (최초 1회)", ["확인했어요 → B-1 홈", "자세히 → H-2 데이터·저작권 안내"],
    f"""{card('<h4>사진은 글자 읽기에만 써요</h4><div class="muted">찍은 사진은 글자를 읽은 직후 바로 삭제돼요.</div>')}
{card('<h4>표현과 설명만 저장해요</h4><div class="muted">서버에는 추출한 단어와 설명만 남아요. 책 내용 전체는 저장하지 않아요.</div>')}
{card('<h4>다른 사용자와 공유하지 않아요</h4><div class="muted">내가 학습한 책 내용은 나만 볼 수 있어요.</div>')}
{card('<div class="muted" style="text-align:center">자세히 보기 ›</div>', "H-2")}
<div class="sp"></div>{btn("확인했어요", "B-1")}""",
    title="시작하기 전에", back=True, back_to="A-2")

# ── B 홈 ────────────────────────────────────────────────────────────────────
add(M_B, "B-1", "홈",
    "그림책 촬영 시작과 이어서 학습하기의 진입점", "A-4 완료 / 하단 탭 '홈'",
    ["촬영 카드 → C-1 그림책 고르기", "이어서 학습 → E-1 문장 작성", "최근 단어 → D-1 단어 카드 상세"],
    f"""{card(f'{ph("일러스트", 90)}<h4 style="margin-top:8px">그림책 사진 찍고 표현 찾기</h4><div class="muted">오늘 읽은 페이지에서 배울 표현을 골라 드려요</div>', "C-1")}
<div class="h">이어서 학습하기</div>
{card(f'<div class="row"><b class="big" style="font-size:18px">{W}</b><span class="chip">문장 연습 2/3</span></div><div class="muted">마지막 학습 · 어제</div>', "E-1")}
<div class="h">최근 학습한 단어</div>{card(f'<div class="row">{chips(["두근두근","퐁당","엉엉","반짝반짝"], -1)}</div>', "D-1")}""",
    tab="홈", title="안녕하세요, 민준 부모님")

add(M_B, "B-2", "홈 (첫 방문 · 빈 상태)",
    "학습 기록이 없을 때 첫 행동 유도", "처음 홈에 들어왔을 때", ["첫 그림책 시작하기 → C-1"],
    f"""<div class="sp"></div>{ph("빈 상태 일러스트", 140)}
<div class="big" style="text-align:center;font-size:17px">아직 학습한 단어가 없어요</div>
<div class="muted" style="text-align:center">그림책 한 페이지를 찍으면<br>배울 표현을 찾아 드려요</div>
{btn("첫 그림책 시작하기", "C-1")}<div class="sp"></div>""",
    tab="홈", title="안녕하세요, 민준 부모님", status=["기록 없음"])

# ── C 단어 탐색 ─────────────────────────────────────────────────────────────
def book_card(title, desc, letter):
    thumb = ph(letter, 56).replace('style="', 'style="width:56px;flex:none;')
    return card(f'<div class="row">{thumb}<div><h4>{title}</h4><div class="muted">{desc}</div></div></div>', "C-7")


add(M_C, "C-1", "그림책 고르기",
    "시연용 공공저작물 그림책을 골라 바로 단어 카드 목록으로 이동. 새 그림책은 하단 고정 버튼으로 촬영",
    "B-1 / 하단 탭 '단어 탐색'",
    ["그림책 선택 → C-7 단어 카드 목록", "사진 찍기(하단 고정 버튼) → C-2 촬영"],
    f"""{book_card("시연용 그림책 A", "공공저작물 · 의성어·의태어 중심", "표지")}
{book_card("시연용 그림책 B", "공공저작물 · 감정 표현 중심", "표지")}
{book_card("시연용 그림책 C", "공공저작물 · 관용 표현 중심", "표지")}
<div class="floatbar">{btn("그림책 사진 찍기", "C-2")}</div>""",
    tab="단어 탐색", title="그림책 고르기",
    status=["'찍은 사진은...' 안내 문구 제거", "'사진 찍기' 버튼을 하단 탭 바로 위 고정 플로팅 버튼으로 전환",
            "'시연용 그림책(공공저작물...)' 안내 문구 제거",
            "그림책 클릭 시 추출 과정 없이 바로 단어 카드 목록(C-7)으로 이동",
            "'아이와 대화 연습' 버튼 제거 — 단어 카드(D-1) 안에서만 진입"])

add(M_C, "C-2", "촬영",
    "한 페이지를 인식하기 좋게 촬영", "C-1 '사진 찍기'",
    ["촬영 → C-4 표현 추출 중", "카메라 권한 거부 시 → C-3"],
    f"""{ph("카메라 화면", 420, True)}
<div class="banner">한 페이지를 틀 안에 맞춰 주세요 · 밝은 곳에서 찍으면 잘 읽혀요</div>
<div class="row" style="justify-content:center"><label class="btn" style="width:64px;height:64px;border-radius:50%;padding:0;line-height:64px;text-align:center" for="go-C-4">촬영</label></div>
<div class="muted" style="text-align:center">사진은 저장되지 않고 글자 읽기 후 삭제돼요</div>""",
    title="촬영", back=True, back_to="C-1",
    status=["갤러리 업로드는 저작권 정책상 제공하지 않음(제안)", "'갤러리 없음'·'플래시' 보조 버튼 제거 — 촬영 버튼만 남김"])

add(M_C, "C-3", "카메라 권한 거부 (예외)",
    "권한이 없을 때 막히지 않게 대안 제시", "C-2에서 카메라 권한 거부", ["설정 열기 → (시스템 설정)", "시연용 그림책 보기 → C-1"],
    f"""<div class="sp"></div>{ph("카메라 꺼짐 아이콘", 110)}
<div class="big" style="text-align:center;font-size:17px">카메라 사용이 꺼져 있어요</div>
<div class="muted" style="text-align:center">그림책 페이지를 찍으려면 카메라 권한이 필요해요</div>
{btn("설정 열기")}{btn("시연용 그림책으로 보기", "C-1", "o")}<div class="sp"></div>""",
    title="촬영", back=True, back_to="C-2", status=["권한 거부"])

add(M_C, "C-4", "표현 추출 중 (로딩)",
    "글자 읽기 → 표현 고르기 → 카드 만들기 진행 상태 안내", "C-2 촬영 / C-1 시연용 그림책 선택",
    ["성공 → C-7 단어 카드 목록", "글자 인식 실패 → C-5", "표현 없음 → C-6", "취소 → C-1"],
    f"""<div class="sp"></div>{ph("스피너", 90)}
<div class="big" style="text-align:center;font-size:17px">글을 읽고 있어요</div>
<div class="sp"></div>""",
    title="표현 추출", status=["스피너와 문구만 남기고 진행 단계 표시·버튼 모두 제거",
                           "문구를 '표현을 찾고 있어요' → '글을 읽고 있어요'로 변경"])

add(M_C, "C-5", "글자 인식 실패 (예외)",
    "글자를 읽지 못했을 때 재촬영 방법 안내", "C-4에서 인식 실패", ["다시 찍기 → C-2"],
    f"""<div class="sp"></div>{ph("물음표 아이콘", 100)}
<div class="big" style="text-align:center;font-size:17px">글자를 잘 읽지 못했어요</div>
{card('<h4>이렇게 찍어 보세요</h4><div class="muted">• 밝은 곳에서 찍어요<br>• 페이지가 화면에 꽉 차게 맞춰요<br>• 그림자와 빛 반사를 피해요</div>')}
{btn("다시 찍기", "C-2")}<div class="sp"></div>""",
    title="표현 추출", back=True, back_to="C-4",
    status=["인식 실패", "'방금 찍은 사진은...' 안내 문구 제거", "'시연용 그림책 보기' 버튼 제거"])

add(M_C, "C-6", "추출 결과 없음 (예외)",
    "글자는 읽었으나 학습할 표현이 없을 때", "C-4에서 표현 0개", ["다른 페이지 찍기 → C-2"],
    f"""<div class="sp"></div>{ph("빈 카드 아이콘", 100)}
<div class="big" style="text-align:center;font-size:17px">이 페이지에서는<br>배울 표현을 못 찾았어요</div>
{btn("다른 페이지 찍기", "C-2")}<div class="sp"></div>""",
    title="표현 추출", back=True, back_to="C-4",
    status=["표현 0개", "'의성어·의태어나 감정 표현이 있는...' 안내 문구 제거"])

add(M_C, "C-7", "단어 카드 목록",
    "추출된 표현을 카드로 탐색하고 학습할 단어 선택. 카드의 🔖을 누르면 복습 목록에 저장됨", "C-4 추출 완료 / 복습·홈에서 재진입",
    ["카드 선택 → D-1 단어 카드 상세", "🔖 책갈피 → 복습(G-1)에 저장/해제", "아이와 대화 연습하기(하단 고정 버튼) → F-1"],
    f"""<div class="grid2">{word_card("dgdg", W, "가슴이 자꾸 세게 뛰는 모양", "Tim đập thình thịch")}{word_card("pd", "퐁당", "작은 물건이 물에 빠질 때 나는 소리", "Tõm")}
{word_card("ee", "엉엉", "크게 소리 내어 우는 모양", "Hu hu (khóc)")}{word_card("bjbj", "반짝반짝", "작은 빛이 계속 빛나는 모양", "Lấp lánh")}
{word_card("nhdg", "눈이 휘둥그레지다", "깜짝 놀라서 눈을 크게 뜨다", "Mắt tròn xoe")}</div>
<div class="floatbar">{btn("아이와 대화 연습하기", "F-1")}</div>""",
    tab="단어 탐색", title="이 페이지의 표현 (5)", back=True, back_to="C-4",
    status=["'사진은 삭제됐고...' 안내 문구 제거", "분류 태그(전체/의성어·의태어/감정/관용) 제거",
            "카드 이름 아래 분류 문구 대신 단어의 사전적 의미(한국어 뜻)를 표시",
            "카드마다 🔖 책갈피 아이콘 추가 — 아직 저장 전이라 기본값은 모두 비어 있음",
            "'다른 페이지 찍기' 버튼 → '아이와 대화 연습하기' 하단 고정 플로팅 버튼(→ F-1)으로 교체"])

# ── D 단어 학습 ─────────────────────────────────────────────────────────────
add(M_D, "D-1", "단어 카드 상세",
    "의미·이럴 때 써요·그림책 속 문맥을 이해하고, 비슷한 표현과 지도법까지 스크롤로 이어서 확인",
    "C-7 카드 선택 / G-1 복습 목록",
    ["문장 전체 듣기 (화면 이동 없이 인라인 재생)", "🔖 책갈피 → 복습(G-1)에 저장/해제", "문장 연습하기 (하단 고정 버튼) → E-1"],
    f"""{ph("자체 제작 이미지", 230)}
<div class="row" style="justify-content:space-between;align-items:center">
<b class="big">{W}</b>
<input type="checkbox" class="bm-check" id="bm-dgdg-d1" checked><label class="bm" for="bm-dgdg-d1" title="복습에 저장">🔖</label>
</div>
{card('<div class="h" style="margin:0">뜻</div>가슴이 자꾸 세게 뛰는 모양<br><span class="muted">Tim đập thình thịch vì hồi hộp hoặc vui</span>')}
{card(f'''<div class="h" style="margin:0">이럴 때 써요</div>기쁘거나 긴장될 때 마음이 설레는 느낌이에요.<br><span class="muted">Cảm giác hồi hộp, háo hức</span>
<div class="muted" style="margin-top:8px">• 선물을 열기 전 — 아이가 상자를 열려고 해요<br>• 놀이공원 입구에서 — 롤러코스터를 타기 전이에요<br>• 그림책 속 토끼 장면 — 토끼가 당근을 발견했어요</div>''')}
{card(f'<div class="row" style="justify-content:space-between;align-items:flex-start"><div class="h" style="margin:0">그림책 속 문장</div><span class="ico" title="문장 읽어주기">▶</span></div>{SENT}')}
<div class="h">비슷한 표현</div>
<table><tr><th>표현</th><th>느낌</th><th>이럴 때</th></tr>
<tr><td><b>{W}</b></td><td>보통 세기로 설레요</td><td>선물을 열기 전</td></tr>
<tr><td><b>콩닥콩닥</b></td><td>작고 귀엽게 뛰어요</td><td>아이·작은 동물</td></tr>
<tr><td><b>쿵쾅쿵쾅</b></td><td>크고 세게 뛰어요</td><td>크게 놀랐을 때</td></tr></table>
{card('<h4>차이 한눈에</h4><div class="muted">Tiếng Việt: 두근두근 = hồi hộp vừa phải / 콩닥콩닥 = nhẹ, đáng yêu / 쿵쾅쿵쾅 = mạnh</div>')}
<div class="h">아이에게는 이렇게</div>
{card('''<h4>① 말풍선처럼 확장해서 말해요</h4>
<div class="muted">아이가 "토끼!"라고 하면</div>
<div>"응, 토끼가 <b>두근두근</b>해 하네!"</div>
<div class="muted" style="margin-top:8px">조금 더 자라면 이렇게 확장해요</div>
<div>"토끼가 당근을 보고 가슴이 콩닥콩닥, <b>두근두근</b> 뛰네!"</div>''')}
{card('''<h4>② 몸으로 느껴봐요</h4>
<div>아이 손을 가슴에 대고 심장 뛰는 걸 함께 느끼며<br>"이게 바로 <b>두근두근</b>이야!"</div>
<div class="muted" style="margin-top:8px">또는</div>
<div>제자리에서 콩콩 뛰어 심장을 빨리 뛰게 한 뒤<br>"지금 마음이 <b>두근두근</b>하지?"</div>''')}
{card('''<h4>③ 상황이 생길 때마다 말해줘요</h4>
<div class="muted">선물 열기 전</div>
<div>"선물 열기 전엔 마음이 두근두근하지!"</div>
<div class="muted" style="margin-top:8px">소풍 가기 전날 밤</div>
<div>"내일 소풍 생각하니 두근두근하다~"</div>''')}
<div class="floatbar">{btn("문장 연습하기", "E-1")}</div>""",
    title=W, back=True, back_to="C-7",
    status=["카테고리·언어 선택 태그 제거", "'예문 듣기' 버튼 → 문장 옆 재생 아이콘으로 인라인 전환",
            "'비슷한 표현' 버튼 → 같은 화면 하단에 스크롤로 이어서 노출 (구 D-4 병합)",
            "'아이와 대화 연습하기' 버튼 제거 — 대화 연습은 C-7 하단 고정 버튼에서 진입",
            "'문장 연습하기'는 화면 하단 고정(sticky) 바 → E-1",
            "'뉘앙스' → '이럴 때 써요'로 이름 변경, 중복되는 '이럴 때 많이 써요' 문구 제거",
            "'아이용 장면 이미지' 영역 제거",
            "'아이에게는 이렇게'를 유아 어휘 지도법(비계 설정·감각 연결·상황적 반복) 3가지로 재구성",
            "자체 제작 이미지 영역 세로 길이 확대"])

add(M_D, "D-2", "예문 · 이미지 · 음성 (참고용 · 현재 미연결)",
    "과거 설계: 목표 단어가 들어간 문장 전체를 듣고 의미를 이미지로 확인하는 화면. D-1에서 인라인 재생 아이콘으로 대체되어 현재는 이 화면으로 들어오는 버튼이 없음 (데이터 보존용으로 남겨둠)",
    "(연결 없음 · 과거 D-1 '예문 듣기')",
    ["다음 → E-1 문장 작성", "뒤로 → D-1"],
    f"""{ph("예문 장면 이미지 (자체 제작)", 190)}
{card(f'<div style="font-size:17px">{SENT}</div><div class="muted" style="margin-top:6px">Con thỏ thấy cà rốt và tim đập thình thịch.</div>')}
<div class="row"><div class="btn s">▶ 문장 듣기</div><div class="btn s g">느리게</div><span class="muted">문장 전체가 재생돼요</span></div>
<div class="muted" style="text-align:center">예문 1 / 3 ‹ ›</div>
<div class="sp"></div>{btn("이 단어로 문장 써 보기", "E-1")}""",
    title="예문", back=True, back_to="D-1", status=["⚠ 현재 어떤 화면에서도 연결되지 않음 (고아 화면)"])

add(M_D, "D-3", "음성 재생 상태 (로딩 · 실패, 참고용 · 현재 미연결)",
    "음성이 늦거나 실패해도 학습이 끊기지 않게. D-2가 더 이상 연결되지 않아 함께 고아 화면이 됨",
    "(연결 없음 · 과거 D-2에서 재생 시도)", ["다시 시도 → D-2", "텍스트로 계속 → E-1"],
    f"""{ph("예문 장면 이미지", 110)}
<div class="h">상태 ① 음성 불러오는 중</div>
{card('<div class="skel" style="width:90%"></div><div class="skel" style="width:60%"></div><div class="muted">▶ 잠시만 기다려 주세요…</div>')}
<div class="h">상태 ② 재생 실패</div>
{banner("소리를 불러오지 못했어요. 네트워크를 확인해 주세요.", "warn")}
{card(f'<div style="font-size:15px">{SENT}</div>')}
{btn("다시 시도", "D-2")}{btn("글로 읽고 계속하기", "E-1", "o")}""",
    title="예문", back=True, back_to="D-2", status=["로딩", "재생 실패", "⚠ 고아 화면"])

add(M_D, "D-4", "유사 표현 비교 (참고용 · D-1에 병합됨)",
    "비슷한 표현의 강도·상황 차이 이해. 현재 이 내용은 D-1 하단에 그대로 병합되어 보여지며, 이 화면은 더 이상 별도로 연결되지 않음",
    "(연결 없음 · 과거 D-1 '비슷한 표현')", ["뒤로 → D-1"],
    f"""<table><tr><th>표현</th><th>느낌</th><th>이럴 때</th></tr>
<tr><td><b>{W}</b></td><td>보통 세기로 설레요</td><td>선물을 열기 전</td></tr>
<tr><td><b>콩닥콩닥</b></td><td>작고 귀엽게 뛰어요</td><td>아이·작은 동물</td></tr>
<tr><td><b>쿵쾅쿵쾅</b></td><td>크고 세게 뛰어요</td><td>크게 놀랐을 때</td></tr></table>
{card('<h4>차이 한눈에</h4><div class="muted">Tiếng Việt: 두근두근 = hồi hộp vừa phải / 콩닥콩닥 = nhẹ, đáng yêu / 쿵쾅쿵쾅 = mạnh</div>')}
{card('<h4>아이에게는 이렇게</h4>"마음이 콩콩 뛰어요!"')}""",
    title="비슷한 표현", back=True, back_to="D-1", status=["⚠ D-1에 내용 병합됨 · 고아 화면"])

# ── E 문장 연습 ─────────────────────────────────────────────────────────────
add(M_E, "E-1", "문장 작성",
    "배운 단어로 부모가 직접 문장 작성 (프로토타입: 입력창은 비어 있고 직접 타이핑 가능)", "D-1 / E-3 / E-4 / G-3",
    ["확인받기 → E-2 AI 검토 중"],
    f"""<div class="row"><span class="chip on">{W}</span><span class="muted">을(를) 넣어 한 문장 써 보세요</span></div>
<textarea class="input ta" placeholder="여기에 직접 문장을 입력해 보세요"></textarea>
<div class="btn s g">마이크로 입력</div>
<div class="sp"></div>{btn("완료", "E-2")}""",
    title="문장 연습", back=True, back_to="D-1",
    status=["상단 단계 표시(①②③) 제거", "힌트 기능·버튼 제거", "입력창을 실제 textarea로 전환 — 직접 타이핑 가능, 기본값 없음",
            "하단 버튼명 'AI에게 확인받기' → '완료'로 변경"])

add(M_E, "E-2", "AI 검토 중 (로딩)",
    "AI 피드백을 기다리는 동안 상태 안내", "E-1 '확인받기'",
    ["완료 → E-3(수정 필요) 또는 E-4(자연스러움)", "오류 → Z-2", "취소 → E-1"],
    f"""<div class="sp"></div>{ph("AI 생각 중 애니메이션", 80)}
<div style="text-align:center;font-weight:700">문장을 살펴보고 있어요…</div>
<div class="sp"></div>""",
    title="문장 연습", status=["스피닝 이미지와 '문장을 살펴보고 있어요' 문구만 남기고 나머지 모두 제거",
                           "로딩 (입력 잠금)"])

add(M_E, "E-3", "AI 피드백 (수정 필요)",
    "오류를 전부 고치지 않고, 의미 전달을 먼저 인정한 뒤 우선순위가 가장 높은 것 1개만 짚어주는 피드백", "E-2 결과",
    ["다시 써 보기 → E-1"],
    f"""{banner("의미는 잘 전달됐어요! 표현 하나만 다듬어볼까요?", "ok")}
<div class="card"><div class="muted">내 문장</div>저는 가슴이 <span style="text-decoration:underline wavy #e03131">두근두근을</span> 해요.</div>
<div class="card sel"><div class="muted">이렇게 말해 보세요</div><div style="font-size:16px">저는 가슴이 <span class="hl">{W}</span>해요.</div></div>
{card(f'<h4>이 부분만 살짝</h4><div>뜻은 정확해요! "{W}"을(를) 상황에 맞게 잘 골랐어요.</div><div class="muted" style="margin-top:6px">"{W}해요"라고 이어서 말하면 더 자연스러워요.</div>')}
{btn("다시 써 보기", "E-1")}""",
    title="AI 피드백", back=True, back_to="E-2",
    status=["상단 단계 표시 제거", "'쉬운 표현 보기' 버튼 제거",
            "피드백을 '의미 전달 먼저 인정 → 우선순위 1개만 짚기' 원칙으로 재구성",
            "오류 우선순위: 틀린 뜻으로 알게 되는 경우(최우선) > 문장 뜻 자체가 달라지는 경우(높음) > 상황에 안 어울리는 단어를 쓴 경우(높음) > 자연스럽게 이어지지 않는 표현(중간) > 뜻 전달엔 문제없는 사소한 차이(낮음)",
            "이번 예시는 '자연스럽게 이어지지 않는 표현'(중간 우선순위) 1개만 다룸",
            "조사 등 문법 용어는 쓰지 않고 자연스러운 말로만 안내"])

add(M_E, "E-4", "AI 피드백 (자연스러운 문장)",
    "잘 쓴 경우 칭찬과 더 풍부한 표현 제안", "E-2 결과", ["단어 보기 → D-1", "다시 써 보기 → E-1"],
    f"""{banner("아주 자연스러워요! 잘했어요", "ok")}
<div class="card sel"><div class="muted">내 문장</div><div style="font-size:16px">저는 선물을 열 때 마음이 <span class="hl">{W}</span>해요.</div></div>
{card('<h4>이런 표현도 써 보세요</h4><div>• 마음이 <b>콩닥콩닥</b>해요 (작게 설렐 때)<br>• 가슴이 <b>쿵쾅쿵쾅</b>해요 (크게 놀랐을 때)</div>')}
<div class="sp"></div><div class="row"><div style="flex:1">{btn("단어 보기", "D-1", "o")}</div><div style="flex:1">{btn("다시 써 보기", "E-1")}</div></div>""",
    title="AI 피드백", back=True, back_to="E-2", status=["상단 단계 표시 제거", "문장이 자연스러운 케이스",
                                                       "'아이에게 쉽게 말하는 법' 버튼 제거 → '단어 보기'·'다시 써 보기' 두 버튼으로 교체"])

# ── F 대화 연습 ─────────────────────────────────────────────────────────────
add(M_F, "F-1", "대화 연습 준비",
    "오늘의 목표만 확인하고 바로 대화 시작 (2단계 삭제 — 1단계 단일 흐름)",
    "C-7 단어 카드 목록 '아이와 대화 연습하기' 하단 고정 버튼에서 진입",
    ["대화 시작 → F-2", "뒤로 → C-7 단어 카드 목록"],
    f"""<div class="h">오늘의 목표</div>
{card(f'<span class="chip on">{W}</span> 을(를) 넣어 아이에게 질문해 보기')}
<div class="sp"></div>{btn("대화 시작하기", "F-2")}""",
    title="아이와 대화 연습", back=True, back_to="C-7")

add(M_F, "F-2", "대화 화면 (대화 중)",
    f"1단계 대화(AI 4회+부모 4회=8발화) 진행 중, 2세트째에 부모가 답할 수 있도록 도움말을 보여주는 장면. "
    "진행 방식 — ①아이가 책 속 장면을 보고 자기 생각을 말하면 부모는 그 생각을 받아주며 학습 단어를 넣어 말한다 "
    "②아이가 단어 뜻을 물으면 부모는 책 장면과 연결해 쉬운 말로 설명한다 "
    "③아이가 자신의 익숙한 경험을 말하면 부모는 그 경험을 인정하고 학습 단어를 넣어 다시 말한다 "
    "④아이가 다른 일상 상황을 말하면 부모는 학습 단어를 적용해 책 속 장면과 다시 연결한다",
    "F-1 '대화 시작하기' / F-5에서 '다시 답변하기'",
    ["답변 보내기 → F-4 (로딩)", "뒤로 → F-1"],
    f"""<div class="row"><span class="chip">오늘의 표현 · {W}</span><span class="chip on">2세트 · 도움말</span></div>
<div class="bub ai"><div class="who">{CHILD} (아이)</div>토끼가 당근을 보고 가슴이 콩닥콩닥할 것 같아!</div>
<div class="bub me">맞아, 토끼 마음이 {W}했을 것 같아!</div>
<div class="bub ai"><div class="who">{CHILD} (아이)</div>근데 {W}이 뭐야?</div>
{card('<div class="h" style="margin:0">💡 도움말</div><div class="muted" style="margin-top:4px">책 장면과 연결해 쉬운 말로 뜻을 설명해보세요.</div>')}
<div class="sp"></div>
<div class="send-row"><input type="text" class="input" placeholder="여기에 답해 보세요"><label class="send-btn" for="go-F-4" title="보내기">➤</label></div>""",
    title=f"{CHILD}과 대화", back=True, back_to="F-1")

add(M_F, "F-3", "1단계 대화 (완료)",
    f"AI 4회, 부모 4회로 총 8번의 대화를 주고받은 완료 상태. 각 발화는 F-2(대화 화면·대화 중)의 진행 방식을 그대로 따른다",
    "F-4 로딩 완료 후 (문제 없이 4세트까지 끝났을 때) / F-5에서 '대화 계속 보기'",
    ["대화 마무리 보기 → F-6", "뒤로 → F-2"],
    f"""<div class="row"><span class="chip">오늘의 표현 · {W}</span><span class="chip on">1단계 · 완료</span></div>
<div class="bub ai"><div class="who">{CHILD} (아이)</div>토끼가 당근을 보고 가슴이 콩닥콩닥할 것 같아!</div>
<div class="bub me">맞아, 토끼 마음이 {W}했을 것 같아!</div>
<div class="bub ai"><div class="who">{CHILD} (아이)</div>근데 {W}이 뭐야?</div>
<div class="bub me">좋아하는 걸 보면 마음이 자꾸 뛰는 거야. 토끼도 당근을 보고 그랬을 거야.</div>
<div class="bub ai"><div class="who">{CHILD} (아이)</div>나도 생일 선물 받을 때 그랬어!</div>
<div class="bub me">맞아! 그때 민준이 마음도 {W}했겠다.</div>
<div class="bub ai"><div class="who">{CHILD} (아이)</div>내일 소풍 가는 것도 {W}해!</div>
<div class="bub me">토끼가 당근 보고 {W}한 것처럼, 민준이도 소풍 생각하면 {W}하지?</div>
{banner("1단계 대화를 모두 마쳤어요 (8개 발화 완료)", "ok")}
<div class="floatbar">{btn("대화 마무리 보기 →", "F-6")}</div>""",
    title=f"{CHILD}과 대화", back=True, back_to="F-2")

add(M_F, "F-4", "AI 응답 대기 (로딩)",
    f"{CHILD} 역할의 AI가 부모의 답변을 받아 다음 발화를 준비하는 동안의 로딩 상태",
    "F-2 '답변 보내기'", ["문제 없이 진행 → F-3 (완료)", "답변에 문제 있음 → F-5 (피드백)", "뒤로 → F-2"],
    chat_base('<div class="bub ai"><div class="dots"><span></span><span></span><span></span></div></div>') + input_bar(True),
    title=f"{CHILD}과 대화", right="입력 잠금", back=True, back_to="F-2")

add(M_F, "F-5", "대화 중 피드백",
    "부모가 2번째 응답(2세트 답변)을 보낸 뒤, 그 답변에 문제가 있을 경우 대화창 안에서 바로 보여주는 피드백. "
    "E-3과 같은 원칙 — 의미 전달을 먼저 인정하고 문법 용어 없이 1개만 자연스럽게 짚는다",
    "F-4 '문제 있음' (2세트 답변 전송 직후)", ["다시 답변하기 → F-2", "대화 계속 보기 → F-3"],
    f"""<div class="row"><span class="chip">오늘의 표현 · {W}</span><span class="chip on">2세트 · 피드백</span></div>
<div class="bub ai"><div class="who">{CHILD} (아이)</div>토끼가 당근을 보고 가슴이 콩닥콩닥할 것 같아!</div>
<div class="bub me">맞아, 토끼 마음이 {W}했을 것 같아!</div>
<div class="bub ai"><div class="who">{CHILD} (아이)</div>근데 {W}이 뭐야?</div>
<div class="bub me">좋아하는 거 보면 마음이 {W}을 해.</div>
{banner("의미는 잘 전달됐어요! 표현 하나만 다듬어볼까요?", "ok")}
{card(f'<h4>이 부분만 살짝</h4><div>뜻은 정확해요! 상황에 맞는 표현을 잘 골랐어요.</div><div class="muted" style="margin-top:6px">"{W}해"라고 이어서 말하면 더 자연스러워요.</div>')}
<div class="sp"></div>
<div class="send-row"><input type="text" class="input" placeholder="다시 답해 보세요"><label class="send-btn" for="go-F-4" title="보내기">➤</label></div>""",
    title=f"{CHILD}과 대화", back=True, back_to="F-2")

add(M_F, "F-6", "대화 마무리",
    "1단계 대화를 마쳤다는 완료 상태만 짧게 보여주고 홈으로 복귀", "F-3 '대화 마무리 보기'", ["홈으로 → B-1"],
    f"""<div class="sp"></div>{ph("완료 일러스트", 90)}<div class="big" style="text-align:center;font-size:17px">오늘 대화 잘했어요!</div>
<div class="sp"></div>{btn("홈으로", "B-1")}<div class="sp"></div>""",
    title="대화 마무리")

# ── G 복습 ──────────────────────────────────────────────────────────────────
add(M_G, "G-1", "학습 단어 목록",
    "단어 카드에서 🔖 책갈피한 단어만, C-7과 같은 2열 카드(사진·사전적 의미·외국어 뜻)로 모아서 다시 찾아보고 재연습. 기본은 최신 책갈피 순",
    "하단 탭 '복습' / F-6",
    ["단어 선택 → G-3 단어별 기록"],
    f"""<div class="muted">🔖 책갈피한 단어 (최신순)</div>
<div class="grid2">{word_card("dgdg-g1", W, "가슴이 자꾸 세게 뛰는 모양", "Tim đập thình thịch", True, "G-3")}{word_card("pd-g1", "퐁당", "작은 물건이 물에 빠질 때 나는 소리", "Tõm", True, "G-3")}
{word_card("ee-g1", "엉엉", "크게 소리 내어 우는 모양", "Hu hu (khóc)", True, "G-3")}{word_card("bjbj-g1", "반짝반짝", "작은 빛이 계속 빛나는 모양", "Lấp lánh", True, "G-3")}</div>""",
    tab="복습", title="복습",
    status=["정렬 방식 태그 제거 — 책갈피한 순서(최신순) 그대로 나열", "책갈피(🔖)하지 않은 단어는 목록에 나타나지 않음",
            "목록을 C-7과 같은 2열 카드(사진·사전적 의미·외국어 뜻)로 전환", "오른쪽 태그('문장 2 · 대화 1' 등) 제거"])

add(M_G, "G-2", "복습 (빈 상태)",
    "책갈피한 단어가 없을 때 안내", "책갈피한 단어가 없는 상태에서 '복습' 탭", [],
    f"""<div class="sp"></div>{ph("빈 상태 일러스트", 120)}
<div class="big" style="text-align:center;font-size:17px">책갈피한 단어가 아직 없어요</div>
<div class="muted" style="text-align:center">단어 카드에서 🔖를 누르면<br>여기에 모여요</div>
<div class="sp"></div>""",
    tab="복습", title="복습", status=["책갈피 0개", "'그림책 시작하기' 버튼 제거"])

add(M_G, "G-3", "단어별 기록",
    "내가 쓴 문장과 받은 피드백을 최근 순으로 나열해 확인하고 재연습", "G-1 단어 선택", ["다시 연습 → E-1", "카드 보기 → D-1"],
    f"""<div class="row"><b class="big">{W}</b></div>
<div class="h">내가 쓴 문장과 피드백</div>
{card(f'<div>저는 선물을 열 때 마음이 <span class="hl">{W}</span>해요.</div><div class="muted" style="margin-top:6px">피드백: 아주 자연스러워요! 잘했어요.</div>')}
{card('<div><s style="color:#868e96">저는 가슴이 두근두근을 해요.</s></div><div class="muted" style="margin-top:6px">피드백: 저는 가슴이 두근두근해요. (이렇게 이어서 말하면 더 자연스러워요)</div>')}
<div class="sp"></div><div class="row"><div style="flex:1">{btn("문장 다시 연습", "E-1")}</div><div style="flex:1">{btn("단어 카드 보기", "D-1", "o")}</div></div>""",
    tab="복습", title=W, back=True, back_to="G-1",
    status=["'1차'·'2차' 문구 제거", "최근에 한 연습일수록 위쪽에 쌓이도록 순서 변경", "'대화 연습' 영역 제거"])

# ── H 내 정보 ───────────────────────────────────────────────────────────────
add(M_H, "H-1", "내 정보",
    "설명 언어 변경, 데이터 안내 확인", "하단 탭 '내 정보'", ["설명 언어 → A-2 (언어 변경 화면)", "데이터·저작권 안내 → H-2"],
    f"""{card('<h4>설명 언어</h4><div class="muted">Tiếng Việt</div>', "A-2")}
{card('<h4>데이터 및 저작권 안내</h4><div class="muted">사진·저장 정보 처리 방식</div>', "H-2")}""",
    tab="내 정보", title="내 정보",
    status=["'아이 정보' 카드 제거", "'학습 기록 삭제' 카드 제거",
            "'설명 언어' 카드는 현재 선택된 언어만 노출, 누르면 언어 변경 화면(A-2)으로 이동"])

add(M_H, "H-2", "데이터 · 저작권 안내",
    "촬영 사진·저장 정보·공유 여부를 표로 투명하게 공개", "H-1 / A-4 '자세히'", ["뒤로 → H-1"],
    f"""<table><tr><th>항목</th><th>처리 방식</th></tr>
<tr><td>찍은 사진</td><td>글자 읽기에만 사용, 직후 삭제</td></tr>
<tr><td>서버 저장</td><td>추출한 단어·설명만 저장</td></tr>
<tr><td>책 내용</td><td>다른 사용자와 공유하지 않음</td></tr>
<tr><td>시연용 책</td><td>자유 이용 가능한 공공저작물만 사용</td></tr></table>
{banner("저작권 관련 세부 사항은 법률 검토 후 확정 예정")}""",
    tab="내 정보", title="데이터 · 저작권 안내", back=True, back_to="H-1",
    status=["'내 학습 기록 삭제' 버튼 제거"])

# ── Z 공통 예외 ─────────────────────────────────────────────────────────────
add(M_Z, "Z-1", "네트워크 오류",
    "연결이 끊겼을 때 공통 안내", "모든 화면에서 연결 실패", ["다시 시도 → 직전 화면", "홈으로 → B-1"],
    f"""<div class="sp"></div>{ph("오프라인 아이콘", 100)}
<div class="big" style="text-align:center;font-size:17px">인터넷에 연결되지 않았어요</div>
<div class="muted" style="text-align:center">연결을 확인하고 다시 시도해 주세요</div>
{btn("홈으로", "B-1", "o")}<div class="sp"></div>""",
    title="오류", status=["오프라인"])

add(M_Z, "Z-2", "AI 응답 지연 · 오류",
    "AI 응답이 늦거나 실패했을 때 공통 안내", "E-2 / F-3 등 AI 호출 화면", ["다시 시도 → 직전 화면", "나중에 하기 → B-1"],
    f"""<div class="sp"></div>{ph("느린 AI 아이콘", 100)}
<div class="big" style="text-align:center;font-size:17px">AI가 대답하는 데<br>시간이 걸려요</div>
<div class="muted" style="text-align:center">잠시 후 다시 시도해 주세요. 입력한 내용은 그대로 있어요.</div>
{btn("나중에 하기", "B-1", "o")}<div class="sp"></div>""",
    title="오류", status=["타임아웃", "서버 오류"])


# ─── 번들 조립 ───────────────────────────────────────────────────────────────
ALL_SECTIONS = "".join(html for _, _, _, html in SCREENS)
SHOW_RULES = "".join(f"#go-{sid}:checked ~ #{sid}{{display:block}}" for sid in ALL_SIDS)
HEAD = f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>와이어프레임 프로토타입</title><style>{CSS}{SHOW_RULES}</style></head>"""


def bundle_for(default_sid):
    radios = "".join(
        f'<input type="radio" name="scr" id="go-{sid}" class="scr-radio"{" checked" if sid == default_sid else ""}>'
        for sid in ALL_SIDS)
    return HEAD + f"<body>{radios}{ALL_SECTIONS}</body></html>"


# ─── 등록 (기존 page id 그대로 갱신) ─────────────────────────────────────────
def call(method, path, data=None):
    req = urllib.request.Request(
        API + path, method=method, headers={"Content-Type": "application/json"},
        data=json.dumps(data).encode("utf-8") if data is not None else None)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode("utf-8"))


if __name__ == "__main__":
    if "--dry" in sys.argv:
        unknown = [sid for sid in ALL_SIDS if sid not in {s for _, s, _, _ in SCREENS}]
        print("참조되지만 화면이 없는 id:", unknown)
        print("bundle size per page ~", len(bundle_for("D-1")))
        sys.exit()

    # 사람이 일부러 지운 페이지는 되살리지도, 보고하지도 않는다 — 존재하는 페이지만 갱신.
    pages = call("GET", f"/api/projects/{PROJECT_ID}/pages")
    id_by_sid = {}
    for p in pages:
        sid = p["name"].split()[0]
        id_by_sid[sid] = p["id"]

    updated = 0
    for _, sid, _, _ in SCREENS:
        pid = id_by_sid.get(sid)
        if not pid:
            continue
        html = bundle_for(sid)
        call("PUT", f"/api/pages/{pid}", {"html_content": html})
        updated += 1
    print("updated", updated, "pages, bundle size", len(ALL_SECTIONS), "bytes shared content")
