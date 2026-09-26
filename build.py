"""Build the GE110 study website from the สรุป-*.md / quiz-*.html files in this folder.

Usage:  python build.py
Output: ./docs  (served by GitHub Pages: main /docs)
"""
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote

from markdown_it import MarkdownIt
from mdit_py_plugins.anchors import anchors_plugin

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"

COURSE = {
    "code": "GE110",
    "name": "วิทยาศาสตร์และเทคโนโลยีในชีวิตประจำวัน",
    "th": "สรุปบทที่ 5–8 พร้อมแบบทดสอบ",
    "accent": "#0f766e",
}
# chapter number -> (icon, accent)
CHAPTERS = {5: ("💄", "#db2777"), 6: ("🏃", "#16a34a"), 7: ("👕", "#7c3aed"), 8: ("🏠", "#c2410c")}

md = MarkdownIt("gfm-like", {"html": True, "linkify": False, "typographer": False})
md.use(anchors_plugin, min_level=2, max_level=3, slug_func=lambda s: slugify(s))
_slug_seen: dict = {}


def slugify(text: str) -> str:
    s = re.sub(r"[^\w฀-๿\s-]", "", text).strip().lower()
    s = re.sub(r"[\s_]+", "-", s) or "sec"
    n = _slug_seen.get(s, 0)
    _slug_seen[s] = n + 1
    return s if n == 0 else f"{s}-{n}"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;500;600;700'
         '&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">')
THEME_BOOT = ("<script>try{var t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t;}"
              "catch(e){}</script>")


def page(title, body, depth, accent=COURSE["accent"]):
    base = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
{THEME_BOOT}
{FONTS}
<link rel="stylesheet" href="{base}assets/style.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🔬</text></svg>">
<style>:root{{--accent:{accent}}}</style>
</head>
<body>
<div id="progress"></div>
<header class="topbar">
  <a class="brand" href="{base}index.html">🔬 <span>{COURSE['code']} สรุปบทเรียน</span></a>
  <div class="topbar-right">
    <button class="icon-btn" id="themeBtn" title="สลับโหมดมืด/สว่าง" aria-label="toggle theme">◐</button>
  </div>
