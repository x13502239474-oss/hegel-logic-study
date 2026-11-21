# -*- coding: utf-8 -*-
"""静态站点构建：把 content/ 下的 Markdown 与数据渲染为移动优先的静态页面。"""
import os, re, json, math, html, importlib.util, datetime, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content")
OUT = ROOT

import markdown
from markdown.extensions import Extension

# ----------------------------------------------------------------------------
# 元数据
# ----------------------------------------------------------------------------
def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

course = load_module("course", os.path.join(CONTENT, "course.py"))
SITE = course.SITE
PARTS = course.PARTS
CHAPTERS = course.CHAPTERS
CONCEPTS = course.CONCEPTS
TOPIC_BY_NUM = course.TOPIC_BY_NUM
CHAPTER_BY_NUM = course.CHAPTER_BY_NUM
PARTS_BY_NUM = course.PARTS_BY_NUM

try:
    derive_data = load_module("derivation", os.path.join(CONTENT, "derivation.py"))
    STEPS = derive_data.STEPS
except Exception:
    STEPS = []

try:
    net_data = load_module("network", os.path.join(CONTENT, "network.py"))
    NET_NODES, NET_EDGES = net_data.NODES, net_data.EDGES
except Exception:
    NET_NODES, NET_EDGES = [], []

try:
    cmp_data = load_module("compare", os.path.join(CONTENT, "compare.py"))
    CMP_COLS, CMP_ROWS, CMP_NOTES = cmp_data.COLS, cmp_data.ROWS, cmp_data.NOTES
except Exception:
    CMP_COLS, CMP_ROWS, CMP_NOTES = [], [], []

try:
    gl_data = load_module("glossary", os.path.join(CONTENT, "glossary.py"))
    GLOSSARY = gl_data.ENTRIES
except Exception:
    GLOSSARY = []

# ----------------------------------------------------------------------------
# Markdown
# ----------------------------------------------------------------------------
md = markdown.Markdown(extensions=["extra", "sane_lists", "footnotes", "attr_list"],
                       extension_configs={"footnotes": {"BACKLINK_TEXT": "↩"}})

HEAD_IDS = {
    "本章导读": "intro",
    "原著位置与文本结构": "locus",
    "本章总结": "summary",
    "学术争议与解释分歧": "debate",
    "思想比较": "compare",
    "现实联系": "relevance",
    "延伸阅读": "reading",
    "概念定义": "definition",
    "原著中的位置": "locus",
    "哲学背景": "background",
    "逻辑推演": "derivation",
    "通俗解释": "plain",
    "典型例子": "examples",
    "与其他概念的联系": "relations",
    "常见误解": "misreadings",
}

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩"


def _prep_derive(inner):
    lines = inner.split("\n")
    out, in_item = [], False
    for ln in lines:
        s = ln.strip()
        if s and s[0] in CIRCLED:
            if in_item:
                out.append("")
            out.append("1. " + s[1:].strip())
            in_item = True
        elif s:
            out.append(ln)
            in_item = False
        else:
            out.append(ln)
            in_item = False
    return "\n".join(out)


def render_containers(text):
    """把 :::kind 标题 ... ::: 容器转换为 HTML，递归处理内部 Markdown。"""
    pattern = re.compile(r"^:::(\w+)(?:[ \t]+(.+?))?[ \t]*\n(.*?)\n:::[ \t]*$", re.S | re.M)
    while True:
        m = pattern.search(text)
        if not m:
            break
        kind, title, inner = m.group(1), (m.group(2) or "").strip(), m.group(3)
        if kind == "derive":
            body = md.reset().convert(_prep_derive(inner))
            block = (
                '<div class="derive"><div class="derive-h">%s</div>%s</div>'
                % (html.escape(title or "推演"), body)
            )
        elif kind == "src":
            body = md.reset().convert(inner)
            block = (
                '<figure class="src"><div class="src-h"><span>原文</span><b>%s</b></div>%s</figure>'
                % (html.escape(title or ""), body)
            )
        elif kind in ("note", "pitfall", "compare-box"):
            cls = {"note": "note", "pitfall": "pitfall", "compare-box": "compare-box"}[kind]
            label = {"note": "提示", "pitfall": "常见误解", "compare-box": "对照"}[kind]
            body = md.reset().convert(inner)
            block = '<div class="%s"><div class="%s-h">%s</div>%s</div>' % (
                cls, cls.replace("compare-box", "compare"), html.escape(title or label), body)
        else:
            body = md.reset().convert(inner)
            block = '<div class="note"><div class="note-h">%s</div>%s</div>' % (
                html.escape(title or kind), body)
        text = text[:m.start()] + "\n\n" + block + "\n\n" + text[m.end():]
    return text


def auto_id(text):
    return "s-" + hashlib.md5(text.encode("utf-8")).hexdigest()[:8]


def md_to_html(raw):
    text = render_containers(raw.strip())
    md.reset()
    out = md.convert(text)
    # 表格包裹
    out = out.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    # 标题锚点
    def h2_repl(m):
        inner = m.group(1)
        tm = re.match(r"^(\d+)\s*[｜|]\s*(.+)$", inner)
        if tm:
            n, title = tm.group(1), tm.group(2)
            return '<h2 id="t%s"><span class="tno">%s</span>%s</h2>' % (n, n, title)
        plain = re.sub(r"<[^>]+>", "", inner)
        hid = HEAD_IDS.get(plain, auto_id(plain))
        return '<h2 id="%s">%s</h2>' % (hid, inner)
    out = re.sub(r"<h2>(.*?)</h2>", h2_repl, out, flags=re.S)
    return out


def toc_from_raw(raw):
    items = []
    for line in raw.split("\n"):
        m = re.match(r"^##\s+(?!#)(.+?)\s*$", line)
        if not m:
            continue
        inner = m.group(1).strip()
        tm = re.match(r"^(\d+)\s*[｜|]\s*(.+)$", inner)
        if tm:
            items.append(("t" + tm.group(1), tm.group(1), tm.group(2)))
        else:
            items.append((HEAD_IDS.get(inner, auto_id(inner)), "", inner))
    return [i for i in items if i[0]]


