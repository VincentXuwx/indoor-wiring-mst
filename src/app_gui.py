import os
import sys

# 【兼容补丁】动态获取当前运行该代码的 Python 解释器路径
current_env_path = sys.exec_prefix

# 组装寻找 tcl 和 tk 库的路径
tcl_path = os.path.join(current_env_path, 'Library', 'lib', 'tcl8.6')
tk_path = os.path.join(current_env_path, 'Library', 'lib', 'tk8.6')

# 智能判断：如果当前电脑存在这个文件夹（说明是带中文的conda环境），就修补路径
# 如果不存在，就什么都不干，让程序按正常的流程走
if os.path.exists(tcl_path) and os.path.exists(tk_path):
    os.environ['TCL_LIBRARY'] = tcl_path
    os.environ['TK_LIBRARY'] = tk_path

import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches


# ==================== 第1部分：核心算法区域 ====================
class Point:
    def __init__(self, x, y):
        self.x = x;
        self.y = y

    def __eq__(self, other):
        return abs(self.x - other.x) < 1e-9 and abs(self.y - other.y) < 1e-9


class Rect:
    def __init__(self, x1, y1, x2, y2):
        self.x1 = min(x1, x2);
        self.y1 = min(y1, y2)
        self.x2 = max(x1, x2);
        self.y2 = max(y1, y2)

    def contains_point(self, p):
        return self.x1 < p.x < self.x2 and self.y1 < p.y < self.y2

    def intersect_segment(self, p1, p2):
        if self.contains_point(p1) or self.contains_point(p2): return True
        dx = p2.x - p1.x;
        dy = p2.y - p1.y
        if abs(dx) > 1e-9:
            for x_edge in [self.x1, self.x2]:
                t = (x_edge - p1.x) / dx
                if 0 < t < 1 and self.y1 < p1.y + t * dy < self.y2: return True
        if abs(dy) > 1e-9:
            for y_edge in [self.y1, self.y2]:
                t = (y_edge - p1.y) / dy
                if 0 < t < 1 and self.x1 < p1.x + t * dx < self.x2: return True
        return False


def manhattan_distance(p1, p2):
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)


def is_path_legal(p1, p2, doors):
    mid1 = Point(p2.x, p1.y);
    legal1 = True
    for door in doors:
        if door.intersect_segment(p1, mid1) or door.intersect_segment(mid1, p2):
            legal1 = False;
            break
    len1 = manhattan_distance(p1, p2) if legal1 else float('inf')

    mid2 = Point(p1.x, p2.y);
    legal2 = True
    for door in doors:
        if door.intersect_segment(p1, mid2) or door.intersect_segment(mid2, p2):
            legal2 = False;
            break
    len2 = manhattan_distance(p1, p2) if legal2 else float('inf')

    if legal1 or legal2:
        return True, min(len1, len2), [p1, mid1, p2] if len1 <= len2 else [p1, mid2, p2]
    return False, float('inf'), []


def shortest_avoiding_path(p1, p2, doors):
    legal, dist, path = is_path_legal(p1, p2, doors)
    if legal: return dist, 'direct', path

    detour_points = []
    for door in doors:
        for corner in [Point(door.x1, door.y1), Point(door.x1, door.y2), Point(door.x2, door.y1),
                       Point(door.x2, door.y2)]:
            if corner not in detour_points: detour_points.append(corner)

    best_dist = float('inf');
    best_path = []
    for corner in detour_points:
        l1_legal, l1_dist, l1_path = is_path_legal(p1, corner, doors)
        l2_legal, l2_dist, l2_path = is_path_legal(corner, p2, doors)
        if l1_legal and l2_legal and (l1_dist + l2_dist < best_dist):
            best_dist = l1_dist + l2_dist;
            best_path = l1_path[:-1] + l2_path

    return (best_dist, 'detour', best_path) if best_dist != float('inf') else (float('inf'), 'none', [])


def build_graph(points, doors):
    n = len(points);
    edges = []
    for i in range(n):
        for j in range(i + 1, n):
            dist, _, path = shortest_avoiding_path(points[i], points[j], doors)
            if dist != float('inf'): edges.append((i, j, dist, path))
    return edges


class DSU:
    def __init__(self, size):
        self.parent = list(range(size));
        self.rank = [0] * size

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]];
            x = self.parent[x]
        return x

    def union(self, x, y):
        x_root = self.find(x);
        y_root = self.find(y)
        if x_root == y_root: return False
        if self.rank[x_root] < self.rank[y_root]:
            self.parent[x_root] = y_root
        else:
            self.parent[y_root] = x_root
            if self.rank[x_root] == self.rank[y_root]: self.rank[x_root] += 1
        return True


def kruskal_mst(num_nodes, edges):
    edges.sort(key=lambda e: e[2])
    dsu = DSU(num_nodes);
    mst_edges = [];
    total_w = 0.0
    for u, v, w, path in edges:
        if dsu.union(u, v):
            mst_edges.append((u, v, w, path));
            total_w += w
            if len(mst_edges) == num_nodes - 1: break
    return (total_w, mst_edges) if len(mst_edges) == num_nodes - 1 else (None, [])


