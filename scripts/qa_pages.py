"""教材站逐页 QA：local / online / browser 三种模式，一页不落。

用法：
  python scripts/qa_pages.py local                       # 直接读 dist 文件（秒级，无需依赖）
  python scripts/qa_pages.py                             # 线上 HTTP 冒烟
  python scripts/qa_pages.py browser http://127.0.0.1:4323/aicoding   # 本地真浏览器
  python scripts/qa_pages.py browser                     # 线上真浏览器

设计要点：
1. **路由从 dist 自动发现**，不手写列表——手册站曾因路由手写漏测过一页。
2. local 只回答"文件在不在、占位符替换了没、结构与交叉引用对不对"；
   BASE 写错、资源 404、控制台报错、搜索点不进去只有 browser 模式抓得出来。
3. 教材特有的三类检查：角标↔延伸阅读双向闭合、图注指向的 SVG 真实存在、
   打印页一页拼多个单元时的重复 id。
"""
import re
import sys
import pathlib
import urllib.request

MODE = sys.argv[1] if len(sys.argv) > 1 else "online"
DIST = pathlib.Path("dist")
HOST = "https://www.cloudzun.com/aicoding"
BASE = (sys.argv[2] if len(sys.argv) > 2 else HOST).rstrip("/")

# 章 → 单元数（用于打印页 h1 计数；从 dist 里反推，不写死）
CHAPTER_UNITS = {}


def discover():
    """从 dist 反推全部路由与每章单元数。"""
    routes = []
    for p in sorted(DIST.rglob("index.html")):
        rel = p.parent.relative_to(DIST).as_posix()
        route = "/" if rel == "." else f"/{rel}/"
        routes.append(route)
    # 排序：首页 → 单元 → 检索 → 打印
    def key(r):
        if r == "/":
            return (0, r)
        if r.startswith("/units/"):
            return (1, r)
        if r == "/search/":
            return (2, r)
        return (3, r)
    routes.sort(key=key)
    for p in DIST.glob("units/*/index.html"):
        no = p.parent.name.split("-")[0]
        CHAPTER_UNITS[no] = CHAPTER_UNITS.get(no, 0) + 1
    return routes


def read_local(route):
    p = DIST / route.strip("/") / "index.html" if route != "/" else DIST / "index.html"
    if not p.exists():
        return None, ""
    return 200, p.read_text(encoding="utf-8", errors="ignore")


def read_remote(route):
    try:
        with urllib.request.urlopen(BASE + route, timeout=25) as r:
            return r.status, r.read().decode("utf-8", "ignore")
    except Exception as e:
        return None, str(e)


def structural_issues(route, html):
    """与模式无关的静态检查：占位符、缺图、h1、侧栏、锚点、角标、图表。"""
    issues = []

    if "@@" in html:
        left = set(re.findall(r"@@[\w.-]+@@", html))
        issues.append(f"占位符未替换 {sorted(left)[:3]}")
    if "[缺图" in html:
        issues.append("存在缺图标记")

    h1 = len(re.findall(r"<h1[ >]", html))
    if route.startswith("/print/ch-"):
        ch = route.split("/print/ch-")[1].split("/")[0]
        want = CHAPTER_UNITS.get(ch, 0)
        if h1 != want:
            issues.append(f"打印页 h1={h1}（该章 {want} 个单元）")
        ids = re.findall(r'\sid="([^"]+)"', html)
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            issues.append(f"重复 id {sorted(dup)[:3]}")
    elif h1 != 1:
        issues.append(f"h1 数量={h1}")

    # 侧栏：7 章组 / 21 单元 / 恰 1 个 active
    if route.startswith("/units/"):
        groups = html.count('class="nav-group"')
        items = len(re.findall(r'class="nav-item c\d', html))
        active = len(re.findall(r'class="nav-item c\d active"', html))
        if groups != 7:
            issues.append(f"侧栏章组={groups}（应 7）")
        if items != 21:
            issues.append(f"侧栏单元={items}（应 21）")
        if active != 1:
            issues.append(f"侧栏 active={active}（应 1）")
        # 页内目录锚点必须都能在本页找到
        toc_targets = re.findall(r'<li class="lv\d"><a href="#([^"]+)"', html)
        page_ids = set(re.findall(r'\sid="([^"]+)"', html))
        missing = [t for t in toc_targets if t not in page_ids]
        if missing:
            issues.append(f"目录锚点落空 {missing[:3]}")

        # 角标 ↔ 延伸阅读 双向闭合
        cites = set(re.findall(r'<sup class="cite"><a href="#[^"]*?ref-(\d+)">', html))
        refs = set(re.findall(r'<li id="[^"]*?ref-(\d+)">', html))
        if cites - refs:
            issues.append(f"角标无对应条目 {sorted(cites - refs)[:4]}")
        if refs - cites:
            issues.append(f"条目无人引用 {sorted(refs - cites)[:4]}")

        # 图：每张图要有 svg / figcaption，图注链接指向的 SVG 文件要真实存在
        figs = re.findall(r'<figure class="fig" id="[^"]*fig-(\d+-\d+)"', html)
        svgs = len(re.findall(r'<figure class="fig"[^>]*>\s*<div class="fig-scroll">\s*<svg', html))
        caps = html.count("<figcaption")
        if len(figs) != svgs:
            issues.append(f"图 {len(figs)} 张，只有 {svgs} 张渲染出 SVG")
        if len(figs) != caps:
            issues.append(f"图 {len(figs)} 张，图注 {caps} 条")
        for fid in figs:
            if not (DIST / "figs" / f"fig-{fid}.svg").exists():
                issues.append(f"图注链接缺文件 fig-{fid}.svg")
                break

        # 样式表必须存在
        for css in re.findall(r'href="/aicoding/assets/([\w.-]+\.css)"', html):
            if not (DIST / "assets" / css).exists():
                issues.append(f"缺样式 {css}")
                break

    return issues