def reading_minutes(raw):
    cn = len(re.findall(r"[\u4e00-\u9fff]", raw))
    return max(3, int(round(cn / 420.0)))


# ----------------------------------------------------------------------------
# 页面外壳
# ----------------------------------------------------------------------------
NAV = [
    ("course.html", "课程总览"),
    ("atlas.html", "全景图"),
    ("derivation.html", "范畴推演"),
    ("network.html", "概念网络"),
    ("compare.html", "概念对照"),
    ("glossary.html", "术语词典"),
    ("about.html", "关于本站"),
]


def nav_html(active=""):
    out = []
    for href, label in NAV:
        cur = ' aria-current="page"' if href == active else ""
        out.append('<a href="%s"%s>%s</a>' % (href, cur, label))
    return "".join(out)


def drawer_html(active=""):
    out = []
    for href, label in NAV:
        out.append('<a href="%s">%s<small>%s</small></a>' % (href, label, href.split(".")[0].upper()))
    return "".join(out)


def shell(title, body, active="", desc="", extra_head="", body_class=""):
    full_title = title if title.startswith(SITE["name"]) else "%s · %s" % (title, SITE["name"])
    return f"""<!DOCTYPE html>
<html lang="zh-Hans">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(full_title)}</title>
<meta name="description" content="{html.escape(desc or '以黑格尔《小逻辑》为底本的系统课程：存在论、本质论与概念论的逐范畴推演。')}">
<meta name="theme-color" content="#f8f3e7">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%23f8f3e7'/%3E%3Crect x='3' y='3' width='58' height='58' fill='none' stroke='%233a2b20' stroke-width='2'/%3E%3Crect x='7' y='7' width='50' height='50' fill='none' stroke='%239a7a3f' stroke-width='1'/%3E%3Ctext x='32' y='43' font-family='Georgia,serif' font-size='30' fill='%233a2b20' text-anchor='middle'%3EH%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="assets/css/style.css">
{extra_head}
</head>
<body class="{body_class}">
<a class="skip" href="#main">跳转到正文</a>
<div class="progress" id="progress" aria-hidden="true"></div>
<header class="header">
  <div class="header-in">
    <a class="brand" href="index.html" aria-label="返回首页">
      <span class="monogram" aria-hidden="true">H</span>
      <span class="brand-txt">
        <span class="brand-cn">黑格尔逻辑学研究室</span>
        <span class="brand-en">Hegel&rsquo;s Science of Logic Study Institute</span>
      </span>
    </a>
    <nav class="nav" aria-label="主导航">{nav_html(active)}</nav>
    <button class="menu-btn" id="menuBtn" aria-expanded="false" aria-controls="drawer">目录 <span aria-hidden="true"></span></button>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="footer">
  <div class="footer-in">
    <div>
      <h4>关于本站</h4>
      <p>以《小逻辑》（贺麟译，商务印书馆）为底本的系统课程，按原著三部分逐范畴讲解。全站 14 章、112 讲、25 个概念专题。</p>
      <p><a href="about.html">编纂说明与参考文献 →</a></p>
    </div>
    <div>
      <h4>课程</h4>
      <ul>
        <li><a href="course.html">全部章节</a></li>
        <li><a href="atlas.html">逻辑学全景图</a></li>
        <li><a href="derivation.html">范畴推演图</a></li>
        <li><a href="glossary.html">哲学术语词典</a></li>
      </ul>
    </div>
    <div>
      <h4>阅读</h4>
      <ul>
        <li><a href="ch01.html">从第一章开始</a></li>
        <li><a href="concept-pure-being.html">纯存在</a></li>
        <li><a href="being-nothing-becoming.html">精读：有—无—生成</a></li>
        <li><a href="compare.html">黑格尔与康德、马克思</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-in" style="padding-top:0">
    <div class="colophon">
      <span>黑格尔逻辑学研究室 · {SITE['built']}</span>
      <span>底本：G. W. F. Hegel, <i>Enzyklopädie der philosophischen Wissenschaften im Grundrisse</i>, Erster Teil</span>
      <span>中译参照：贺麟译本（§1–§244）</span>
    </div>
  </div>
</footer>
<button class="to-top" id="toTop" aria-label="返回顶部">↑</button>
<div class="drawer" id="drawer" role="dialog" aria-modal="true" aria-label="站点目录">
  <div class="drawer-panel">
    <div class="drawer-head">
      <span class="drawer-title">目录</span>
      <button class="drawer-close" id="drawerClose" aria-label="关闭">×</button>
    </div>
    {drawer_html(active)}
  </div>
</div>
<script src="assets/js/site.js"></script>
{extra_head and ''}
</body>
</html>"""


def page_head(kicker, title, lede="", de=""):
    return f"""<div class="wrap">
<header class="page-head">
  <div class="kicker">{kicker}</div>
  <h1>{title}</h1>
  {f'<div class="de" style="font-family:Georgia,serif;font-style:italic;color:var(--ink-4);margin-top:.5rem">{de}</div>' if de else ''}
  {f'<p>{lede}</p>' if lede else ''}
</header>
</div>"""


# ----------------------------------------------------------------------------
# 章节
# ----------------------------------------------------------------------------
def chapter_path(num):
    return os.path.join(CONTENT, "chapters", "ch%02d.md" % num)


def related_concepts(num):
    return [c for c in CONCEPTS if num in c[6]]


