# 来源与依赖

工作流与模板来自本项目的研究实践整理。`tools/extract_figures.py` 从同一研究项目的 2026-10-04 批量提图脚本整理为通用命令行入口；自动排版规则仍是启发式候选生成，保留其适用范围说明。

## Python 依赖

第三方依赖没有随仓库分发，也不由本仓库的 MIT 许可重新授权。

| 依赖 | 用途 | 官方来源 |
| --- | --- | --- |
| pypdf | PDF 基础核验与首页文字提取 | [官方仓库](https://github.com/py-pdf/pypdf) |
| PyMuPDF | 页面文字位置与渲染 | [官方仓库](https://github.com/pymupdf/PyMuPDF) |
| Pillow | 图片裁剪与保存 | [官方仓库](https://github.com/python-pillow/Pillow) |
| NumPy | 图像像素与留白检测 | [官方仓库](https://github.com/numpy/numpy) |

PyMuPDF／MuPDF 提供 AGPL 和商业许可选项；运行、组合或再分发时应查看其[官方许可说明](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright)。本仓库的 MIT 许可不会替代这些依赖的许可要求。

## 外部工作与文献

复现工具和评测项目仅作为链接与方法参考，具体来源见 [docs/references.md](docs/references.md)。本仓库未复制其实现，也未包含论文全文、原论文插图、数据或权重；相关材料由各自权利人与许可证管理。
