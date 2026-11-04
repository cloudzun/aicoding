# aicoding · 教材网站

《通用 AI Coding 现代软件工程实战》教材的在线阅读站，与配套实验手册站互为姊妹站。

- **本站在线**：<https://www.cloudzun.com/aicoding/>
- **配套手册站**：<https://www.cloudzun.com/mingzhou/>（讲"怎么做"：三篇实操、五套向导、三套素材包）
- **本站定位**：讲"为什么"——八环的门禁与判据、三个典型场景的原理、30 张架构图的读法

## 当前状态：M1（21 单元已上线）

21 个单元、章封面首页、全文检索、7 卷打印视图已全部生成并发布。

**产物入库策略**：`dist/` 由本地构建脚本生成后提交（31 个页面 / 6.8 MB），CI 只做校验 + 扫描 + 发布。
原因是 30 张 mermaid 图需要 Playwright 预渲染成 SVG，放进 CI 反而更慢更脆。
构建脚本在文档仓 `project/aicoding/proto/`：`build-all.ps1`（复制样式 → 生成页面 → 建 Pagefind 索引）。

| 阶段 | 内容 | 状态 |
|---|---|---|
| M0 | 建仓 + Pages 子路径 + 发布链路 | 已完成（2026-11-04） |
| M1 | 21 单元 + 章封面 + 两级侧栏 + 页内目录 + 检索 + 打印 | **已完成（2026-11-04）** |
| M2 | 渲染细化：提示框/角标/内链/导引卡/图注/锚点/打印分卷 | **已完成（随 M1）** |
| M3 | QA 自动化、双站互链、CI 加 QA 步骤 | 待做 |
| M4 | 上线与四步验证 | 待做 |

设计依据见内部文档 `00-建站可行性调研.md`（不在本仓库内，仓库只放站点代码）。

## 部署

- 仓库必须是 **public**：私有发布的 project site 不继承账号级的自定义域名，`/aicoding/` 会失效。
- Pages 来源 = **GitHub Actions**（不是分支部署），`pages.yml` 自带最小权限。
- 站点挂在父站的自定义域名下：`cloudzun.github.io` 设了 `www.cloudzun.com`，本仓作为 project site 自动落在 `www.cloudzun.com/aicoding/`，**不需要 DNS 与 CNAME 文件**。
- 因此 `base` 固定为 `/aicoding`，站内链接一律走 base 变量，禁止写死。

## 本地预览

```bash
node scripts/serve-dist.cjs 4323    # 把 dist 挂到 /aicoding/ 前缀下（直接 serve dist 会让带 BASE 的链接 404）
# → http://127.0.0.1:4323/aicoding/
```

## 重新发布

```powershell
# 1 改教材源文件（通用AI_Coding课程与教材/text/单元*.md）
# 2 重建（在项目文档仓 project/aicoding/proto/）
powershell -File build-all.ps1
# 3 把 proto/dist 同步到本仓 dist，跑扫描，提交推送
python scripts/scan_sensitive.py
git add -A; git commit -m "content: 同步教材"; git push
```

## 纪律

1. 正文不在本仓库编写——正文来自教材源文件，经同步脚本生成镜像；镜像目录不手改。
2. 提交前必过敏感词扫描（`pages.yml` 已内置，命中即失败）。
3. 不把客户实名、现网地址、真实凭据带进仓库。
4. 仓库名是 URL 的一部分（`/aicoding/`），**改名即全站 404**，动手前先确认。
