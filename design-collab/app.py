"""Design Collab - 화면 시안 협업 도구 (Supabase 공용 DB 버전)"""
import os
import re

from flask import Flask, Response, jsonify, request, session
from dotenv import load_dotenv
from supabase import create_client

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ─── Supabase 클라이언트 (.env.local 에서 URL / Publishable key 로딩) ────────
# Secret key 는 서버 코드에도 브라우저 코드에도 넣지 않는다.
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = (os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
                or os.environ.get("SUPABASE_ANON_KEY", ""))

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or "design-collab-local-dev-key"


def _no_cache(resp):
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp


def _sb():
    """Supabase 클라이언트 (publishable key 만 사용). 매 호출마다 만들어도 가벼움."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY 가 .env.local 에 없습니다.")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ─── 헬퍼 ────────────────────────────────────────────────────────────────────

def _ts(s):
    """ISO8601 → 'YYYY-MM-DD HH:MM:SS' (SQLite localtime 과 같은 표기)."""
    if not s:
        return ""
    return s.replace("T", " ").split(".")[0].replace("+00:00", "").rstrip()


def _fmt(row, ts_fields=("created_at", "updated_at")):
    """행(dict)에서 지시자열 필드를 datetime 문자열로 바꿔 반환."""
    if row is None:
        return None
    out = dict(row)
    for f in ts_fields:
        if f in out and isinstance(out[f], str):
            out[f] = _ts(out[f])
    return out


def _find(table, **conds):
    q = _sb().table(table).select("*").limit(1)
    for k, v in conds.items():
        q = q.eq(k, v)
    data = q.execute().data
    return data[0] if data else None


def _row(table, rid):
    return _find(table, id=rid)


def _insert(table, values):
    data = _sb().table(table).insert(values).select().execute().data
    return data[0] if data else None


def _update(table, rid, values):
    data = _sb().table(table).update(values).eq("id", rid).select().execute().data
    return data[0] if data else None


def _delete(table, rid):
    _sb().table(table).delete().eq("id", rid).execute()


def _rows(table, order_col=None, desc=False, **conds):
    q = _sb().table(table).select("*")
    for k, v in conds.items():
        q = q.eq(k, v)
    if order_col:
        q = q.order(order_col, desc=desc)
    return q.execute().data


def _user():
    return session.get("user")


EMAIL_RE = re.compile(r"^[\w.\-+]+@[\w\-]+(\.[\w\-]+)+$")


def _notify(user_email, notif_type, ref_id, message):
    if not user_email:
        return
    try:
        _insert("notifications", {
            "user_email": user_email,
            "type": notif_type,
            "ref_id": ref_id,
            "message": message,
        })
    except Exception:
        pass


# ─── 페이지 ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    with open(os.path.join(BASE_DIR, "templates", "index.html"), encoding="utf-8") as f:
        return _no_cache(Response(f.read(), mimetype="text/html"))


@app.route("/probed")
def probed():
    return "ok"


# ─── 사용자 (가입/로그인/팀원 목록) ──────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    if not name:
        return jsonify({"error": "이름을 입력해 주세요."}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "올바른 이메일 형식이 아닙니다."}), 400
    if _find("users", email=email):
        return jsonify({"error": "이미 가입된 이메일입니다."}), 409
    user = _insert("users", {"name": name, "email": email})
    # 처음 가입한 사람은 관리자로 만든다 (초대 모델 대신 self-host 기준).
    count = len(_rows("users"))
    if count == 1:
        user = _update("users", user["id"], {"is_admin": True})
    session["user"] = _fmt(user)
    return jsonify(dict(_fmt(user))), 201


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "이메일을 입력해 주세요."}), 400
    user = _find("users", email=email)
    if not user:
        return jsonify({"error": "가입되지 않은 이메일입니다."}), 404
    session["user"] = _fmt(user)
    return jsonify(dict(_fmt(user)))


@app.route("/api/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return jsonify({"ok": True})


@app.route("/api/me")
def me():
    u = _user()
    if not u:
        return jsonify(None)
    return jsonify(u)


@app.route("/api/users", methods=["GET"])
def list_users():
    return jsonify([dict(_fmt(r)) for r in _rows("users", "id")])


@app.route("/api/users/<int:uid>", methods=["DELETE"])
def delete_user(uid):
    data = request.get_json(force=True) if request.is_json else {}
    requester = _user()
    if not requester:
        return jsonify({"error": "로그인이 필요합니다."}), 401
    if not requester.get("is_admin"):
        return jsonify({"error": "관리자만 팀원을 삭제할 수 있습니다."}), 403
    if requester.get("email") and requester["email"].lower() == data.get("email", "").lower():
        return jsonify({"error": "본인은 삭제할 수 없습니다."}), 400
    target = _row("users", uid)
    if not target:
        return jsonify({"error": "팀원을 찾을 수 없습니다."}), 404
    _delete("users", uid)
    return jsonify({"ok": True, "deleted": dict(_fmt(target))})



# ─── 프로젝트 ────────────────────────────────────────────────────────────────

@app.route("/api/projects", methods=["GET"])
def list_projects():
    return jsonify([dict(_fmt(r)) for r in _rows("projects", "id")])


@app.route("/api/projects", methods=["POST"])
def create_project():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "프로젝트 이름이 필요합니다."}), 400
    proj = _insert("projects", {"name": name})
    return jsonify(dict(_fmt(proj))), 201


@app.route("/api/projects/<int:pid>", methods=["PUT"])
def rename_project(pid):
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "이름이 비어있습니다."}), 400
    proj = _update("projects", pid, {"name": name})
    if not proj:
        return jsonify({"error": "프로젝트를 찾을 수 없습니다."}), 404
    return jsonify({"ok": True})


@app.route("/api/projects/<int:pid>", methods=["DELETE"])
def delete_project(pid):
    _delete("projects", pid)  # FK ON DELETE CASCADE → pages 등 자동 삭제
    return jsonify({"ok": True})


# ─── 페이지 ──────────────────────────────────────────────────────────────────

@app.route("/api/projects/<int:pid>/pages", methods=["GET"])
def list_pages(pid):
    return jsonify([dict(_fmt(r)) for r in _rows("pages", project_id=pid, order_col="sort_order")])


@app.route("/api/projects/<int:pid>/pages", methods=["POST"])
def create_page(pid):
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "페이지 이름이 필요합니다."}), 400
    rows = _rows("pages", project_id=pid)
    next_order = max((r["sort_order"] for r in rows), default=0) + 1
    pg = _insert("pages", {
        "project_id": pid,
        "name": name,
        "html_content": data.get("html_content", ""),
        "sort_order": next_order,
        "menu_name": data.get("menu_name"),
    })
    return jsonify(dict(_fmt(pg))), 201


@app.route("/api/pages/<int:page_id>", methods=["PUT"])
def update_page(page_id):
    data = request.get_json(force=True)
    fields = {}
    if "name" in data and (data.get("name") or "").strip():
        fields["name"] = data["name"].strip()
    if "html_content" in data:
        fields["html_content"] = data["html_content"]
    if "menu_name" in data:
        fields["menu_name"] = data.get("menu_name")
    if "sort_order" in data:
        fields["sort_order"] = data.get("sort_order")
    if not fields:
        return jsonify({"error": "수정할 항목이 없습니다."}), 400
    pg = _update("pages", page_id, fields)
    if not pg:
        return jsonify({"error": "페이지를 찾을 수 없습니다."}), 404
    return jsonify(dict(_fmt(pg)))


@app.route("/api/pages/<int:page_id>", methods=["DELETE"])
def delete_page(page_id):
    _delete("pages", page_id)  # cascade → descriptions/comments/tags/memos
    return jsonify({"ok": True})


@app.route("/api/pages/<int:page_id>/move", methods=["PUT"])
def move_page(page_id):
    """다른 프로젝트/메뉴로 이동하거나 순서 변경."""
    data = request.get_json(force=True)
    pg = _row("pages", page_id)
    if not pg:
        return jsonify({"error": "페이지를 찾을 수 없습니다."}), 404
    fields = {}
    if "project_id" in data and data["project_id"] != pg["project_id"]:
        fields["project_id"] = data["project_id"]
    if "menu_name" in data:
        fields["menu_name"] = data.get("menu_name")
    if "sort_order" in data and data["sort_order"] != pg["sort_order"]:
        fields["sort_order"] = data["sort_order"]
    if fields:
        pg = _update("pages", page_id, fields)
    return jsonify(dict(_fmt(pg)))


# ─── 메뉴 ────────────────────────────────────────────────────────────────────

@app.route("/api/projects/<int:pid>/menus", methods=["GET"])
def list_menus(pid):
    """프로젝트의 메뉴 목록 + 각 메뉴에 속한 페이지 수."""
    menus = _rows("menus", project_id=pid, order_col="sort_order")
    pages = _rows("pages", project_id=pid)
    count = {}
    for p in pages:
        if p["menu_name"]:
            count[p["menu_name"]] = count.get(p["menu_name"], 0) + 1
    out = []
    for m in menus:
        d = dict(_fmt(m))
        d["page_count"] = count.get(m["name"], 0)
        out.append(d)
    return jsonify(out)


@app.route("/api/projects/<int:pid>/menus", methods=["POST"])
def add_menu(pid):
    """새 메뉴 추가. 같은 이름의 menu_name을 가진 기존 페이지는 자동 연결됨."""
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "메뉴 이름이 필요합니다."}), 400
    if _find("menus", project_id=pid, name=name):
        return jsonify({"error": f"'{name}' 메뉴가 이미 존재합니다."}), 409
    rows = _rows("menus", project_id=pid)
    max_order = max((r["sort_order"] for r in rows), default=-1) + 1
    menu = _insert("menus", {"project_id": pid, "name": name, "sort_order": max_order})
    return jsonify(dict(_fmt(menu))), 201


@app.route("/api/menus/<int:menu_id>", methods=["PUT"])
def rename_menu(menu_id):
    """메뉴 이름 변경 → 해당 메뉴의 모든 페이지 menu_name도 함께 갱신."""
    data = request.get_json(force=True)
    new_name = (data.get("name") or "").strip()
    if not new_name:
        return jsonify({"error": "메뉴 이름이 비어있습니다."}), 400
    menu = _row("menus", menu_id)
    if not menu:
        return jsonify({"error": "메뉴를 찾을 수 없습니다."}), 404
    dup = _find("menus", project_id=menu["project_id"], name=new_name)
    if dup and dup["id"] != menu_id:
        return jsonify({"error": f"'{new_name}' 메뉴가 이미 존재합니다."}), 409
    old_name = menu["name"]
    _update("menus", menu_id, {"name": new_name})
    # 해당 메뉴의 페이지들 menu_name 동기화
    for p in _rows("pages", project_id=menu["project_id"], menu_name=old_name):
        _update("pages", p["id"], {"menu_name": new_name})
    updated = _row("menus", menu_id)
    return jsonify(dict(_fmt(updated)))


@app.route("/api/menus/<int:menu_id>", methods=["DELETE"])
def delete_menu(menu_id):
    """메뉴 삭제 → 해당 페이지들은 menu_name=NULL(미분류)로 이동."""
    menu = _row("menus", menu_id)
    if not menu:
        return jsonify({"error": "메뉴를 찾을 수 없습니다."}), 404
    for p in _rows("pages", project_id=menu["project_id"], menu_name=menu["name"]):
        _update("pages", p["id"], {"menu_name": None})
    _delete("menus", menu_id)
    return jsonify({"ok": True})


# ─── Descriptions ────────────────────────────────────────────────────────────

@app.route("/api/pages/<int:page_id>/description", methods=["GET"])
def get_description(page_id):
    row = _find("descriptions", page_id=page_id)
    if row:
        return jsonify(dict(_fmt(row)))
    return jsonify({"page_id": page_id, "content": "", "author_name": "", "updated_at": ""})


@app.route("/api/pages/<int:page_id>/description", methods=["PUT"])
def save_description(page_id):
    data = request.get_json(force=True)
    content = data.get("content", "")
    author = (data.get("author_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    existing = _find("descriptions", page_id=page_id)
    # 기존 디스크립션이 있고, 다른 사람이 쓴 것이라면 수정 불가
    if existing and existing["author_email"] and not email:
        return jsonify({"error": "로그인이 필요합니다."}), 401
    if existing and existing["author_email"] and existing["author_email"] != email:
        return jsonify({"error": "본인 작성분이 아닙니다. 수정할 수 없습니다."}), 403
    values = {"page_id": page_id, "content": content,
              "author_name": author, "author_email": email}
    if existing:
        row = _update("descriptions", existing["id"], values)
    else:
        row = _insert("descriptions", values)
    return jsonify(dict(_fmt(row)))


# ─── Comments ────────────────────────────────────────────────────────────────

def _comment_number(page_id, cid):
    """표시 순서대로 1부터 번호를 붙인다 (created_at, id 기준)."""
    rows = _rows("comments", page_id=page_id, order_col="created_at")
    for i, r in enumerate(rows, 1):
        if r["id"] == cid:
            return i
    return None


def _comment_out(r):
    """코멘트 행 → 응답 dict. id는 'c'+숫자 문자열 규칙으로 반환."""
    d = dict(_fmt(r))
    d["id"] = "c" + str(r["id"])
    if d.get("mention_email"):
        urow = _find("users", email=d["mention_email"])
        d["mention_name"] = urow["name"] if urow else ""
    else:
        d["mention_name"] = ""
    return d


@app.route("/api/pages/<int:page_id>/comments", methods=["GET"])
def list_comments(page_id):
    include_hidden = request.args.get("include_hidden") == "1"
    rows = _rows("comments", page_id=page_id, order_col="created_at")
    out = []
    for i, r in enumerate(rows, 1):
        if r["parent_tag_id"] is not None:
            continue  # 태그에 달린 댓글은 화면 코멘트 탭에 포함하지 않는다
        if r["hidden"] and not include_hidden:
            continue
        d = _comment_out(r)
        d["comment_number"] = i
        out.append(d)
    return jsonify(out)


@app.route("/api/comments/<int:cid>")
def get_comment(cid):
    """알림 클릭 시 해당 코멘트의 page_id / parent_tag_id 역참조용."""
    row = _row("comments", cid)
    if not row:
        return jsonify({"error": "코멘트를 찾을 수 없습니다."}), 404
    return jsonify({"id": row["id"], "page_id": row["page_id"],
                    "parent_tag_id": row["parent_tag_id"], "content": row["content"] or ""})


@app.route("/api/pages/<int:page_id>/comments", methods=["POST"])
def add_comment(page_id):
    data = request.get_json(force=True)
    author = (data.get("author_name") or "").strip()
    content = (data.get("content") or "").strip()
    email = (data.get("email") or "").strip().lower()
    mention_email = (data.get("mention_email") or "").strip().lower()
    x_pct = data.get("x_pct")
    y_pct = data.get("y_pct")
    x_pct = float(x_pct) if x_pct is not None else None
    y_pct = float(y_pct) if y_pct is not None else None
    if not author or not content:
        return jsonify({"error": "이름과 내용을 모두 입력해 주세요."}), 400
    # 대상(@지정) 필수: 가입된 팀원 이메일이어야 한다.
    if not mention_email:
        return jsonify({"error": "코멘트 대상을 지정해 주세요. (@로 한 명을 선택하세요)"}), 400
    user_row = _find("users", email=mention_email)
    if not user_row:
        return jsonify({"error": "대상이 이 워크스페이스에 가입되지 않은 사용자입니다."}), 400
    row = _insert("comments", {
        "page_id": page_id, "author_name": author, "content": content,
        "author_email": email, "mention_email": mention_email,
        "x_pct": x_pct, "y_pct": y_pct,
    })
    # 멘션 알림: @대상에게 알림 생성 (본인 제외)
    if mention_email and mention_email != email:
        _notify(mention_email, "mention", row["id"], f"{author}님이 코멘트에서 당신을 멘션했습니다")
    d = _comment_out(row)
    d["comment_number"] = _comment_number(page_id, row["id"])
    return jsonify(d), 201


@app.route("/api/comments/<int:cid>/toggle-hidden", methods=["POST"])
def toggle_comment_hidden(cid):
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    comment = _row("comments", cid)
    if not comment:
        return jsonify({"error": "코멘트를 찾을 수 없습니다."}), 404
    # 작성자와 @대상(mention_email) 단 두 명만 숨김 체크 가능
    if comment["mention_email"]:
        allowed = {comment["author_email"], comment["mention_email"]} - {""}
        if email not in allowed:
            return jsonify({"error": "작성자와 지정된 대상만 숨김 처리할 수 있습니다."}), 403
    elif comment["author_email"]:
        if comment["author_email"] != email:
            return jsonify({"error": "본인 작성분이 아닙니다. 숨길 수 없습니다."}), 403
    new_hidden = 0 if comment["hidden"] else 1
    # 숨김 처리(체크)는 곧 확인 완료이므로 is_checked도 함께 1로 — 다시 표시할 때는 건드리지 않는다.
    fields = {"hidden": bool(new_hidden)}
    if new_hidden:
        fields["is_checked"] = True
    _update("comments", cid, fields)
    return jsonify({"id": "c" + str(cid), "hidden": bool(new_hidden)})


@app.route("/api/comments/<int:cid>", methods=["PUT"])
def update_comment(cid):
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    comment = _row("comments", cid)
    if not comment:
        return jsonify({"error": "코멘트를 찾을 수 없습니다."}), 404
    content = (data.get("content") or "").strip()
    x_pct = data.get("x_pct")
    y_pct = data.get("y_pct")
    # 좌표가 포함되면 위치 이동으로 간주하고 권한 체크를 건너뛴다 (드래그 후 새로고침 복귀 방지).
    is_position_only = x_pct is not None or y_pct is not None
    if not is_position_only:
        if comment["author_email"] and not email:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        if comment["author_email"] and comment["author_email"] != email:
            return jsonify({"error": "본인 작성분이 아닙니다. 수정할 수 없습니다."}), 403
        if not content:
            return jsonify({"error": "내용을 입력해 주세요."}), 400
    if x_pct is not None:
        x_pct = max(0.0, min(100.0, float(x_pct)))
    if y_pct is not None:
        y_pct = max(0.0, min(100.0, float(y_pct)))
    new_content = comment["content"] if is_position_only else content
    fields = {"content": new_content}
    if x_pct is not None and y_pct is not None:
        fields["x_pct"] = x_pct
        fields["y_pct"] = y_pct
    updated = _update("comments", cid, fields)
    d = _comment_out(updated)
    d["comment_number"] = _comment_number(comment["page_id"], cid)
    return jsonify(d)


@app.route("/api/comments/<int:cid>", methods=["DELETE"])
def delete_comment(cid):
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    comment = _row("comments", cid)
    if not comment:
        return jsonify({"error": "코멘트를 찾을 수 없습니다."}), 404
    # 작성자만 삭제 가능 (author_email이 비어 있는 기존 데이터는 누구나)
    if comment["author_email"] and not email:
        return jsonify({"error": "로그인이 필요합니다."}), 401
    if comment["author_email"] and comment["author_email"] != email:
        return jsonify({"error": "본인 작성분이 아닙니다. 삭제할 수 없습니다."}), 403
    _delete("comments", cid)
    return jsonify({"ok": True})


# ─── Memos (메모 탭: 나만 보기 / 공개) ───────────────────────────────────────

@app.route("/api/pages/<int:page_id>/memos", methods=["GET"])
def list_memos(page_id):
    email = (request.args.get("email") or "").strip().lower()
    rows = _rows("memos", page_id=page_id, order_col="created_at", desc=True)
    out = []
    for r in rows:
        if email:
            # 본인 메모는 전부, 타인 메모는 공개된 것만
            if r["is_private"] and r["author_email"] != email:
                continue
        elif r["is_private"]:
            continue
        d = dict(_fmt(r))
        d["mine"] = bool(email and r["author_email"] == email)
        out.append(d)
    return jsonify(out)


@app.route("/api/pages/<int:page_id>/memos", methods=["POST"])
def create_memo(page_id):
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    content = (data.get("content") or "").strip()
    is_private = 1 if data.get("is_private") else 0
    if not content:
        return jsonify({"error": "메모 내용을 입력해 주세요."}), 400
    if not _row("pages", page_id):
        return jsonify({"error": "페이지를 찾을 수 없습니다."}), 404
    memo = _insert("memos", {
        "page_id": page_id, "author_name": name, "author_email": email,
        "content": content, "is_private": bool(is_private),
    })
    return jsonify(dict(_fmt(memo))), 201


@app.route("/api/memos/<int:mid>", methods=["PUT"])
def update_memo(mid):
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    memo = _row("memos", mid)
    if not memo:
        return jsonify({"error": "메모를 찾을 수 없습니다."}), 404
    if memo["author_email"] and memo["author_email"] != email:
        return jsonify({"error": "본인 작성분이 아닙니다. 수정할 수 없습니다."}), 403
    fields = {}
    if "content" in data:
        content = (data.get("content") or "").strip()
        if not content:
            return jsonify({"error": "메모 내용은 비울 수 없습니다."}), 400
        fields["content"] = content
    if "is_private" in data:
        fields["is_private"] = bool(data["is_private"])
    if fields:
        memo = _update("memos", mid, fields)
    return jsonify(dict(_fmt(memo)))


@app.route("/api/memos/<int:mid>", methods=["DELETE"])
def delete_memo(mid):
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    memo = _row("memos", mid)
    if not memo:
        return jsonify({"error": "메모를 찾을 수 없습니다."}), 404
    if memo["author_email"] and memo["author_email"] != email:
        return jsonify({"error": "본인 작성분이 아닙니다. 삭제할 수 없습니다."}), 403
    _delete("memos", mid)
    return jsonify({"ok": True})


# ─── Page Tags ───────────────────────────────────────────────────────────────

@app.route("/api/pages/<int:page_id>/tags", methods=["GET"])
def list_tags(page_id):
    rows = _rows("page_tags", page_id=page_id, order_col="tag_number")
    out = []
    for r in rows:
        d = dict(_fmt(r))
        d["desc_author_email"] = (r["author_email"] or "").lower()
        out.append(d)
    return jsonify(out)


# ─── Description Comments (태그에 달린 댓글 — 코멘트 탭과 무관) ─────────────

@app.route("/api/tags/<int:tag_id>/comments", methods=["GET"])
def list_tag_comments(tag_id):
    tag = _row("page_tags", tag_id)
    if not tag:
        return jsonify({}), 404
    # 해결된 태그의 댓글은 반환하지 않는다.
    if tag["is_resolved"]:
        return jsonify([])
    rows = _rows("comments", parent_tag_id=tag_id, order_col="created_at")
    out = []
    for i, r in enumerate(rows, 1):
        d = dict(_fmt(r))
        d["id"] = "c" + str(d["id"])
        d["comment_number"] = i
        out.append(d)
    return jsonify(out)


@app.route("/api/tags/<int:tag_id>/comments", methods=["POST"])
def add_tag_comment(tag_id):
    data = request.get_json(force=True)
    author = (data.get("author_name") or "").strip()
    content = (data.get("content") or "").strip()
    email = (data.get("email") or "").strip().lower()
    if not author or not content:
        return jsonify({"error": "이름과 내용을 모두 입력해 주세요."}), 400
    tag = _row("page_tags", tag_id)
    if not tag:
        return jsonify({"error": "태그를 찾을 수 없습니다."}), 404
    row = _insert("comments", {
        "page_id": tag["page_id"], "author_name": author, "content": content,
        "author_email": email, "parent_tag_id": tag_id,
    })
    # 새 답글이 왔으므로 태그를 다시 미해결 상태로 전환
    if tag["is_resolved"]:
        _update("page_tags", tag_id, {"is_resolved": False})
    # 디스크립션 댓글 알림: 태그 작성자에게 (본인 제외)
    tag_author = (tag["author_email"] or "").lower()
    if tag_author and tag_author != email:
        _notify(tag_author, "description", row["id"], f"{author}님이 내 디스크립션에 댓글을 달았습니다")
    d = dict(_fmt(row))
    d["id"] = "c" + str(row["id"])
    cnt = len([c for c in _rows("comments", parent_tag_id=tag_id) if c["id"] <= row["id"]])
    d["comment_number"] = cnt
    return jsonify(d), 201


@app.route("/api/tags/<int:tag_id>/comments/<int:cid>/check", methods=["POST"])
def toggle_tag_comment_check(tag_id, cid):
    """태그에 달린 댓글의 확인 완료 토글. 체크 시 목록에서 숨겨진다.
    태그 작성자 또는 해당 댓글의 작성자가 체크/해제할 수 있다."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    tag = _row("page_tags", tag_id)
    if not tag:
        return jsonify({"error": "태그를 찾을 수 없습니다."}), 404
    comment = _find("comments", id=cid, parent_tag_id=tag_id)
    if not comment:
        return jsonify({"error": "댓글을 찾을 수 없습니다."}), 404
    # 태그 작성자 또는 댓글 작성자만 체크/해제 가능 (작성자 비어 있으면 누구나)
    tag_author = (tag["author_email"] or "").lower()
    c_author = (comment["author_email"] or "").lower()
    is_allowed = (not tag_author and not c_author) or (
        email and (email == tag_author or email == c_author)
    )
    if not is_allowed:
        if not email:
            return jsonify({"error": "로그인 후 처리할 수 있습니다."}), 401
        return jsonify({"error": "태그 또는 댓글 작성자만 체크/해제할 수 있습니다."}), 403
    new_val = 0 if comment["is_checked"] else 1
    _update("comments", cid, {"is_checked": bool(new_val)})
    # 모든 댓글이 확인 완료가 되면 태그를 자동으로 해결로 표시
    remaining = [c for c in _rows("comments", parent_tag_id=tag_id) if not c["is_checked"]]
    resolved = 0 if remaining else 1
    _update("page_tags", tag_id, {"is_resolved": bool(resolved)})
    return jsonify({"id": cid, "is_checked": new_val, "is_resolved": resolved})