</header>
{body}
<footer class="foot">สรุปโดย Claude จากสไลด์ประกอบการเรียน · {COURSE['code']} {COURSE['name']}</footer>
<script src="{base}assets/app.js"></script>
</body>
</html>"""


def render(text):
    global _slug_seen
    _slug_seen = {}
    text = re.sub(r"^#\s+.+\n", "", text, count=1)
    text = re.sub(r"^(>[ \t]*\S.*)\n(?=>[ \t]*[^\s\-*|\d>])", r"\1\n>\n", text, flags=re.M)
    body = md.render(text)
    body = body.replace("<img ", '<img loading="lazy" ')
    body = re.sub(r"<blockquote>", '<blockquote class="callout">', body)
    body = re.sub(r"<p>(💡)", r'<p class="c-tip">\1', body)
    body = re.sub(r"<p>(⚠️)", r'<p class="c-warn">\1', body)
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    toc = []
    for m in re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>', body):
        label = html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))
        if label.strip() != "สารบัญ":
            toc.append((m.group(1), label))
    body = re.sub(r'<h2 id="[^"]*">สารบัญ.*?</h2>\s*<ol>.*?</ol>\s*(<hr />\s*)?', "", body, count=1, flags=re.S)
    return body, toc


QUIZ_BAR = """<div style="position:sticky;top:0;z-index:50;margin:-24px -16px 20px;padding:10px 16px;background:rgba(245,246,250,.92);backdrop-filter:blur(8px);border-bottom:1px solid #e3e5ee;display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:.92rem">
<a href="index.html" style="color:#3f51b5;text-decoration:none;font-weight:600">← กลับไปอ่านสรุป</a>
<span style="color:#999">|</span>
<a href="../index.html" style="color:#555;text-decoration:none">หน้าแรก</a>
</div>"""


def find_lessons():
    lessons = []
    for f in sorted(ROOT.glob("สรุป-บทที่*.md")):
        n = int(re.search(r"บทที่(\d+)", f.name).group(1))
        text = f.read_text(encoding="utf-8")
        title = re.search(r"^#\s+(.+)$", text, re.M).group(1)
        title = re.sub(r"^สรุป\s*[:：]\s*", "", title)
        title = re.sub(r"\s*\(GE110.*?\)\s*$", "", title)
        quiz = next(iter(ROOT.glob(f"quiz-บทที่{n}-*.html")), None)
        icon, accent = CHAPTERS.get(n, ("📘", COURSE["accent"]))
        lessons.append({"n": n, "slug": f"ch{n}", "title": title, "md": text, "quiz": quiz,
                        "icon": icon, "accent": accent})
    return sorted(lessons, key=lambda l: l["n"])


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("")

    lessons = find_lessons()
    search_index, rows = [], ""
    for i, les in enumerate(lessons):
        ldir = OUT / les["slug"]
        (ldir / "img").mkdir(parents=True)
        for img in ROOT.glob(f"img/ch{les['n']}-*"):
            shutil.copy2(img, ldir / "img" / img.name)

        body, toc = render(les["md"])
        toc_html = "".join(f'<li><a href="#{a}">{esc(t)}</a></li>' for a, t in toc)
        quiz_btn = '<a class="btn btn-quiz" href="quiz.html">📝 ทำแบบทดสอบ</a>' if les["quiz"] else ""
        prev_l = lessons[i - 1] if i > 0 else None
        next_l = lessons[i + 1] if i + 1 < len(lessons) else None
        pager = '<nav class="pager">'
        pager += (f'<a class="pg prev" href="../{prev_l["slug"]}/index.html"><small>← บทก่อนหน้า</small>'
                  f'<span>{esc(prev_l["title"])}</span></a>' if prev_l else "<span></span>")
        pager += (f'<a class="pg next" href="../{next_l["slug"]}/index.html"><small>บทถัดไป →</small>'
                  f'<span>{esc(next_l["title"])}</span></a>' if next_l else "<span></span>")
        pager += "</nav>"
        quiz_end = (f'<div class="quiz-cta"><div><strong>อ่านจบแล้ว? ลองทดสอบความเข้าใจ</strong>'
                    f'<p>แบบทดสอบ 30 ข้อ 4 ตัวเลือก เฉลยพร้อมเหตุผลทันที</p></div>{quiz_btn}</div>'
                    if les["quiz"] else "")
        content = f"""
  <div class="lesson-layout">
    <aside class="toc" id="toc">
      <button class="toc-toggle" id="tocToggle">☰ สารบัญ</button>
      <div class="toc-inner">
        <a class="toc-back" href="../index.html">← ทุกบท</a>
        <ol>{toc_html}</ol>
      </div>
    </aside>
    <main class="lesson">
      <div class="crumbs"><a href="../index.html">หน้าแรก</a> / {les['icon']} บทที่ {les['n']}</div>
      <h1 class="lesson-title">{esc(les['title'])}</h1>
      <div class="lesson-actions">{quiz_btn}</div>
      <article class="prose">{body}</article>
      {quiz_end}
      {pager}
    </main>
  </div>"""
        (ldir / "index.html").write_text(page(f"{les['title']} · {COURSE['code']}", content, 1, les["accent"]),
                                         encoding="utf-8")
        if les["quiz"]:
            q = les["quiz"].read_text(encoding="utf-8")
            q = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + QUIZ_BAR, q, count=1)
            q = q.replace("<head>", '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">', 1)
            (ldir / "quiz.html").write_text(q, encoding="utf-8")

        search_index.append({"s": f"บทที่ {les['n']}", "t": les["title"], "u": f"{les['slug']}/index.html",
                             "h": [t for _, t in toc]})
        qlink = f'<a class="chip chip-quiz" href="{les["slug"]}/quiz.html">📝 Quiz</a>' if les["quiz"] else ""
        rows += (f'<li class="lesson-row"><span class="num">{les["icon"]}</span>'
                 f'<a class="lesson-link" href="{les["slug"]}/index.html"><small>{COURSE["code"]} · บทที่ {les["n"]}</small>'
                 f'<span>{esc(les["title"])}</span></a>'
                 f'<div class="row-actions"><a class="chip" href="{les["slug"]}/index.html">📖 อ่าน</a>{qlink}</div></li>')

    # extra files published unchanged (e.g. the practice exam PDF), listed above the chapters
    exam_rows = ""
    # combined quizzes covering every chapter: quiz-รวม*.html -> docs/review-<n>/quiz.html
    for n, cq in enumerate(sorted(ROOT.glob("quiz-รวม*.html")), 1):
        qdir = OUT / f"review-{n}"
        qdir.mkdir(exist_ok=True)
        q = cq.read_text(encoding="utf-8")
        bar = QUIZ_BAR.replace('<a href="index.html" style="color:#3f51b5;text-decoration:none;font-weight:600">← กลับไปอ่านสรุป</a>\n<span style="color:#999">|</span>\n', "")
        q = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + bar, q, count=1)
        q = q.replace("<head>", '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">', 1)
        (qdir / "quiz.html").write_text(q, encoding="utf-8")
        title = re.search(r"<h1>Quiz: (.*?)</h1>", q).group(1)
        exam_rows += (f'<li class="lesson-row"><span class="num">🎯</span>'
                      f'<a class="lesson-link" href="{qdir.name}/quiz.html"><small>แบบทดสอบรวมทุกบท · บทละ 20 ข้อ</small>'
                      f'<span>{esc(title)}</span></a>'
                      f'<div class="row-actions"><a class="chip chip-quiz" href="{qdir.name}/quiz.html">📝 ทำแบบทดสอบ</a></div></li>')
    for pdf in sorted(ROOT.glob("*.pdf")):
        shutil.copy2(pdf, OUT / pdf.name)
        href = quote(pdf.name)
        # interactive version of the same exam: quiz-<pdf stem>-*.html -> docs/exam-<n>/quiz.html
        quiz = next(iter(ROOT.glob(f"quiz-{pdf.stem}-*.html")), None)
        qhref = ""
        if quiz:
            qdir = OUT / ("exam-" + re.sub(r"\D", "", pdf.stem))
            qdir.mkdir(exist_ok=True)
            q = quiz.read_text(encoding="utf-8")
            bar = QUIZ_BAR.replace('href="index.html"', f'href="../{href}" target="_blank"').replace(
                "← กลับไปอ่านสรุป", "📄 เปิดข้อสอบ PDF ต้นฉบับ")
            q = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + "\n" + bar, q, count=1)
            q = q.replace("<head>", '<head>\n<meta name="viewport" content="width=device-width, initial-scale=1">', 1)
            (qdir / "quiz.html").write_text(q, encoding="utf-8")
            qhref = f"{qdir.name}/quiz.html"
        main_href = qhref or href
        exam_rows += (f'<li class="lesson-row"><span class="num">🎯</span>'
                      f'<a class="lesson-link" href="{main_href}"><small>แบบฝึกหัดทบทวนก่อนสอบ · รวมทุกบท</small>'
                      f'<span>{esc(pdf.stem)} — ข้อสอบบทที่ 5–8 (70 ข้อ พร้อมเฉลย)</span></a>'
                      f'<div class="row-actions">'
                      + (f'<a class="chip chip-quiz" href="{qhref}">📝 ทำข้อสอบ</a>' if qhref else "")
                      + f'<a class="chip" href="{href}" target="_blank">📄 PDF</a></div></li>')
    exam_block = (f'<h2 style="margin:24px 0 8px">🎯 แบบทดสอบรวม</h2><ol class="lesson-list">{exam_rows}</ol>'
                  f'<h2 style="margin:24px 0 8px">📖 สรุปรายบท</h2>' if exam_rows else "")

    nq = sum(1 for l in lessons if l["quiz"])
    home = f"""
<main class="wrap">
  <section class="home-hero">
    <h1>{COURSE['code']} {COURSE['name']}</h1>
    <p>{COURSE['th']} · {len(lessons)} บทสรุป · {nq} แบบทดสอบ — อ่านสรุปพร้อมรูปสไลด์ แล้วทดสอบความเข้าใจท้ายบท</p>
    <div class="search">
      <input id="q" type="search" placeholder="ค้นหาหัวข้อ เช่น SPF, BMI, เรยอน, 4R…" autocomplete="off">
      <ul id="results"></ul>
    </div>
  </section>
  {exam_block}<ol class="lesson-list">{rows}</ol>
</main>
<script>window.SEARCH_INDEX = {json.dumps(search_index, ensure_ascii=False)};</script>"""
    (OUT / "index.html").write_text(page(f"{COURSE['code']} · สรุปบทเรียน", home, 0), encoding="utf-8")
    print("built", sum(1 for _ in OUT.rglob("*.html")), "html files")


if __name__ == "__main__":
    build()
