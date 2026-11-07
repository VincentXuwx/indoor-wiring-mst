# -*- coding: utf-8 -*-
"""
生成 README 中的结果示意图（修复原图中文字体缺失导致的方块问题）。

用法：
    python demo/render_demo.py [数据文件] [输出图片]

默认读取 data/demo_two_doors.txt，输出 docs/images/result-demo.png。
"""
import os
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

from indoor_wiring import read_input_from_file, build_graph, kruskal_mst  # noqa: E402


def setup_chinese_font():
    """挑选一个可用的中文字体，避免绘图出现方块（tofu）。"""
    candidates = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Source Han Sans SC",
                  "PingFang SC", "WenQuanYi Micro Hei", "SimSun"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name]
            plt.rcParams["axes.unicode_minus"] = False
            return name
    plt.rcParams["axes.unicode_minus"] = False
    return None


def main():
    data = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "demo_two_doors.txt")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "docs", "images", "result-demo.png")

    font = setup_chinese_font()
    print("使用字体:", font or "（未找到中文字体，可能出现方块）")

    points, doors = read_input_from_file(data)
    edges = build_graph(points, doors)
    total, mst_edges = kruskal_mst(len(points), edges)
    if total is None:
        raise SystemExit("图不连通，请检查输入数据")

    fig, ax = plt.subplots(figsize=(9, 6.2), dpi=160)

    for door in doors:
        ax.add_patch(patches.Rectangle(
            (door.x1, door.y1), door.x2 - door.x1, door.y2 - door.y1,
            linewidth=1.4, edgecolor="#d64545", facecolor="#f8b4b4",
            alpha=0.55, linestyle="--", zorder=2))

    for u, v, w, path in mst_edges:
        xs = [p.x for p in path]
        ys = [p.y for p in path]
        ax.plot(xs, ys, color="#1f6f3f", linewidth=4.5, alpha=0.18,
                solid_capstyle="round", zorder=3)
        ax.plot(xs, ys, color="#2e9c5a", linewidth=2.2,
                solid_capstyle="round", zorder=4)

    for i, p in enumerate(points):
        ax.scatter(p.x, p.y, s=170, c="#1f77b4", edgecolors="white",
                   linewidths=1.6, zorder=6)
        ax.annotate(str(i + 1), (p.x, p.y), textcoords="offset points",
                    xytext=(12, 8), fontsize=13, fontweight="bold", color="#12395c")

    ax.set_aspect("equal", adjustable="datalim")
    ax.margins(0.12)
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.set_title(f"室内布线方案（最短电线总长 {total:.2f}）", fontsize=15, pad=12)
    ax.set_xlabel("X 坐标")
    ax.set_ylabel("Y 坐标")

    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor="#1f77b4",
               markeredgecolor="white", markersize=11, label="插座（节点）"),
        patches.Patch(facecolor="#f8b4b4", edgecolor="#d64545", linestyle="--", label="门（障碍物）"),
        Line2D([0], [0], color="#2e9c5a", linewidth=2.4, label="布线路径（MST 边）"),
    ]
    ax.legend(handles=handles, loc="upper left", framealpha=0.95)

    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    print(f"已保存 {out}；插座 {len(points)} 个，门 {len(doors)} 个，最短总长 {total:.2f}")


if __name__ == "__main__":
    main()