@app.route("/api/tags/<int:tag_id>/comments/<int:cid>", methods=["PUT"])
def update_tag_comment(tag_id, cid):
    """디스크립션 댓글 수정. 작성자만 가능하고, 체크된 댓글은 수정 불가."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "내용을 입력해 주세요."}), 400
    tag = _row("page_tags", tag_id)
    if not tag:
        return jsonify({"error": "태그를 찾을 수 없습니다."}), 404
    comment = _find("comments", id=cid, parent_tag_id=tag_id)
    if not comment:
        return jsonify({"error": "댓글을 찾을 수 없습니다."}), 404
    if comment["is_checked"]:
        return jsonify({"error": "확인 완료된 댓글은 수정할 수 없습니다."}), 403
    c_author = (comment["author_email"] or "").lower()
    if c_author and not email:
        return jsonify({"error": "로그인 후 처리할 수 있습니다."}), 401
    if c_author and c_author != email:
        return jsonify({"error": "본인 작성분이 아닙니다. 수정할 수 없습니다."}), 403
    updated = _update("comments", cid, {"content": content})
    d = dict(_fmt(updated))
    d["id"] = "c" + str(d["id"])
    return jsonify(d)


@app.route("/api/pages/<int:page_id>/tags", methods=["POST"])
def create_tag(page_id):
    data = request.get_json(force=True)
    x_pct = float(data.get("x_pct", 50))
    y_pct = float(data.get("y_pct", 50))
    description = (data.get("description") or "").strip()
    title = (data.get("title") or "").strip()
    email = (data.get("email") or "").strip().lower()
    author_name = (data.get("author_name") or "").strip()
    if not author_name:
        _u = _find("users", email=email)
        if _u:
            author_name = _u["name"]
    x_pct = max(0.0, min(100.0, x_pct))
    y_pct = max(0.0, min(100.0, y_pct))
    rows = _rows("page_tags", page_id=page_id)
    next_num = max((r["tag_number"] for r in rows), default=0) + 1
    tag = _insert("page_tags", {
        "page_id": page_id, "tag_number": next_num, "x_pct": x_pct, "y_pct": y_pct,
        "title": title, "description": description,
        "author_email": email, "author_name": author_name,
    })
    d = dict(_fmt(tag))
    # list_tags와 동일하게 desc_author_email을 붙여준다
    desc_row = _find("descriptions", page_id=page_id)
    d["desc_author_email"] = (desc_row["author_email"] or "") if desc_row else ""
    return jsonify(d), 201


@app.route("/api/tags/<int:tag_id>", methods=["PUT"])
def update_tag(tag_id):
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    tag = _row("page_tags", tag_id)
    if not tag:
        return jsonify({"error": "태그를 찾을 수 없습니다."}), 404
    # 디스크립션(내용) 수정과 위치 이동 모두 누구나 가능
    x_pct = data.get("x_pct", tag["x_pct"])
    y_pct = data.get("y_pct", tag["y_pct"])
    description = data.get("description", tag["description"])
    title = data.get("title", tag["title"] if "title" in tag.keys() else "")
    x_pct = max(0.0, min(100.0, float(x_pct)))
    y_pct = max(0.0, min(100.0, float(y_pct)))
    # is_resolved: 태그 작성자 또는 디스크립션 작성자가 체크/해제 가능
    if "is_resolved" in data:
        tag_author = (tag["author_email"] or "").lower()
        desc_row = _find("descriptions", page_id=tag["page_id"])
        desc_author = ((desc_row["author_email"] or "").lower() if desc_row else "")
        if not email:
            return jsonify({"error": "로그인이 필요합니다."}), 401
        allowed = []
        if tag_author:
            allowed.append(tag_author)
        if desc_author:
            allowed.append(desc_author)
        if allowed and email not in allowed:
            return jsonify({"error": "태그·디스크립션 작성자가 아닙니다."}), 403
    is_resolved = 1 if data.get("is_resolved") else 0
    updated = _update("page_tags", tag_id, {
        "x_pct": x_pct, "y_pct": y_pct, "title": title,
        "description": description, "is_resolved": bool(is_resolved),
    })
    return jsonify(dict(_fmt(updated)))


@app.route("/api/tags/<int:tag_id>", methods=["DELETE"])
def delete_tag(tag_id):
    data = request.get_json(silent=True) or {}
    tag = _row("page_tags", tag_id)
    if not tag:
        return jsonify({"error": "태그를 찾을 수 없습니다."}), 404
    # 태그 아래 달린 답글과, 그 답글을 가리키는 알림도 함께 삭제
    for c in _rows("comments", parent_tag_id=tag_id):
        _delete("comments", c["id"])
    for n in _rows("notifications", type="description"):
        if n["ref_id"] in {c["id"] for c in _rows("comments", parent_tag_id=tag_id)}:
            _delete("notifications", n["id"])
    _delete("page_tags", tag_id)
    # 남은 태그를 연속 번호로 재배치
    remaining = _rows("page_tags", page_id=tag["page_id"], order_col="tag_number")
    for i, r in enumerate(remaining, 1):
        if r["tag_number"] != i:
            _update("page_tags", r["id"], {"tag_number": i})
    return jsonify({"ok": True})


# ─── Notifications ───────────────────────────────────────────────────────────

def _active_notifications(email):
    """활성 알림 목록 — comments.is_checked=0 인 코멘트 계열 + is_read=0 인 기타 유형."""
    rows = _rows("notifications", user_email=email, order_col="id", desc=True)
    out = []
    for n in rows:
        ctype = n["type"]
        ref = n["ref_id"]
        if ctype in ("comment", "mention", "description"):
            c = _row("comments", ref) if ref else None
            if not c or c["is_checked"] or c["hidden"]:
                continue  # 고아 알림 / 체크됨 / 숨김
            out.append({**n, "is_checked": c["is_checked"]})
        else:
            if n["is_read"]:
                continue
            out.append(n)
    return out[:50]


@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    email = (request.args.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "로그인이 필요합니다."}), 401
    return jsonify([dict(_fmt(r)) for r in _active_notifications(email)])


@app.route("/api/notifications/unread-count", methods=["GET"])
def get_unread_count():
    email = (request.args.get("email") or "").strip().lower()
    if not email:
        return jsonify({"count": 0})
    return jsonify({"count": len(_active_notifications(email))})


@app.route("/api/notifications/<int:nid>/read", methods=["POST"])
def mark_notification_read(nid):
    """알림 하나를 읽음으로 표시. 체크박스 토글 지원."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "로그인이 필요합니다."}), 401
    row = _row("notifications", nid)
    if not row or row["user_email"].lower() != email:
        return jsonify({"error": "알림을 찾을 수 없습니다."}), 404
    new_val = 0 if row["is_read"] else 1
    _update("notifications", nid, {"is_read": bool(new_val)})
    return jsonify({"id": nid, "is_read": new_val})


@app.route("/api/notifications/<int:nid>/resolve", methods=["POST"])
def toggle_notification_resolved(nid):
    """알림의 관련 태그 is_resolved 토글 + 알림 읽음 처리."""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "로그인이 필요합니다."}), 401
    row = _row("notifications", nid)
    if not row or row["user_email"].lower() != email:
        return jsonify({"error": "알림을 찾을 수 없습니다."}), 404
    # 항상 읽음으로 처리
    _update("notifications", nid, {"is_read": True})
    resolved_val = 0
    c = _row("comments", row["ref_id"]) if row["ref_id"] else None
    if c and c["parent_tag_id"]:
        trow = _row("page_tags", c["parent_tag_id"])
        if trow:
            new_res = 0 if trow["is_resolved"] else 1
            _update("page_tags", c["parent_tag_id"], {"is_resolved": bool(new_res)})
            resolved_val = new_res
    return jsonify({"ok": True, "is_resolved": resolved_val})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)