def build_chapter(ch):
    num = ch["num"]
    part = course.PARTS_BY_NUM[ch["part"]]
    p = chapter_path(num)
    if os.path.exists(p):
        raw = open(p, encoding="utf-8").read()
    else:
        raw = ("## 本章导读\n\n本章正文正在编纂中。\n\n## 原著位置与文本结构\n\n"
               "对应 %s。\n\n## 本章总结\n\n待补。\n" % ch["secs"])
    body_html = md_to_html(raw)
    toc = toc_from_raw(raw)
    mins = reading_minutes(raw)

    first, last = ch["topics"][0][0], ch["topics"][-1][0]
    idx = [c["num"] for c in CHAPTERS].index(num)
    prev_ch = CHAPTERS[idx - 1] if idx > 0 else None
    next_ch = CHAPTERS[idx + 1] if idx < len(CHAPTERS) - 1 else None

    toc_items = "".join(
        '<li><a href="#%s">%s%s</a></li>' % (i, ('<span class="n">%s</span>' % n) if n else "", t)
        for (i, n, t) in toc
    )
    rail_items = "".join(
        '<a href="#%s">%s%s</a>' % (i, ('<span class="n">%s</span>' % n) if n else "", t)
        for (i, n, t) in toc
    )

    rel = related_concepts(num)
    rel_html = ""
    if rel:
        rel_html = '<div class="related"><h2>相关概念专题</h2><ul>%s</ul></div>' % "".join(
            '<li><a href="concept-%s.html">%s <span style="color:var(--bronze);font-size:.9em">%s</span></a></li>'
            % (c[0], c[2], c[3]) for c in rel)

    chain = ch.get("chain")
    chain_html = ""
    if chain:
        parts = []
        for i, (label, tn) in enumerate(chain):
            if i:
                parts.append('<span class="cc-ar" aria-hidden="true">→</span>')
            parts.append('<a href="#t%d">%s</a>' % (tn, label))
        chain_html = ('<div class="chapter-chain"><span class="cc-label">本章推演</span>'
                      '<div class="cc-track">%s</div></div>' % "".join(parts))

    pager = '<div class="pager">'
    if prev_ch:
        pager += ('<a href="ch%02d.html"><span class="lab">上一章</span><span class="tt">%s</span></a>'
                  % (prev_ch["num"], prev_ch["title"]))
    else:
        pager += '<span class="empty"></span>'
    if next_ch:
        pager += ('<a class="next" href="ch%02d.html"><span class="lab">下一章</span><span class="tt">%s</span></a>'
                  % (next_ch["num"], next_ch["title"]))
    else:
        pager += '<span class="empty"></span>'
    pager += "</div>"

    body = f"""<div class="wrap">
<header class="article-head">
  <div class="crumb"><a href="index.html">首页</a><span>/</span><a href="part{part['num']}.html">{part['title']}</a><span>/</span>第 {num} 章</div>
  <div class="pnum">第 {num} 章 · 课程 {first}–{last}</div>
  <h1>{ch['title']}</h1>
  <div class="de">{ch['de']}</div>
  <div class="article-meta">
    <span>原著 <b>{ch['secs']}</b></span>
    <span>所属 <b>{part['title']}</b></span>
    <span>篇幅 <b>约 {mins} 分钟</b></span>
    <span>体例 <b>导读 · 原文 · 推演 · 争议</b></span>
  </div>
</header>
{chain_html}
<div class="article-body">
  <article class="prose" id="article">
    <details class="toc-mobile"><summary>本章目录（{len(toc)} 节）</summary><ol>{toc_items}</ol></details>
    {body_html}
    {rel_html}
    {pager}
  </article>
  <aside class="rail" aria-label="本章目录">
    <div class="rail-inner">
      <div class="rail-title">本章目录</div>
      {rail_items}
      <div class="rail-title" style="margin-top:1.4rem">快速跳转</div>
      <a href="derivation.html">范畴推演图</a>
      <a href="network.html">概念网络</a>
      <a href="glossary.html">术语词典</a>
    </div>
  </aside>
</div>
</div>"""
    out = shell("第%d章 %s" % (num, ch["title"]), body, active="course.html",
                desc=ch["gist"])
    open(os.path.join(OUT, "ch%02d.html" % num), "w", encoding="utf-8").write(out)


# ----------------------------------------------------------------------------
# 课程总览
# ----------------------------------------------------------------------------
def build_course():
    blocks = []
    for part in PARTS:
        chs = [c for c in CHAPTERS if c["part"] == part["num"]]
        rows = []
        for c in chs:
            topics = "".join(
                '<li><a href="ch%02d.html#t%d"><b>%d</b><span>%s</span></a></li>' % (c["num"], n, n, t)
                for (n, t, s) in c["topics"]
            )
            rows.append(f"""<div class="chap-row">
  <div class="cn">{c['num']:02d}</div>
  <div>
    <h3><a href="ch{c['num']:02d}.html">{c['title']}</a><span class="cs">{c['secs']}</span></h3>
    <ol>{topics}</ol>
  </div>
</div>""")
        blocks.append(f"""<section class="part-block">
  <header>
    <h2>{part['title']}</h2>
    <span class="pde">{part['de']}</span>
    <span class="pmeta">第 {part['num']} 部分 · 课程 {part['range'][0]}–{part['range'][1]}</span>
  </header>
  <p class="lead">{part['gist']}</p>
  {''.join(rows)}
</section>""")

    body = page_head("Curriculum · 课程", "课程总览",
                     "五部分、十四章、一百一十二讲。按原著三部分推进：存在论从最贫乏的范畴开始，本质论进入反思的中介，概念论达到自我规定的自由。",
                     "Der Gang der Logik") + f'<div class="wrap" style="padding-bottom:2rem">{"".join(blocks)}</div>'
    open(os.path.join(OUT, "course.html"), "w", encoding="utf-8").write(
        shell("课程总览", body, active="course.html"))


