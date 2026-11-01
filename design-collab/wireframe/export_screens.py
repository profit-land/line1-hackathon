"""현재 디자인 코랩(Supabase) 프로젝트의 와이어프레임 화면을 정적 HTML 파일로 내보낸다.
로컬 서버(http://localhost:5002)가 떠 있어야 한다.
사용자가 사이드바에서 직접 지운 화면은 다시 만들지 않고, 지금 남아있는 화면만 그대로 내보낸다.
"""
import json
import os
import re
import urllib.request

API = "http://localhost:5002"
PROJECT_ID = 3
OUT_DIR = os.path.join(os.path.dirname(__file__), "screens")


def call(path):
    with urllib.request.urlopen(API + path) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    pages = call(f"/api/projects/{PROJECT_ID}/pages")

    def sort_key(p):
        m = re.match(r"([A-Z])-?(\d+)?", p["name"])
        return (m.group(1) if m else "Z", int(m.group(2)) if m and m.group(2) else 0)

    pages.sort(key=sort_key)

    index_rows = []
    for p in pages:
        sid = p["name"].split(" ")[0]
        fname = f"{sid}.html"
        with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as f:
            f.write(p["html_content"])
        index_rows.append((sid, p["name"], fname))

    index_html = """<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
<title>와이어프레임 화면 목록</title>
<style>
body{font-family:sans-serif;max-width:720px;margin:40px auto;padding:0 16px;color:#212529}
h1{font-size:20px}
ul{list-style:none;padding:0}
li{border-bottom:1px solid #eee;padding:10px 0}
a{color:#4f46e5;text-decoration:none;font-weight:600}
a:hover{text-decoration:underline}
.sid{display:inline-block;width:48px;color:#868e96;font-weight:700}
</style></head><body>
<h1>그림책 표현 학습 와이어프레임</h1>
<p>디자인 코랩에서 만든 화면 목록 (정적 스냅샷, 클릭 네비게이션은 이 파일들만 모아서 열면 동작하지 않을 수 있음).</p>
<ul>
""" + "\n".join(
        f'<li><span class="sid">{sid}</span><a href="{fname}">{name}</a></li>'
        for sid, name, fname in index_rows
    ) + "\n</ul></body></html>"

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    print(f"exported {len(pages)} screens to {OUT_DIR}")


if __name__ == "__main__":
    main()
