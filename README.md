# 黑格尔逻辑学研究室

以《小逻辑》（G. W. F. Hegel, *Enzyklopädie der philosophischen Wissenschaften im Grundrisse*, Erster Teil）为底本的中文系统课程网站。手机端优先，纯静态，无后端、无账号、无追踪。

## 规模

- 五部分 · 十四章 · 一百一十二讲（课程编号 1–112）
- 二十五个概念专题（每个含定义、原著位置、背景、推演、通俗解释、例子、关联、误解、争议）
- 一百零六条哲学术语（德文／英文／中文对照，标原著节号）
- 四十二步范畴推演图，每一步给出「为什么不能再停在这里」
- 正文约十七万字

## 打开方式

直接双击 `index.html` 即可，无需服务器。若要发布，把整个目录上传到任意静态托管（对象存储、GitHub Pages、Nginx 均可）。

## 重新构建

```bash
pip install markdown      # 唯一依赖
python build.py           # 生成全部 HTML
python tools/qa.py        # 内容校验：标题结构、容器闭合、引文可溯、禁用句式、篇幅
python tools/sec.py 86 89 # 查阅《小逻辑》§86–§89 原文（用于核对引文）
```

## 目录

```
index.html            首页（视觉系统 + 结构总览 + 三个入口）
course.html           课程总览（五部分 / 十四章 / 112 讲）
part1–5.html          各篇导览
ch01–14.html          十四章正文
concept-*.html        25 个概念专题
atlas.html            逻辑学全景图（每个范畴可点进对应讲次）
derivation.html       范畴推演图（42 步，可展开「为什么」）
network.html          概念关系网络（25 节点，可交互）
compare.html          黑格尔 / 康德 / 亚里士多德 / 马克思 对照表
glossary.html         术语词典（检索 + 分部筛选）
being-nothing-becoming.html  精读：从纯存在到生成（六步推演 + 五种反驳）
about.html            编纂说明、译本差异、参考文献

content/
  course.py           课程结构元数据（篇、章、讲、概念）
  chapters/*.md       各章正文（Markdown）
  concepts/*.md       概念专题
  pages/*.md          精读与关于页
  derivation.py       推演步骤数据
  network.py          概念网络节点与边
  compare.py          对照表数据
  glossary.py         术语数据
  cameo.svg           首页侧面剪影（手绘 SVG）
  SPEC.md             撰稿规范（术语表、结构、语言禁令）

assets/css/style.css  视觉系统（19 世纪研究院风格）
assets/js/site.js     交互（目录、筛选、网络图、进度）
tools/sec.py          原文分节检索
tools/qa.py           机器校验
```

## 内容原则

1. 引文一律逐字取自贺麟译本，标节号，长度控制在必要范围；《大逻辑》单独标明，不与《小逻辑》混引。
2. 区分《小逻辑》（244 节纲要）与《大逻辑》（两卷本论证）。
3. 不使用「正—反—合」公式解释辩证法；按 §79–§82 的「知性—否定的理性—肯定的理性」三环节讲。
4. 学界有争议处标出至少两种读法，不把一家之言当作黑格尔原意。
5. 不设考试、答题、打卡、积分、排名与社交功能。

## 已知限制

- 首页肖像为手绘侧面剪影示意，非写实摹写。
- 术语词典与概念专题覆盖核心范畴，未穷尽《小逻辑》全部 244 节。
- 引文核对基于贺麟译本电子文本，与纸书页码不完全对应；正文以节号为准。

详细说明见 `about.html`。