def build_part(part):
    chs = [c for c in CHAPTERS if c["part"] == part["num"]]
    cards = []
    for c in chs:
        topics = "".join('<li><a href="ch%02d.html#t%d"><b>%d</b>%s</a></li>' % (c["num"], n, n, t)
                         for (n, t, s) in c["topics"])
        cards.append(f"""<div class="chap-row">
  <div class="cn">{c['num']:02d}</div>
  <div>
    <h3><a href="ch{c['num']:02d}.html">{c['title']}</a><span class="cs">{c['secs']}</span></h3>
    <p style="margin:.3rem 0 0;font-size:.84rem;color:var(--ink-3)">{c['gist']}</p>
    <ol>{topics}</ol>
  </div>
</div>""")
    body = page_head("Part %d · 第%s部分" % (part["num"], "一二三四五"[part["num"] - 1]),
                     part["title"], part["lead"], part["de"])
    body += f'<div class="wrap" style="padding-bottom:2rem">{"".join(cards)}</div>'
    open(os.path.join(OUT, "part%d.html" % part["num"]), "w", encoding="utf-8").write(
        shell(part["title"], body, active="course.html"))


# ----------------------------------------------------------------------------
# 概念页
# ----------------------------------------------------------------------------
def build_concept(c):
    slug, no, cn, de, en, secs, chs, short = c
    p = os.path.join(CONTENT, "concepts", slug + ".md")
    raw = open(p, encoding="utf-8").read() if os.path.exists(p) else "## 概念定义\n\n待补。\n"
    body_html = md_to_html(raw)
    toc = toc_from_raw(raw)
    rail = "".join('<a href="#%s">%s</a>' % (i, t) for (i, n, t) in toc)
    ch_links = "".join('<a href="ch%02d.html">第 %d 章 · %s</a>' % (n, n, CHAPTER_BY_NUM[n]["title"]) for n in chs)
    body = f"""<div class="wrap">
<header class="concept-head">
  <div class="crumb"><a href="index.html">首页</a><span>/</span><a href="network.html">概念网络</a><span>/</span>专题 {no:02d}</div>
  <div class="no">概念专题 {no:02d} / 25</div>
  <h1>{cn}</h1>
  <div><span class="term-de">{de}</span><span class="term-en">{en}</span></div>
  <p class="def">{short}</p>
  <span class="ghost-no" aria-hidden="true">{no:02d}</span>
  <dl class="dossier">
    <div><dt>德文</dt><dd>{de}</dd></div>
    <div><dt>英文</dt><dd>{en}</dd></div>
    <div><dt>原著</dt><dd>{secs}</dd></div>
    <div><dt>所在</dt><dd>{ch_links}</dd></div>
  </dl>
</header>
<div class="concept-grid">
  <article class="prose">{body_html}
    <div class="related"><h2>继续</h2><ul>
      <li><a href="network.html">在概念网络中查看</a></li>
      <li><a href="derivation.html">在范畴推演中定位</a></li>
      <li><a href="glossary.html">术语词典</a></li>
    </ul></div>
  </article>
  <aside class="rail"><div class="rail-inner">
    <div class="rail-title">本页目录</div>{rail}
    <div class="rail-title" style="margin-top:1.4rem">所属章节</div>{ch_links}
  </div></aside>
</div>
</div>"""
    open(os.path.join(OUT, "concept-%s.html" % slug), "w", encoding="utf-8").write(
        shell("%s（%s）" % (cn, de), body, active="network.html", desc=short))


