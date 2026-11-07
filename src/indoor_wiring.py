import math
import sys

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class Point:
    # 平面坐标
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"({self.x:.2f}, {self.y:.2f})"

    def __eq__(self, other):
        return abs(self.x - other.x) < 1e-9 and abs(self.y - other.y) < 1e-9


class Rect:
    # 矩形（门）
    def __init__(self, x1, y1, x2, y2):
        self.x1 = min(x1,x2)
        self.y1 = min(y1,y2)
        self.x2 = max(x1,x2)
        self.y2 = max(y1,y2)

    def contains_point(self, p):
        return self.x1 < p.x < self.x2 and self.y1 < p.y < self.y2

    def intersect_segment(self, p1, p2):
        """
        判断p1-p2是否与矩形相交（包括边界）
        """
        # 如果线段两个端点有一个在矩形内，则必相交
        if self.contains_point(p1) or self.contains_point(p2):
            return True

        dx = p2.x - p1.x
        dy = p2.y - p1.y

        # 检查门与四条边的交点
        # 左边界
        if abs(dx) > 1e-9:
            t_left = (self.x1 - p1.x) / dx
            if 0 < t_left < 1:
                y = p1.y +  t_left * dy
                if self.y1 < y < self.y2:
                    return True
        # 右边界
        if abs(dx) > 1e-9:
            t_right = (self.x2 - p1.x) / dx
            if 0 < t_right < 1:
                y = p1.y + t_right * dy
                if self.y1 < y < self.y2:
                    return True
        # 下边界
        if abs(dy) > 1e-9:
            t_bottom = (self.y1 - p1.y) / dy
            if 0 < t_bottom < 1:
                x = p1.x + t_bottom * dx
                if self.x1 < x < self.x2:
                    return True
        # 上边界
        if abs(dy) > 1e-9:
            t_top = (self.y2 - p1.y) / dy
            if 0 < t_top < 1:
                x = p1.x + t_top * dx
                if self.x1 < x < self.x2:
                    return True

        return False

    @staticmethod
    def _segments_intersect(p1, p2, p3, p4):
        """判断两条线段是否严格相交（交点不是端点）"""
        def cross(o, a, b):
            return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)

        c1 = cross(p1, p2, p3)
        c2 = cross(p1, p2, p4)
        c3 = cross(p3, p4, p1)
        c4 = cross(p3, p4, p2)

        return (c1 * c2 < 0) and (c3 * c4 < 0)


def manhattan_distance(p1, p2):
    # 曼哈顿距离
    return abs(p1.x - p2.x) + abs(p1.y - p2.y)


def make_l_path(p1, mid, p2):
    # 组装折线路径，并去掉与端点重合的拐点（两点同 x 或同 y 时会出现重复点）
    points = [p1]
    if mid != p1 and mid != p2:
        points.append(mid)
    points.append(p2)
    return points


def is_path_legal(p1, p2, doors):
    """
    检查两种曼哈顿路径是否至少有一条不与门相交
    1：先水平后垂直（p1 -> （p2.x, p1.y） -> p2）
    2：先垂直后水平（p1 -> （p1.x, p2.y） -> p2）
    返回
    """
    # 路径1
    mid1 = Point(p2.x, p1.y)
    legal1 = True
    for door in doors:
        if door.intersect_segment(p1, mid1) or door.intersect_segment(mid1, p2):
            legal1 = False
            break
    len1 = manhattan_distance(p1, p2) if legal1 else float('inf')

    # 路径2
    mid2 = Point(p1.x, p2.y)
    legal2 = True
    for door in doors:
        if door.intersect_segment(p1, mid2) or door.intersect_segment(mid2, p2):
            legal2 = False
            break
    len2 = manhattan_distance(p1, p2) if legal2 else float('inf')

    if legal1 or legal2:
        if len1 <= len2:
            return True, len1, make_l_path(p1, mid1, p2)
        else:
            return True, len2, make_l_path(p1, mid2, p2)
    else:
        return False, float('inf'), []


def shortest_avoiding_path(p1, p2, doors):
    # 直接路径
    legal, dist, path_points = is_path_legal(p1, p2, doors)
    if legal:
        return dist, 'direct', path_points

    # 绕行，尝试门的四个角点
    detour_points = []
    for door in doors:
        corners = [
            Point(door.x1, door.y1),
            Point(door.x1, door.y2),
            Point(door.x2, door.y1),
            Point(door.x2, door.y2),
        ]
        for corner in corners:
            if not any(corner == p for p in detour_points):
                detour_points.append(corner)

    best_dist = float('inf')
    best_path = []
    for corner in detour_points:
        leg1_legal, leg1_dist, leg1_path = is_path_legal(p1, corner, doors)
        leg2_legal, leg2_dist, leg2_path = is_path_legal(corner, p2, doors)

        if leg1_legal and leg2_legal:
            total = leg1_dist + leg2_dist
            if total < best_dist:
                best_dist = total
                best_path = leg1_path[:-1] + leg2_path

    if best_dist != float('inf'):
        return best_dist, 'detour', best_path
    else:
        return float('inf'), 'none', []


