# aicoding · 教材网站

《通用 AI Coding 现代软件工程实战》教材的在线阅读站，与配套实验手册站互为姊妹站。

- **本站在线**：<https://www.cloudzun.com/aicoding/>
- **配套手册站**：<https://www.cloudzun.com/mingzhou/>（讲"怎么做"：三篇实操、五套向导、三套素材包）
- **本站定位**：讲"为什么"——八环的门禁与判据、三个典型场景的原理、30 张架构图的读法

## 当前状态：M0（链路验证）

仓库、Actions 与 Pages 子路径已打通，**正文尚未上线**。`dist/index.html` 是占位页，仅用于验证 `/aicoding/` 可达。

| 阶段 | 内容 | 状态 |
|---|---|---|
| M0 | 建仓 + Pages 子路径 + 发布链路 | **进行中** |
| M1 | Astro 骨架、正文同步、7 章 × 21 单元两级导航 | 待做 |
| M2 | 渲染：提示框/角标引注/跨单元内链/导引卡/图注/锚点/打印 | 待做 |
| M3 | 检索配置、QA 扩展、双站互链 | 待做 |
| M4 | 上线与四步验证 | 待做 |

设计依据见内部文档 `00-建站可行性调研.md`（不在本仓库内，仓库只放站点代码）。

## 部署

- 仓库必须是 **public**：私有发布的 project site 不继承账号级的自定义域名，`/aicoding/` 会失效。
- Pages 来源 = **GitHub Actions**（不是分支部署），`pages.yml` 自带最小权限。
- 站点挂在父站的自定义域名下：`cloudzun.github.io` 设了 `www.cloudzun.com`，本仓作为 project site 自动落在 `www.cloudzun.com/aicoding/`，**不需要 DNS 与 CNAME 文件**。
- 因此 `base` 固定为 `/aicoding`，站内链接一律走 base 变量，禁止写死。

## 本地预览

M0 阶段是纯静态页：

```bash
npx serve dist          # 或任意静态服务器
```

M1 起改为：

```bash
npm ci && npm run build
node scripts/serve-dist.cjs 4321    # 把 dist 挂到 /aicoding/ 前缀下，避免带 BASE 的链接 404
```

## 纪律

1. 正文不在本仓库编写——正文来自教材源文件，经同步脚本生成镜像；镜像目录不手改。
2. 提交前必过敏感词扫描（`pages.yml` 已内置，命中即失败）。
3. 不把客户实名、现网地址、真实凭据带进仓库。
4. 仓库名是 URL 的一部分（`/aicoding/`），**改名即全站 404**，动手前先确认。