# ----------------------------------------------------------------------------
# 首页
# ----------------------------------------------------------------------------
def build_home():
    cameo = open(os.path.join(CONTENT, "cameo.svg"), encoding="utf-8").read()
    # 体系树
    tree = []
    for part in PARTS:
        chs = [c for c in CHAPTERS if c["part"] == part["num"]]
        links = "".join('<a href="ch%02d.html"><span>%02d</span>%s</a>' % (c["num"], c["num"], c["title"]) for c in chs)
        tree.append(f"""<div class="tree-part">
  <div class="pno">{['I','II','III','IV','V'][part['num']-1]}</div>
  <div>
    <h3>{part['title']}<em>{part['de']}</em></h3>
    <p>{part['gist']}</p>
    <div class="tree-chapters">{links}</div>
  </div>
</div>""")

    doors = [
        ("存在论", "Die Lehre vom Sein", "§84–§111", "课程 24–47",
         "从无规定性的直接性出发，让范畴在自身矛盾中过渡。",
         ["纯存在 → 纯无 → 生成", "定在、有限与真无限", "量、尺度与量变到质变"], "part2.html"),
        ("本质论", "Die Lehre vom Wesen", "§112–§159", "课程 48–63",
         "范畴不再直接过渡，而在对方中映现自身：反思、矛盾、根据、现象、现实。",
         ["同一、差异、对立、矛盾", "根据与实存", "实体、因果、相互作用"], "part3.html"),
        ("概念论", "Die Lehre vom Begriff", "§160–§244", "课程 64–99",
         "概念是自由的原则：它在判断中分开自己，在推论中接合，在理念中证明自己即实在。",
         ["普遍、特殊、个别", "判断与推论的必然序列", "生命、认识、绝对理念"], "part4.html"),
    ]
    door_html = "".join(f"""<a class="door" href="{u}">
  <div class="door-no">{secs} · {rng}</div>
  <h3>{t}</h3>
  <div class="de">{de}</div>
  <p>{g}</p>
  <ul>{''.join('<li>%s</li>' % x for x in items)}</ul>
  <span class="go">进入 · ENTER →</span>
</a>""" for (t, de, secs, rng, g, items, u) in doors)

    idx = "".join(
        '<a href="concept-%s.html">%s<span class="lead"></span><span class="ref">§%s</span></a>'
        % (c[0], c[2], c[5].replace("§", "")) for c in CONCEPTS)

    facts = """
<dl class="facts">
  <div><dt>原 名</dt><dd>Enzyklopädie der philosophischen Wissenschaften im Grundrisse. Erster Teil: Die Wissenschaft der Logik</dd></div>
  <div><dt>体 例</dt><dd>纲要式正文 244 节，附「说明」与编者整理的学生笔记「附释」</dd></div>
  <div><dt>初 版</dt><dd>1817 年（海德堡）；1827 年第二版；1830 年第三版</dd></div>
  <div><dt>中 译</dt><dd>贺麟译，商务印书馆；全书分三篇：存在论、本质论、概念论</dd></div>
  <div><dt>别 名</dt><dd>《小逻辑》为后人为区别于两卷本《大逻辑》而用的称法，非黑格尔原书名</dd></div>
</dl>"""

    body = f"""<div class="wrap">
<section class="hero">
  <div class="hero-grid">
    <div>
      <div class="kicker">Digital Research Institute · Est. {SITE['built']}</div>
      <h1>黑格尔<br>逻辑学研究室<small>A DIGITAL COURSE ON THE ENCYCLOPAEDIA LOGIC</small></h1>
      <p class="hero-de">&ldquo;{SITE['motto']}&rdquo; — {SITE['motto_zh']}</p>
      <p class="hero-lede">这是一门从零开始、逐范畴推进的《小逻辑》课程，只读文本本身。全书 <strong>112 讲</strong>
      按原著三部分展开：存在论从最贫乏的「纯存在」起步，本质论进入反思的中介，概念论达到自我规定的自由。
      每一讲都回到<strong>原著节号</strong>，把「为什么必须过渡」讲清楚。</p>
      <div class="hero-actions">
        <a class="btn btn--red" href="ch01.html">从第一章开始 <span class="arw">→</span></a>
        <a class="btn" href="being-nothing-becoming.html">先读精读：有—无—生成</a>
      </div>
    </div>
    <div class="plate reveal">
      <div class="plate-inner">
        <div class="plate-name">G. W. F. Hegel</div>
        {{CAMEO}}
        <div class="plate-years">MDCCLXX — MDCCCXXXI</div>
        <div class="plate-cap">格奥尔格·威廉·弗里德里希·黑格尔<br>1770 年斯图加特 — 1831 年柏林<br><span style="font-size:.62rem;color:var(--ink-4)">侧面剪影示意，非写实肖像</span></div>
      </div>
    </div>
  </div>
</section>

<section class="sec">
  <div class="editorial reveal">
    <div class="note-col">编者按<br><span style="letter-spacing:.06em;color:var(--ink-4);font-family:var(--serif);font-size:.76rem">EDITOR'S NOTE</span></div>
    <div>
      <p>《小逻辑》是《哲学全书纲要》的第一部分，一部用来配合讲课的纲要：正文常常只有两三句话，真正的论证在「说明」与「附释」里。它的难，不在于术语生僻，而在于每一个规定都从上一个规定的失败中长出来。读懂它的标志，是能够自己说出「为什么不能再停在这里」。</p>
      <p>因此本站不按「概念词典」的方式编写。每一讲都先还原问题，再逐句拆开原文的推演，然后指出这个范畴的限度，以及限度如何逼出下一个范畴。存在论、本质论、概念论在这里是一条路的三段，并非三个并列的知识板块。</p>
      <div class="note" style="margin-top:1.2rem"><div class="note-h">阅读提醒</div>
      <p>《小逻辑》（1817/1827/1830，244 节）与《大逻辑》（1812–1816，两卷）不是同一部书。前者是纲要，后者是展开的论证。本站以《小逻辑》为骨架，必要时注明引用《大逻辑》之处，绝不混用。</p></div>
      {facts}
    </div>
  </div>
</section>

<section class="sec">
  <div class="sec-head"><h2><span class="no">I · STRUCTURE</span>全书结构总览</h2><a href="course.html">全部 112 讲 →</a></div>
  <div class="tree">{''.join(tree)}</div>
</section>

<section class="sec">
  <div class="sec-head"><h2><span class="no">II · THREE PORTALS</span>三个主要入口</h2><a href="atlas.html">全景图 →</a></div>
  <div class="doors">{door_html}</div>
</section>

<section class="band">
  <div class="band-in">
    <h2>第一步为什么是「纯存在」</h2>
    <p class="sub">全书最著名、也最容易被当成文字游戏的一次推演</p>
    <div class="chain">
      <span class="node">纯存在<em>das reine Sein</em></span>
      <span class="arrow">→</span>
      <span class="node">纯无<em>das Nichts</em></span>
      <span class="arrow">→</span>
      <span class="node">生成<em>das Werden</em></span>
      <span class="arrow">→</span>
      <span class="node">定在<em>das Dasein</em></span>
    </div>
    <p class="why">纯存在是抽掉一切规定之后剩下的纯思。它除「是」之外说不出任何内容；而「说不出任何内容」正是无。二者的区别只剩指谓上的区别，于是思想被迫进入第三个东西：一个从有到无、从无到有的运动。这就是生成。</p>
    <p style="margin-top:1rem"><a class="btn" href="being-nothing-becoming.html">读完整精读（六步推演 + 五种反驳）</a></p>
  </div>
</section>

<section class="sec">
  <div class="sec-head"><h2><span class="no">III · CONCEPTS</span>核心概念</h2><a href="network.html">概念网络 →</a></div>
  <div class="idx">{idx}</div>
</section>

<section class="sec" style="padding-bottom:3rem">
  <div class="sec-head"><h2><span class="no">IV · HOW TO READ</span>如何使用这座研究室</h2></div>
  <div class="editorial">
    <div class="note-col">四种读法<br><span style="letter-spacing:.06em;color:var(--ink-4);font-family:var(--serif);font-size:.76rem">WAYS IN</span></div>
    <div class="two">
      <p><strong>一、顺序读。</strong>从第一章到第十四章，按课程编号推进。每章先读「本章导读」，再逐节读原文与推演，最后看「学术争议」。</p>
      <p><strong>二、按图读。</strong>先看<a href="atlas.html">全景图</a>建立骨架，再用<a href="derivation.html">范畴推演图</a>沿着箭头读每一步的「为什么」。</p>
      <p><strong>三、按概念读。</strong>从<a href="network.html">概念网络</a>或<a href="glossary.html">术语词典</a>进入，遇到不懂的术语就查德文原词与节号。</p>
      <p><strong>四、对照读。</strong>用<a href="compare.html">概念对照表</a>看黑格尔与康德、亚里士多德、马克思的分歧究竟落在哪个命题上。</p>
    </div>
  </div>
</section>
</div>"""

    body = body.replace("{CAMEO}", cameo)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        shell("黑格尔逻辑学研究室", body, active="index.html",
              desc="以《小逻辑》为底本的 112 讲系统课程：存在论、本质论、概念论的逐范畴推演，附原著节号、概念专题与术语词典。"))