def smoke():
    routes = discover()
    rows, bad = [], 0
    for route in routes:
        if MODE == "local":
            code, html = read_local(route)
        else:
            code, html = read_remote(route)
        issues = []
        if code != 200:
            issues.append(f"HTTP {code}")
        else:
            issues += structural_issues(route, html)
        rows.append((route, code, "OK" if not issues else "; ".join(issues)))
        bad += 1 if issues else 0
    if MODE == "local" and not (DIST / "pagefind").is_dir():
        rows.append(("/pagefind/", "-", "缺 Pagefind 索引（先跑 build-all.ps1）"))
        bad += 1
    return routes, rows, bad


def browser():
    from playwright.sync_api import sync_playwright

    routes = discover()
    rows, bad = [], 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        for route in routes:
            page = ctx.new_page()
            errs, http_bad = [], []
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
            page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
            page.on("response", lambda r: http_bad.append(f"{r.status} {r.url}") if r.status >= 400 else None)
            issues = []
            try:
                page.goto(BASE + route, wait_until="load", timeout=30000)
                page.wait_for_timeout(500)
            except Exception as e:
                rows.append((route, "-", f"打不开: {str(e)[:80]}"))
                bad += 1
                page.close()
                continue

            if errs:
                issues.append(f"控制台 {len(errs)} 错: {errs[0][:60]}")
            if http_bad:
                issues.append(f"资源错: {http_bad[0][:60]}")

            html = page.content()
            issues += structural_issues(route, html)

            # 桌面下不应出现横向溢出（宽表宽图各自在容器里滚）
            overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1")
            if overflow:
                issues.append("页面横向溢出")

            # 图必须真的画出来（有尺寸），不是 0×0
            if route.startswith("/units/"):
                boxes = page.evaluate(
                    "() => [...document.querySelectorAll('figure.fig svg')].map(s => {"
                    " const r = s.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })"
                )
                zero = [b for b in boxes if b[0] < 40 or b[1] < 40]
                if zero:
                    issues.append(f"图未渲染出尺寸 {zero[:2]}")

            if route == "/search/":
                box = page.locator(".pagefind-ui__search-input")
                if box.count() == 0:
                    issues.append("找不到搜索框")
                else:
                    page.wait_for_timeout(900)
                    for attempt in range(2):
                        box.first.fill("拒答")
                        try:
                            page.wait_for_selector(".pagefind-ui__result", timeout=6000)
                            break
                        except Exception:
                            page.evaluate(
                                "() => { const i = document.querySelector('.pagefind-ui__search-input');"
                                " if (i) { i.value = '拒答'; i.dispatchEvent(new Event('input', { bubbles: true })); } }"
                            )
                            page.wait_for_timeout(2500)
                    links = page.locator(".pagefind-ui__result-link")
                    if links.count() == 0:
                        page.wait_for_timeout(2500)
                    if links.count() == 0:
                        issues.append("搜索结果为空")
                    else:
                        href = links.first.get_attribute("href") or ""
                        if "/aicoding/" not in href:
                            issues.append(f"结果链接不在 BASE 下: {href[:60]}")

            rows.append((route, "200", "OK" if not issues else "; ".join(issues)))
            bad += 1 if issues else 0
            page.close()

        # 移动端：抽首页 + 一个单元页，390 宽不得横向溢出、侧栏应折叠
        mobile = [r for r in routes if r in ("/", "/units/5-2/", "/units/7-1/")]
        mctx = b.new_context(viewport={"width": 390, "height": 844},
                             device_scale_factor=2, is_mobile=True, has_touch=True)
        for route in mobile:
            page = mctx.new_page()
            try:
                page.goto(BASE + route, wait_until="load", timeout=30000)
                page.wait_for_timeout(400)
            except Exception as e:
                rows.append((f"[移动] {route}", "-", f"打不开: {str(e)[:60]}"))
                bad += 1
                page.close()
                continue
            issues = []
            if page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1"):
                issues.append("390 宽横向溢出")
            if route.startswith("/units/"):
                if page.locator(".m-nav>summary").count() == 0:
                    issues.append("缺移动端折叠目录")
                elif page.evaluate("() => getComputedStyle(document.querySelector('.m-nav>summary')).display") == "none":
                    issues.append("移动端目录未显示")
            rows.append((f"[移动] {route}", "200", "OK" if not issues else "; ".join(issues)))
            bad += 1 if issues else 0
            page.close()
        mctx.close()
        b.close()
    return rows, bad


def main():
    if MODE == "browser":
        rows, bad = browser()
    else:
        _, rows, bad = smoke()
    label = {"local": "本地文件", "online": "线上 HTTP", "browser": "真浏览器"}.get(MODE, MODE)
    print(f"模式：{label} ｜ 基址：{BASE}")
    print(f"{'路由':<22}{'状态':<6}结果")
    for r, c, s in rows:
        print(f"{r:<22}{str(c):<6}{s}")
    print(f"\n共 {len(rows)} 页，异常 {bad} 页")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
