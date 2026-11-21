# -*- coding: utf-8 -*-
"""内容质量机器校验：标题结构、容器闭合、引文可溯、语言禁令、篇幅。"""
import os, re, json, sys, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")

spec = importlib.util.spec_from_file_location("course", os.path.join(CONTENT, "course.py"))
course = importlib.util.module_from_spec(spec); spec.loader.exec_module(course)

SEC = json.load(open(os.path.join(ROOT, "..", ".work", "_epub", "sections.json"), encoding="utf-8"))
def strip_par(s):
    s = re.sub(r"\[\d+\]", "", s)
    s = re.sub(r"[（(][^）)]{0,40}[）)]", "", s)
    return re.sub(r"〔[^〕]*〕", "", s)

CORPUS = re.sub(r"[\s，。、；：！？“”‘’（）《》〈〉·—…,.;:!?\"\'()\[\]〔〕\-]", "", strip_par("".join(SEC.values())))


def norm(s):
    s = strip_par(s)
    return re.sub(r"[\s，。、；：！？“”‘’（）《》〈〉·—…,.;:!?\"'()\[\]〔〕\-]", "", s)


def check_chapter(ch):
    p = os.path.join(CONTENT, "chapters", "ch%02d.md" % ch["num"])
    problems = []
    if not os.path.exists(p):
        return ["文件缺失"], 0
    raw = open(p, encoding="utf-8").read()
    body = re.sub(r"```.*?```", "", raw, flags=re.S)

    # 1. 容器闭合
    if body.count(":::") % 2 != 0:
        problems.append("容器 ::: 数量为奇数，存在未闭合块")

    # 2. 二级标题
    h2 = re.findall(r"^##\s+(?!#)(.+?)\s*$", body, re.M)
    expected = ["本章导读", "原著位置与文本结构"] + ["%d｜%s" % (n, t) for (n, t, s) in ch["topics"]] + \
               ["本章总结", "学术争议与解释分歧", "思想比较", "现实联系", "延伸阅读"]
    if h2 != expected:
        miss = [x for x in expected if x not in h2]
        extra = [x for x in h2 if x not in expected]
        if miss:
            problems.append("缺少标题: " + " / ".join(miss[:4]))
        if extra:
            problems.append("多余标题: " + " / ".join(extra[:4]))
        if not miss and not extra:
            problems.append("标题顺序不一致")

    # 3. 引文可溯
    quotes = re.findall(r":::src[^\n]*\n(.*?)\n:::", body, re.S)
    bad = []
    for q in quotes:
        q2 = strip_par(q)
        for frag in re.split(r"……|…", q2):
            f = norm(frag)
            if len(f) >= 12 and f not in CORPUS:
                bad.append(frag.strip()[:28])
    if bad:
        problems.append("引文未在原文检索到 %d 处: %s" % (len(bad), " | ".join(bad[:3])))

    # 4. 语言禁令
    if "不是" in body and re.search(r"不是[^。；\n]{0,40}而是", body):
        problems.append("出现「不是……而是」句式 %d 处" % len(re.findall(r"不是[^。；\n]{0,40}而是", body)))
    for banned in ["众所周知", "让我们", "值得注意的是", "总的来说"]:
        if banned in body:
            problems.append("出现禁用词「%s」" % banned)
    if re.search(r"正题.{0,6}反题.{0,6}合题", body):
        problems.append("出现正反合公式")

    # 5. 篇幅与过渡
    cn = len(re.findall(r"[\u4e00-\u9fff]", body))
    if cn < 3500:
        problems.append("篇幅偏短：%d 字" % cn)
    if cn and ch["num"] < 13:
        trans = body.count("**过渡**") + body.count("**过渡：**")
        need = len(ch["topics"])
        if trans < need:
            problems.append("过渡段不足：%d/%d" % (trans, need))
    return problems, cn


def check_concept(c):
    slug, no, cn, de, en, secs, chs, short = c
    p = os.path.join(CONTENT, "concepts", slug + ".md")
    problems = []
    if not os.path.exists(p):
        return ["文件缺失"], 0
    raw = open(p, encoding="utf-8").read()
    h2 = re.findall(r"^##\s+(?!#)(.+?)\s*$", raw, re.M)
    expected = ["概念定义", "原著中的位置", "哲学背景", "逻辑推演", "通俗解释",
                "典型例子", "与其他概念的联系", "常见误解", "学术争议"]
    if h2 != expected:
        miss = [x for x in expected if x not in h2]
        problems.append("标题不符" + ("，缺：" + "/".join(miss) if miss else "（顺序或多余）"))
    if raw.count(":::") % 2:
        problems.append("容器未闭合")
    n = len(re.findall(r"[\u4e00-\u9fff]", raw))
    if n < 800:
        problems.append("篇幅偏短：%d 字" % n)
    if re.search(r"不是[^。；\n]{0,40}而是", raw):
        problems.append("出现「不是……而是」句式")
    return problems, n


def main():
    total_bad = 0
    print("== 章节 ==")
    for ch in course.CHAPTERS:
        probs, n = check_chapter(ch)
        flag = "OK " if not probs else "!! "
        print("%s ch%02d %5d字  %s" % (flag, ch["num"], n, "; ".join(probs)))
        total_bad += len(probs)
    print("\n== 概念专题 ==")
    for c in course.CONCEPTS:
        probs, n = check_concept(c)
        flag = "OK " if not probs else "!! "
        print("%s %-32s %5d字  %s" % (flag, c[0], n, "; ".join(probs)))
        total_bad += len(probs)
    print("\n问题合计：%d" % total_bad)


if __name__ == "__main__":
    main()