# ----------------------------------------------------------------------------
# 全景图
# ----------------------------------------------------------------------------
ATLAS = [
    ("存在论", "Die Lehre vom Sein", "§84–§111", 2, [
        ("质", "Qualität", "§86–§98", 4, "第 4–5 章", [
            ("存在（Sein）", "§86–§88", 4, 25),
            ("定在（Dasein）", "§89–§95", 5, 30),
            ("自为存在（Fürsichsein）", "§96–§98", 5, 36),
        ]),
        ("量", "Quantität", "§99–§106", 6, "第 6 章", [
            ("纯量", "§99–§100", 6, 40),
            ("定量", "§101–§105", 6, 43),
            ("程度", "§103–§105", 6, 44),
        ]),
        ("尺度", "Maß", "§107–§111", 6, "第 6 章", [
            ("尺度的特殊化", "§108", 6, 45),
            ("无尺度", "§109", 6, 46),
            ("尺度节点与过渡", "§110–§111", 6, 47),
        ]),
    ]),
    ("本质论", "Die Lehre vom Wesen", "§112–§159", 3, [
        ("本质自身", "Das Wesen als Reflexion in ihm selbst", "§115–§130", 7, "第 7–8 章", [
            ("反思规定：同一·差异·矛盾", "§115–§120", 7, 51),
            ("根据", "§121", 7, 53),
            ("实存", "§122–§124", 8, 54),
            ("物", "§125–§130", 8, 55),
        ]),
        ("现象", "Die Erscheinung", "§131–§141", 8, "第 8 章", [
            ("现象界", "§131–§132", 8, 55),
            ("内容与形式", "§133–§134", 8, 57),
            ("关系：全体与部分·力·内外", "§135–§141", 8, 56),
        ]),
        ("现实", "Die Wirklichkeit", "§142–§159", 8, "第 8 章", [
            ("可能性与现实性", "§143–§146", 8, 59),
            ("必然性", "§147–§149", 8, 60),
            ("实体", "§150–§152", 8, 61),
            ("因果", "§153–§154", 8, 62),
            ("相互作用", "§155–§159", 8, 63),
        ]),
    ]),
    ("概念论", "Die Lehre vom Begriff", "§160–§244", 4, [
        ("主观概念", "Der subjektive Begriff", "§163–§193", 9, "第 9–10 章", [
            ("概念本身", "§163–§165", 9, 66),
            ("判断", "§166–§180", 10, 74),
            ("推论", "§181–§193", 10, 79),
        ]),
        ("客观性", "Die Objektivität", "§194–§212", 11, "第 11 章", [
            ("机械性", "§195–§199", 11, 84),
            ("化学性", "§200–§203", 11, 86),
            ("目的论", "§204–§212", 11, 88),
        ]),
        ("理念", "Die Idee", "§213–§244", 12, "第 12 章", [
            ("生命", "§216–§222", 12, 93),
            ("认识", "§223–§235", 12, 94),
            ("绝对理念", "§236–§244", 12, 98),
        ]),
    ]),
]


def build_atlas():
    cols = []
    for (t, de, secs, part, subs) in ATLAS:
        sub_html = []
        for (st, sde, ssecs, ch, clabel, items) in subs:
            lis = "".join(
                '<li><a href="ch%02d.html#t%d">%s</a> <span class="as">%s</span></li>' % (t[2], t[3], t[0], t[1])
                for t in items)
            sub_html.append(f"""<div class="atlas-sec">
  <h4>{st}<span>{sde}</span></h4>
  <ul>{lis}</ul>
  <div style="margin-top:.3rem"><a href="ch{ch:02d}.html" style="font-size:.72rem">{clabel} · {ssecs} →</a></div>
</div>""")
        cols.append(f"""<div class="atlas-part">
  <h3>{t}<em>{de}</em></h3>
  <p>{secs} · 课程 {PARTS_BY_NUM[part]['range'][0]}–{PARTS_BY_NUM[part]['range'][1]}</p>
  {''.join(sub_html)}
</div>""")
    body = page_head("Atlas · 全景", "黑格尔逻辑学全景图",
                     "《小逻辑》的范畴不是并列的目录，而是一条推演的道路。下图按原著的三篇九章展开，点击任一范畴可进入对应章节。",
                     "Die Gliederung der Wissenschaft der Logik")
    body += f"""<div class="wrap" style="padding-bottom:2rem">
<div class="atlas"><div class="atlas-col">{''.join(cols)}</div></div>
<div class="note" style="margin-top:1.5rem"><div class="note-h">读图说明</div>
<p>三个部分是同一件事的三种自我关系：存在论停留在直接性里，范畴彼此过渡；本质论进入中介，范畴在对方中映现；概念论回到自身，范畴在区别中保持同一。图中的节号依据贺麟译本，与德文原版（拉松本／格罗克曼本）的节号一致。</p></div>
<p style="margin-top:1.4rem"><a class="btn" href="derivation.html">看范畴之间的过渡理由 →</a></p>
</div>"""
    open(os.path.join(OUT, "atlas.html"), "w", encoding="utf-8").write(
        shell("逻辑学全景图", body, active="atlas.html"))