# ==================== 第2部分：GUI 界面逻辑 ====================
class WiringApp:
    def __init__(self, root):
        self.root = root
        self.root.title("最小生成树应用：室内布线系统（前端界面版）")
        self.root.geometry("900x600")  # 设置窗口大小的宽x高

        # 左侧控制面板（给输入框留位置）
        control_frame = tk.Frame(root, width=250, padx=15, pady=15)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)

        # 1. 插座输入区
        tk.Label(control_frame, text="🔌 插座坐标 (每行一个，x y):", font=("黑体", 11)).pack(anchor="w", pady=(0, 5))
        self.sockets_text = tk.Text(control_frame, height=8, width=25, font=("Consolas", 10))
        self.sockets_text.pack(pady=5)
        # 预设几个坐标方便测试
        self.sockets_text.insert(tk.END, "0 0\n2 5\n8 0\n10 5")

        # 2. 门输入区
        tk.Label(control_frame, text="🚪 门坐标 (每行一个，x1 y1 x2 y2):", font=("黑体", 11)).pack(anchor="w",
                                                                                                 pady=(10, 5))
        self.doors_text = tk.Text(control_frame, height=5, width=25, font=("Consolas", 10))
        self.doors_text.pack(pady=5)
        # 预设一个门挡在中间
        self.doors_text.insert(tk.END, "4 -1 6 3")

        # 3. 运行按钮
        self.calc_btn = tk.Button(control_frame, text="⚡ 开始计算并绘制路径",
                                  command=self.calculate_and_draw,
                                  bg="#4CAF50", fg="white", font=("黑体", 12, "bold"))
        self.calc_btn.pack(pady=20, fill=tk.X)

        # 4. 结果文字展示区
        self.result_label = tk.Label(control_frame, text="等待计算...", fg="#E91E63", justify=tk.LEFT,
                                     font=("黑体", 11))
        self.result_label.pack(anchor="w")

        # 右侧画板区（显示图像的内容）
        self.plot_frame = tk.Frame(root, bg="white", bd=2, relief=tk.GROOVE)
        self.plot_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 初始化matplotlib画布
        self.fig, self.ax = plt.subplots(figsize=(6, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        # 先空着画布提示一下
        self.ax.text(0.5, 0.5, "请在左侧输入数据后点击计算", horizontalalignment='center', verticalalignment='center',
                     color='gray')
        self.ax.axis('off')

    # 当按下计算按钮时，会触发这个函数
    def calculate_and_draw(self):
        points = []
        doors = []

        # -- 尝试读取你在界面输入框里的文字 --
        try:
            # 读取插座数据
            socket_lines = self.sockets_text.get("1.0", tk.END).strip().split('\n')
            for line in socket_lines:
                if line.strip():
                    x, y = map(float, line.split())
                    points.append(Point(x, y))

            # 读取门数据
            door_lines = self.doors_text.get("1.0", tk.END).strip().split('\n')
            for line in door_lines:
                if line.strip():
                    x1, y1, x2, y2 = map(float, line.split())
                    doors.append(Rect(x1, y1, x2, y2))
        except Exception as e:
            messagebox.showerror("输入错误", "数据格式不对！请确保输入数字且用空格隔开。")
            return

        if len(points) < 2:
            messagebox.showwarning("提示", "你需要输入至少两个插座才能连线哦！")
            return

        # -- 调用原有的算法计算连通和最小树 --
        edges = build_graph(points, doors)
        total_len, mst_edges = kruskal_mst(len(points), edges)

        if total_len is None:
            self.result_label.config(text="失败：被门彻底阻挡\n无法全部连通！")
            messagebox.showerror("计算失败", "所有插座无法通过可行路径连通（图不连通），请检查门是否太大阻挡了路径。")
            return

        # -- 更新左侧的计算结果文字 --
        self.result_label.config(text=f"✅ 布线成功！\n\n📌 最小生成树总长:\n{total_len:.2f}")

        # -- 将计算结果画到右侧面板上 --
        self.ax.clear()  # 先擦除旧图片
        self.ax.axis('on')  # 开启坐标轴

        # 1. 涂抹红色半透明矩形代表门
        for door in doors:
            rect = patches.Rectangle((door.x1, door.y1), door.x2 - door.x1, door.y2 - door.y1, color='red', alpha=0.3)
            self.ax.add_patch(rect)

        # 2. 点上蓝色插孔代表插座
        for i, p in enumerate(points):
            self.ax.scatter(p.x, p.y, c='blue', s=80, zorder=5)
            self.ax.text(p.x + 0.2, p.y + 0.2, f"插座{i + 1}", fontsize=10, fontweight='bold', color='darkblue')

        # 3. 按照算好的路径连上绿线
        for u, v, w, path in mst_edges:
            xs = [p.x for p in path]
            ys = [p.y for p in path]
            self.ax.plot(xs, ys, 'green', linewidth=2.5, alpha=0.8)

        # 4. 图表美化
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.ax.set_title("室内最小布线方案（曼哈顿距离）", fontsize=14, fontweight='bold')
        self.ax.set_xlabel("X向坐标")
        self.ax.set_ylabel("Y向坐标")

        self.canvas.draw()  # 刷新画布，将图呈现出来


if __name__ == "__main__":
    # --- 解决 matplotlib 中文字体显示方格的问题 ---
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']  # 适配不同系统的中文字体
    plt.rcParams['axes.unicode_minus'] = False  # 正常显示负号

    # --- 启动 Tkinter 应用 ---
    root = tk.Tk()
    app = WiringApp(root)
    root.mainloop()  # 让窗口持续显示