def build_graph(points, doors, progress_callback=None):
    # 构建完全图的边列表，每条边为（u, v, weight）
    n = len(points)
    edges = []
    total_pairs = n * (n - 1) // 2
    processed = 0

    for i in range(n):
        for j in range(i+1, n):
            dist, _, path_points = shortest_avoiding_path(points[i], points[j], doors)
            if dist != float('inf'):
                edges.append((i, j, dist, path_points))

            processed += 1
            if progress_callback and processed % max(1, total_pairs//20) == 0:
                progress_callback(processed, total_pairs)
    return edges


# ---------- 并查集 ----------
class DSU:
    def __init__(self, size):
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x, y):
        x_root = self.find(x)
        y_root = self.find(y)
        if x_root == y_root:
            return False

        if self.rank[x_root] < self.rank[y_root]:
            self.parent[x_root] = y_root
        elif self.rank[x_root] > self.rank[y_root]:
            self.parent[y_root] = x_root
        else:
            self.parent[y_root] = x_root
            self.rank[x_root] += 1
        return True


def kruskal_mst(num_nodes, edges):
    edges_sorted = sorted(edges, key=lambda e: e[2])
    dsu = DSU(num_nodes)
    mst_edges = []
    total_weight = 0.0

    for u, v, w, path in edges_sorted:
        if dsu.union(u, v):
            mst_edges.append((u, v, w, path))
            total_weight += w
            if len(mst_edges) == num_nodes - 1:
                break

    if len(mst_edges) != num_nodes - 1:
        return None, [] # 不连通
    return total_weight, mst_edges


def visualize(points, doors, mst_edges, title="室内布线方案"):
    # 可视化
    if not MATPLOTLIB_AVAILABLE:
        print("matplotlib未安装，无法显示图形。")
        return

    fig, ax = plt.subplots(figsize=(8,6))

    # 画出门（矩形）
    for door in doors:
        rect = patches.Rectangle((door.x1, door.y1), door.x2 - door.x1, door.y2 - door.y1, linewidth=2, edgecolor='red', facecolor='red', alpha=0.2)
        ax.add_patch(rect)

    # 画出插座点(蓝色＋符号)
    for i, p in enumerate(points):
        ax.scatter(p.x, p.y, c='blue', s=80, zorder=5, label='插座')
        ax.text(p.x + 0.1, p.y + 0.1, str(i+1), fontsize=12, fontweight='bold')

    # 绘制MST边(画出实际的曼哈顿折线)
    for u, v, w, path in mst_edges:
        xs = [p.x for p in path]
        ys = [p.y for p in path]
        ax.plot(xs, ys, 'g-', linewidth=2, alpha=0.7, label='布线路径')

    ax.set_title(title, fontsize=14)
    ax.set_xlabel("X 坐标", fontsize=12)
    ax.set_ylabel("Y 坐标", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(["插座", "门", "布线路径"], loc='upper right')
    plt.savefig("布线方案.png", dpi=300, bbox_inches='tight')
    print("图形已保存为：布线方案.png")
    plt.show()


def read_input_from_file(filename):
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    idx = 0
    n = int(lines[idx]); idx += 1
    points = []
    for _ in range(n):
        x, y = map(float, lines[idx].split())
        points.append(Point(x, y))
        idx += 1

    m = int(lines[idx]); idx += 1
    doors = []
    for _ in range(m):
        x1, y1, x2, y2 = map(float, lines[idx].split())
        doors.append(Rect(x1, y1, x2, y2))
        idx += 1

    return points, doors


def interactive_input():
    print("===== 室内布线系统（最小生成树，支持多个门） =====")
    n = int(input("请输入插座数量："))
    points = []
    for i in range(n):
        while True:
            try:
                x, y = map(float, input(f"插座{i+1}坐标(x y)：").split())
                points.append(Point(x, y))
                break
            except:
                print("输入错误，请重新输入")

    m = int(input("请输入门的数量："))
    doors = []
    for i in range(m):
        while True:
            try:
                x1, y1, x2, y2 = map(float, input("左下角(x1 y1) 和 右上角(x2 y2)，空格分隔: ").split())
                doors.append(Rect(x1, y1, x2, y2))
                break
            except:
                print("输入错误，请重新输入")

    return points, doors


def main():
    mode = input("选择输入方式：1-交互式输入  2-从文件读取（文件格式见说明）: ").strip()
    if mode == '2':
        filename = input("请输入文件名: ").strip()
        try:
            points, doors = read_input_from_file(filename)
            print(f"成功读取 {len(points)} 个插座和 {len(doors)} 个门")
        except Exception as e:
            print(f"读取文件失败：{e}")
            return
    else:
        points, doors = interactive_input()

    if len(points) < 2:
        print("至少需要2个插座才能布线。")
        return

    print("\n正在计算插座间的最短可行路径……")

    def progress(current, total):
        print(f"\r进度: {current}/{total} ({current/total*100:.1f}%)", end='', flush=True)

    edges = build_graph(points, doors, progress_callback=progress)
    print("\n路径计算完成！")

    if not edges:
        print("错误：没有任何两个插座可以连通，请检查门是否阻断了所有路径。")
        return

    total_len, mst_edges = kruskal_mst(len(points), edges)
    if total_len is None:
        print("错误：所有插座无法通过可行路径连通（图不连通）。")
        return

    print(f"\n最短电线总长度：{total_len:.2f}")
    print("\n布线方案（插座编号从一开始，边及长度）：")
    for u, v, w, path in mst_edges:
        path_str = "->".join([f"({p.x:.1f}, {p.y:.1f})" for p in path])
        print(f" 插座{u + 1} 到插座 {v + 1} | 长度：{w:.2f} | 路径：{path_str}")

    # 询问
    if MATPLOTLIB_AVAILABLE:
        show_graph = input("\n是否显示图形化布线图？（y/n）：").strip().lower()
        if show_graph == "y":
            visualize(points, doors, mst_edges)
    else:
        print("\n提示：未安装matplotlib，无法显示图形。")
        print("如需图形化展示，请在当前 Python 环境执行: pip install matplotlib")


if __name__ == "__main__":
    main()