# ----------------------------------------------------------------------------
# 推演页
# ----------------------------------------------------------------------------
def build_derivation():
    if STEPS:
        items = []
        for s in STEPS:
            key = " is-key" if s.get("key") else ""
            items.append(f"""<li class="step{key}" data-part="{s['part']}">
  <div class="step-h"><span class="n">{s['no']}</span><h3>{s['cn']}</h3><span class="de">{s['de']}</span><span class="loc">{s['loc']}</span></div>
  <p>{s['what']}</p>
  <details><summary>为什么过渡到「{s['next']}」</summary><div class="body">{s['why']}</div></details>
</li>""")
        steps_html = "".join(items)
    else:
        steps_html = '<li class="step"><p>推演数据尚未载入。</p></li>'
    body = page_head("Derivation · 推演", "范畴推演图",
                     "箭头不解释任何事情。每一步都可以展开，看到黑格尔凭什么说「这里停不住了」。这是全站最该慢读的一页。",
                     "Der Übergang von Kategorie zu Kategorie")
    body += f"""<div class="wrap" style="padding-bottom:2rem">
<div class="deriv-filter">
  <button class="chip is-on" data-filter="all">全部</button>
  <button class="chip" data-filter="2">存在论</button>
  <button class="chip" data-filter="3">本质论</button>
  <button class="chip" data-filter="4">概念论</button>
</div>
<ol class="steps">{steps_html}</ol>
<div class="note" style="margin-top:1.5rem"><div class="note-h">怎么用这一页</div>
<p>先自己回答「为什么」，再展开对照。若你的回答只是「因为黑格尔这么说」，说明还没读懂；若你能指出上一范畴的哪一个规定使它无法自持，才算抓住了推演。所有节号对应贺麟译本。</p></div>
</div>"""
    open(os.path.join(OUT, "derivation.html"), "w", encoding="utf-8").write(
        shell("范畴推演图", body, active="derivation.html"))


# ----------------------------------------------------------------------------
# 概念网络
# ----------------------------------------------------------------------------
NET_POS = {
    "pure-being": (250, 60), "pure-nothing": (420, 60), "becoming": (335, 135),
    "determinate-being": (335, 215), "finite-and-infinite": (145, 300), "true-infinity": (145, 385),
    "quality-and-quantity": (335, 300), "measure": (500, 380),
    "essence-and-appearance": (660, 215), "identity-and-difference": (660, 300),
    "opposition-and-contradiction": (660, 385), "ground": (660, 470),
    "actuality": (830, 385), "possibility-and-necessity": (830, 470),
    "substance-and-causality": (830, 555),
    "concept": (335, 470), "universal-particular-singular": (335, 555),
    "judgment-and-syllogism": (500, 555), "mechanism-and-chemistry": (660, 640),
    "teleology": (830, 640), "idea": (500, 720), "absolute-idea": (335, 720),
    "negativity": (145, 215), "sublation": (145, 135), "abstract-and-concrete": (250, 640),
    "determinate-being2": (0, 0),
}


def build_network():
    nodes = []
    for n in NET_NODES:
        x, y = n["xy"]
        cls = "net-node"
        nodes.append(
            f'<g class="{cls}" data-id="{n["id"]}" transform="translate({x},{y})" tabindex="0" role="button" aria-label="{n["cn"]}：{n["de"]}">'
            f'<circle class="hit" r="34"/><circle class="dot" r="7"/>'
            f'<text y="27">{n["short"]}</text></g>')
    edges = []
    for (a, b, lab) in NET_EDGES:
        pa = next((n["xy"] for n in NET_NODES if n["id"] == a), None)
        pb = next((n["xy"] for n in NET_NODES if n["id"] == b), None)
        if not pa or not pb:
            continue
        mx, my = (pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2
        edges.append(f'<line class="net-edge" data-edge="{a}|{b}" x1="{pa[0]}" y1="{pa[1]}" x2="{pb[0]}" y2="{pb[1]}"/>')

    data = {"nodes": [{"id": n["id"], "cn": n["cn"], "de": n["de"], "def": n["desc"],
                       "loc": n["loc"], "url": "concept-%s.html" % n["id"]} for n in NET_NODES],
            "edges": [list(e) for e in NET_EDGES]}
    body = page_head("Network · 网络", "概念关系网络",
                     "存在与无、有限与无限、本质与现象、同一与差异、普遍与特殊——概念之间的关系本身就是论证。点击节点查看定义、原著位置与相关章节。",
                     "Das Netz der Bestimmungen")
    body += f"""<div class="wrap" style="padding-bottom:2rem">
<div class="net-shell">
  <p class="net-hint">左右滑动查看全图 · 点击节点查看释义</p>
  <div class="net-canvas">
    <svg id="net" viewBox="0 0 960 800" aria-label="概念关系网络图">
      <g>{''.join(edges)}</g>
      <g>{''.join(nodes)}</g>
    </svg>
  </div>
  <div class="net-panel" id="netPanel"></div>
</div>
<div class="note" style="margin-top:1.4rem"><div class="note-h">图例</div>
<p>连线标出概念之间的主要关系：→ 表示「过渡到」，⇢ 表示「映现于」，⊂ 表示「环节／包含」。这张图不是全集，只收 25 个关键节点；每条线都可以在对应章节找到论证。</p></div>
<script>window.NET_DATA = {json.dumps(data, ensure_ascii=False)};</script>
</div>"""
    open(os.path.join(OUT, "network.html"), "w", encoding="utf-8").write(
        shell("概念关系网络", body, active="network.html"))


# ----------------------------------------------------------------------------
# 对照
# ----------------------------------------------------------------------------
def build_compare():
    head = "".join("<th>%s</th>" % c[0] for c in CMP_COLS)
    rows = []
    for r in CMP_ROWS:
        cells = "".join('<td class="%s">%s</td>' % ("hg" if i == 0 else "", v) for i, v in enumerate(r[1]))
        rows.append('<tr><th scope="row">%s</th>%s</tr>' % (r[0], cells))
    notes = "".join("<p><strong>%s</strong>　%s</p>" % (a, b) for a, b in CMP_NOTES)
    body = page_head("Comparison · 对照", "哲学概念对照",
                     "把同一个问题分别交给黑格尔、康德、亚里士多德与马克思，看分歧究竟落在哪个命题上。表格可左右滑动。",
                     "Hegel im Gespräch")
    body += f"""<div class="wrap" style="padding-bottom:2rem">
<div class="matrix-wrap">
<table class="matrix">
<thead><tr><th>问题</th>{head}</tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>
<div class="editorial" style="margin-top:2rem">
  <div class="note-col">使用说明<br><span style="letter-spacing:.06em;color:var(--ink-4);font-family:var(--serif);font-size:.76rem">HOW TO USE</span></div>
  <div>{notes}</div>
</div>
</div>"""
    open(os.path.join(OUT, "compare.html"), "w", encoding="utf-8").write(
        shell("哲学概念对照", body, active="compare.html"))


# ----------------------------------------------------------------------------
# 词典
# ----------------------------------------------------------------------------
def build_glossary():
    partmap = {"1": "总论", "2": "存在论", "3": "本质论", "4": "概念论"}
    entries = []
    for e in GLOSSARY:
        parts = e.get("part", "1").split()
        pname = " ".join(partmap.get(p, "") for p in parts)
        key = " ".join([e["cn"], e["de"], e.get("en", ""), e.get("desc", "")])
        rel = "".join('<a href="concept-%s.html">%s</a>　' % (s, t) for s, t in e.get("rel", []))
        entries.append(f"""<div class="entry" data-part="{' '.join(parts)}" data-key="{html.escape(key)}">
  <h3>{e['cn']}<span class="de">{e['de']}</span><span class="en">{e.get('en','')}</span></h3>
  <p>{e['desc']}</p>
  <div class="loc">原著 {e.get('loc','')} · {pname}{(' · 相关：' + rel) if rel else ''}</div>
</div>""")
    body = page_head("Glossary · 词典", "哲学术语词典",
                     "德文原词、中文译名、英文对应与原著位置。同一德文词在不同中译本中常有不同译法，条目内注明贺麟译本的处理。",
                     "Terminologie")
    body += f"""<div class="wrap" style="padding-bottom:2rem">
<div class="dict-tools">
  <div class="row">
    <label class="search"><span style="color:var(--bronze);font-family:Georgia,serif">⌕</span>
      <input id="dictSearch" type="search" placeholder="检索中文、德文或英文术语…" aria-label="检索术语"></label>
    <div class="chips">
      <button class="chip is-on" data-part="all">全部</button>
      <button class="chip" data-part="1">总论</button>
      <button class="chip" data-part="2">存在论</button>
      <button class="chip" data-part="3">本质论</button>
      <button class="chip" data-part="4">概念论</button>
    </div>
  </div>
  <div class="dict-count" id="dictCount">收录 {len(GLOSSARY)} 条</div>
</div>
<div class="note" style="margin-bottom:1.2rem"><div class="note-h">译名差异</div>
<p>贺麟译本把 Begriff 译作「总念」，以区别于通常所谓抽象「概念」；Allgemeinheit 译作「共相」；Dasein 译作「限有」，同时用「定在」；Werden 译作「变易」。本站正文统一用「概念／普遍性／定在／生成」，引文保留原译，以便对照纸书。</p></div>
<div id="dict">{''.join(entries)}</div>
</div>"""
    open(os.path.join(OUT, "glossary.html"), "w", encoding="utf-8").write(
        shell("哲学术语词典", body, active="glossary.html"))


# ----------------------------------------------------------------------------
# 精读页 / 关于
# ----------------------------------------------------------------------------
def build_markdown_page(fname, slug, title, kicker, lede, de, active, css_class="prose"):
    p = os.path.join(CONTENT, "pages", fname)
    raw = open(p, encoding="utf-8").read() if os.path.exists(p) else "正文编纂中。\n"
    toc = toc_from_raw(raw)
    rail = "".join('<a href="#%s">%s</a>' % (i, t) for (i, n, t) in toc)
    body_html = md_to_html(raw)
    body = f"""<div class="wrap">
<header class="article-head">
  <div class="crumb"><a href="index.html">首页</a><span>/</span>{kicker}</div>
  <div class="pnum">{kicker}</div>
  <h1>{title}</h1>
  <div class="de">{de}</div>
</header>
<div class="article-body">
  <article class="{css_class}">{body_html}</article>
  <aside class="rail"><div class="rail-inner"><div class="rail-title">本页目录</div>{rail}</div></aside>
</div>
</div>"""
    open(os.path.join(OUT, slug + ".html"), "w", encoding="utf-8").write(
        shell(title, body, active=active, desc=lede))


def build():
    build_home()
    build_course()
    for part in PARTS:
        build_part(part)
    for ch in CHAPTERS:
        build_chapter(ch)
    for c in CONCEPTS:
        build_concept(c)
    build_atlas()
    build_derivation()
    build_network()
    build_compare()
    build_glossary()
    build_markdown_page("being-nothing-becoming.md", "being-nothing-becoming",
                        "从纯存在到生成：一次完整的范畴推演", "Close Reading · 精读",
                        "《小逻辑》§86–§89 的六步推演与五种反驳",
                        "Sein — Nichts — Werden", "derivation.html")
    build_markdown_page("about.md", "about", "编纂说明", "About · 关于",
                        "底本、体例、译本差异与参考文献",
                        "Über dieses Institut", "about.html")
    print("built: %d chapters, %d concepts, %d glossary entries, %d derivation steps"
          % (len(CHAPTERS), len(CONCEPTS), len(GLOSSARY), len(STEPS)))


if __name__ == "__main__":
    build()
