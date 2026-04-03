import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as patches
from matplotlib.figure import Figure
import numpy as np
import threading
import time
import mysql.connector
import json
import random
import string
import math
from typing import List, Dict, Optional, Tuple, Callable

# 设置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# ===================== 数据库管理模块 =====================
class DatabaseManager:
    def __init__(self, host='localhost', user='root', password='******', database='hotel'):
        """初始化数据库连接"""
        try:
            self.connection = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database
            )
            self.cursor = self.connection.cursor()
            print("数据库连接成功")
        except mysql.connector.Error as e:
            print(f"数据库连接失败: {e}")
            raise
    
    def generate_user_id(self, length=8):
        """生成随机用户ID"""
        return ''.join(random.choices(string.digits, k=length))
    
    def register_user(self, username: str) -> Optional[str]:
        """注册新用户，返回用户ID"""
        try:
            # 生成唯一用户ID
            while True:
                user_id = self.generate_user_id()
                self.cursor.execute("SELECT id FROM user WHERE id = %s", (user_id,))
                if not self.cursor.fetchone():
                    break
            
            # 插入新用户
            self.cursor.execute("INSERT INTO user (id, username) VALUES (%s, %s)", 
                              (user_id, username))
            self.connection.commit()
            return user_id
            
        except mysql.connector.Error as e:
            print(f"注册用户失败: {e}")
            self.connection.rollback()
            return None
    
    def verify_user(self, user_id: str, username: str) -> bool:
        """验证用户身份"""
        try:
            self.cursor.execute("SELECT id FROM user WHERE id = %s AND username = %s", 
                              (user_id, username))
            return self.cursor.fetchone() is not None
        except mysql.connector.Error as e:
            print(f"验证用户失败: {e}")
            return False
    
    def save_signature(self, user_id: str, signature_data: Dict) -> bool:
        """保存签名数据"""
        try:
            # 压缩签名数据，移除不必要的字段以减少存储空间
            compressed_data = {
                'points': signature_data.get('points', []),
                'duration': signature_data.get('duration', 0),
                'total_points': signature_data.get('total_points', 0),
                'stroke_count': signature_data.get('stroke_count', 0)
            }
            signature_json = json.dumps(compressed_data, separators=(',', ':'))
            
            self.cursor.execute("INSERT INTO signatures (userid, signature) VALUES (%s, %s)", 
                              (user_id, signature_json))
            self.connection.commit()
            return True
        except mysql.connector.Error as e:
            print(f"保存签名失败: {e}")
            self.connection.rollback()
            return False
    
    def get_user_signatures(self, user_id: str) -> List[Dict]:
        """获取用户的所有签名数据"""
        try:
            self.cursor.execute("SELECT signature FROM signatures WHERE userid = %s", (user_id,))
            signatures = []
            for (signature_json,) in self.cursor.fetchall():
                signatures.append(json.loads(signature_json))
            return signatures
        except mysql.connector.Error as e:
            print(f"获取用户签名失败: {e}")
            return []
    
    def get_all_users_info(self) -> List[Dict[str, any]]:
        """获取所有用户的基本信息"""
        try:
            self.cursor.execute("""
                SELECT u.id, u.username, COUNT(s.id) as signature_count 
                FROM user u 
                LEFT JOIN signatures s ON u.id = s.userid 
                GROUP BY u.id, u.username
                ORDER BY u.id
            """)
            
            users_info = []
            for (user_id, username, count) in self.cursor.fetchall():
                users_info.append({
                    'id': user_id,
                    'username': username,
                    'signature_count': count
                })
            return users_info
        except mysql.connector.Error as e:
            print(f"获取用户信息失败: {e}")
            return []
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户及其所有签名数据"""
        try:
            self.cursor.execute("DELETE FROM user WHERE id = %s", (user_id,))
            self.connection.commit()
            return self.cursor.rowcount > 0
        except mysql.connector.Error as e:
            print(f"删除用户失败: {e}")
            self.connection.rollback()
            return False
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
            print("数据库连接已关闭")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# ===================== DTW算法模块 =====================
class DTWAlgorithm:
    """动态时间规整算法实现"""
    
    def __init__(self):
        self.threshold = 0.8  # 相似度阈值
    
    def euclidean_distance(self, point1: List[float], point2: List[float]) -> float:
        """计算欧氏距离"""
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(point1, point2)))
    
    def calculate_dtw_distance(self, sequence1: List[List[float]], 
                             sequence2: List[List[float]]) -> float:
        """计算两个时间序列之间的DTW距离"""
        n = len(sequence1)
        m = len(sequence2)
        
        # 创建距离矩阵
        distance_matrix = np.zeros((n, m))
        
        # 计算点与点之间的距离
        for i in range(n):
            for j in range(m):
                distance_matrix[i][j] = self.euclidean_distance(sequence1[i], sequence2[j])
        
        # 创建累积距离矩阵
        cost_matrix = np.zeros((n, m))
        cost_matrix[0][0] = distance_matrix[0][0]
        
        # 初始化第一行和第一列
        for i in range(1, n):
            cost_matrix[i][0] = cost_matrix[i-1][0] + distance_matrix[i][0]
        
        for j in range(1, m):
            cost_matrix[0][j] = cost_matrix[0][j-1] + distance_matrix[0][j]
        
        # 填充累积距离矩阵
        for i in range(1, n):
            for j in range(1, m):
                cost_matrix[i][j] = min(
                    cost_matrix[i-1][j],      # 插入
                    cost_matrix[i][j-1],      # 删除
                    cost_matrix[i-1][j-1]     # 匹配
                ) + distance_matrix[i][j]
        
        # 返回DTW距离
        return cost_matrix[n-1][m-1]
    
    def get_dtw_path(self, sequence1: List[List[float]], 
                    sequence2: List[List[float]]) -> List[Tuple[int, int]]:
        """获取DTW最优路径"""
        n = len(sequence1)
        m = len(sequence2)
        
        # 计算距离矩阵
        distance_matrix = np.zeros((n, m))
        for i in range(n):
            for j in range(m):
                distance_matrix[i][j] = self.euclidean_distance(sequence1[i], sequence2[j])
        
        # 计算累积距离矩阵
        cost_matrix = np.zeros((n, m))
        cost_matrix[0][0] = distance_matrix[0][0]
        
        for i in range(1, n):
            cost_matrix[i][0] = cost_matrix[i-1][0] + distance_matrix[i][0]
        
        for j in range(1, m):
            cost_matrix[0][j] = cost_matrix[0][j-1] + distance_matrix[0][j]
        
        for i in range(1, n):
            for j in range(1, m):
                cost_matrix[i][j] = min(
                    cost_matrix[i-1][j],
                    cost_matrix[i][j-1],
                    cost_matrix[i-1][j-1]
                ) + distance_matrix[i][j]
        
        # 回溯路径
        path = []
        i, j = n-1, m-1
        
        while i > 0 or j > 0:
            path.append((i, j))
            
            if i == 0:
                j -= 1
            elif j == 0:
                i -= 1
            else:
                min_cost = min(
                    cost_matrix[i-1][j],
                    cost_matrix[i][j-1],
                    cost_matrix[i-1][j-1]
                )
                
                if min_cost == cost_matrix[i-1][j-1]:
                    i -= 1
                    j -= 1
                elif min_cost == cost_matrix[i-1][j]:
                    i -= 1
                else:
                    j -= 1
        
        path.append((0, 0))
        path.reverse()
        
        return path
    
    def normalize_sequence(self, sequence: List[List[float]]) -> List[List[float]]:
        """序列归一化"""
        if not sequence:
            return []
        
        sequence = np.array(sequence)
        
        # 计算每个维度的均值和标准差
        mean = np.mean(sequence, axis=0)
        std = np.std(sequence, axis=0)
        
        # 避免除以零
        std = np.where(std == 0, 1, std)
        
        # Z-score归一化
        normalized = (sequence - mean) / std
        
        return normalized.tolist()
    
    def resample_sequence(self, sequence: List[List[float]], target_length: int = 100) -> List[List[float]]:
        """重采样序列到目标长度"""
        if len(sequence) <= 1:
            return sequence
        
        if len(sequence) == target_length:
            return sequence
        
        old_indices = np.linspace(0, len(sequence) - 1, len(sequence))
        new_indices = np.linspace(0, len(sequence) - 1, target_length)
        
        resampled = []
        for dim in range(len(sequence[0])):
            dim_values = [point[dim] for point in sequence]
            interpolated = np.interp(new_indices, old_indices, dim_values)
            
            if not resampled:
                for i in range(target_length):
                    resampled.append([interpolated[i]])
            else:
                for i in range(target_length):
                    resampled[i].append(interpolated[i])
        
        return resampled
    
    def calculate_similarity(self, signature1: Dict, signature2: Dict) -> Dict:
        """计算两个签名的相似度"""
        try:
            # 提取特征序列
            features1 = self.extract_features(signature1)
            features2 = self.extract_features(signature2)
            
            if not features1 or not features2:
                return {'similarity': 0.0, 'dtw_distance': float('inf'), 'passed': False}
            
            # 对齐签名起点到原点
            features1 = self._align_signature_start(features1)
            features2 = self._align_signature_start(features2)
            
            # 确保特征向量维度一致（只使用位置和速度特征，固定为3维）
            features1 = self._standardize_features(features1)
            features2 = self._standardize_features(features2)
            
            # 归一化和重采样到相同长度
            normalized1 = self.normalize_sequence(features1)
            normalized2 = self.normalize_sequence(features2)
            
            # 重采样到相同的目标长度
            target_length = min(100, max(len(normalized1), len(normalized2)))
            resampled1 = self.resample_sequence(normalized1, target_length)
            resampled2 = self.resample_sequence(normalized2, target_length)
            
            # 计算DTW距离
            dtw_distance = self.calculate_dtw_distance(resampled1, resampled2)
            
            # 调整相似度计算
            # 使用更平缓的衰减函数
            similarity = max(0.0, 1.0 / (1 + (dtw_distance / 100.0)**3))
            
            # 调试信息
            print(f"DTW距离: {dtw_distance:.2f}, 相似度: {similarity:.4f}, 验证结果: {'通过' if similarity >= self.threshold else '失败'}")
            
            # 获取DTW路径用于可视化
            dtw_path = self.get_dtw_path(resampled1, resampled2)
            
            return {
                'similarity': similarity,
                'dtw_distance': dtw_distance,
                'passed': similarity >= self.threshold,
                'dtw_path': dtw_path,
                'resampled_seq1': resampled1,
                'resampled_seq2': resampled2
            }
            
        except Exception as e:
            print(f"计算相似度时出错: {e}")
            return {'similarity': 0.0, 'dtw_distance': float('inf'), 'passed': False}
    
    def extract_features(self, signature_data: Dict) -> List[List[float]]:
        """从签名数据中提取特征序列"""
        try:
            points = signature_data.get('points', [])
            if not points:
                return []
            
            features = []
            
            for i, point in enumerate(points):
                feature_vector = []
                
                # 基本位置特征
                feature_vector.append(point['x'])
                feature_vector.append(point['y'])
                
                # 速度特征（除了第一个点）
                if i > 0:
                    prev_point = points[i-1]
                    dx = point['x'] - prev_point['x']
                    dy = point['y'] - prev_point['y']
                    dt = point['timestamp'] - prev_point['timestamp']
                    
                    if dt > 0:
                        velocity = math.sqrt(dx**2 + dy**2) / dt
                        feature_vector.append(velocity)
                        
                        # 方向特征
                        direction = math.atan2(dy, dx)
                        feature_vector.append(direction)
                        
                        # 加速度特征
                        if i > 1:
                            prev_prev_point = points[i-2]
                            prev_dx = prev_point['x'] - prev_prev_point['x']
                            prev_dy = prev_point['y'] - prev_prev_point['y']
                            prev_dt = prev_point['timestamp'] - prev_prev_point['timestamp']
                            
                            if prev_dt > 0:
                                prev_velocity = math.sqrt(prev_dx**2 + prev_dy**2) / prev_dt
                                acceleration = (velocity - prev_velocity) / ((dt + prev_dt) / 2)
                                feature_vector.append(acceleration)
                            else:
                                feature_vector.append(0.0)
                        else:
                            feature_vector.append(0.0)
                    else:
                        feature_vector.extend([0.0, 0.0, 0.0])
                else:
                    # 第一个点，速度和方向设为0
                    feature_vector.extend([0.0, 0.0, 0.0])
                
                # 压力特征（如果存在）
                if 'pressure' in point:
                    feature_vector.append(point['pressure'])
                else:
                    feature_vector.append(1.0)  # 默认压力
                
                features.append(feature_vector)
            
            return features
            
        except Exception as e:
            print(f"特征提取出错: {e}")
            return []
    
    def _standardize_features(self, features: List[List[float]]) -> List[List[float]]:
        """标准化特征向量，确保所有向量维度一致（固定为3维：x, y, velocity）"""
        standardized = []
        
        for feature_vec in features:
            # 确保至少有3个维度
            if len(feature_vec) >= 3:
                # 只取前3个维度：x, y, velocity
                standardized.append([feature_vec[0], feature_vec[1], feature_vec[2]])
            elif len(feature_vec) == 2:
                # 只有位置信息，速度设为0
                standardized.append([feature_vec[0], feature_vec[1], 0.0])
            else:
                # 异常情况，跳过或使用默认值
                continue
        
        return standardized
    
    def _calculate_avg_feature_distance(self, seq1: List[List[float]], seq2: List[List[float]]) -> float:
        """计算两个序列的平均特征距离，用作相似度计算的基准"""
        if not seq1 or not seq2:
            return float('inf')
        
        total_distance = 0.0
        count = 0
        
        # 采样一些点对来计算平均距离
        step = max(1, min(len(seq1), len(seq2)) // 10)  # 采样10个点
        
        for i in range(0, min(len(seq1), len(seq2)), step):
            if i < len(seq1) and i < len(seq2):
                dist = self.euclidean_distance(seq1[i], seq2[i])
                total_distance += dist
                count += 1
        
        return total_distance / count if count > 0 else float('inf')
    
    def set_threshold(self, threshold: float):
        """设置相似度阈值"""
        self.threshold = max(0.0, min(1.0, threshold))
    
    def get_threshold(self) -> float:
        """获取当前相似度阈值"""
        return self.threshold
    
    def _align_signature_start(self, features: List[List[float]]) -> List[List[float]]:
        """对齐签名起点到原点"""
        if not features:
            return features
        
        # 获取第一个点的位置
        start_x = features[0][0]
        start_y = features[0][1] if len(features[0]) > 1 else 0.0
        
        # 将所有点平移，使起点移到原点
        aligned_features = []
        for feature_vec in features:
            aligned_vec = feature_vec.copy()
            if len(aligned_vec) >= 2:
                aligned_vec[0] -= start_x  # x坐标平移
                aligned_vec[1] -= start_y  # y坐标平移
            aligned_features.append(aligned_vec)
        
        return aligned_features

# ===================== 签名画布模块 =====================
class SignatureCanvas(tk.Canvas):
    """签名画布组件"""
    
    def __init__(self, parent, width=400, height=200, bg='white', on_signature_complete: Optional[Callable] = None):
        super().__init__(parent, width=width, height=height, bg=bg)
        
        self.width = width
        self.height = height
        
        # 签名数据
        self.current_stroke = []  # 当前笔画
        self.all_strokes = []     # 所有笔画
        self.points = []          # 所有点（包含时间戳）
        
        # 绘图状态
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        
        # 回调函数
        self.on_signature_complete = on_signature_complete
        
        # 绑定鼠标事件
        self.bind("<Button-1>", self.start_draw)
        self.bind("<B1-Motion>", self.draw)
        self.bind("<ButtonRelease-1>", self.stop_draw)
        
        # 绘图设置
        self.configure(highlightthickness=2, highlightbackground="gray")
        self.configure(cursor="crosshair")
    
    def start_draw(self, event):
        """开始绘制"""
        self.is_drawing = True
        self.last_x = event.x
        self.last_y = event.y
        
        # 记录点数据
        point_data = {
            'x': event.x,
            'y': event.y,
            'timestamp': time.time() * 1000,  # 毫秒时间戳
            'pressure': 1.0  # 鼠标默认压力
        }
        
        self.points.append(point_data)
        self.current_stroke.append(point_data)
        
        # 绘制起始点
        self.create_oval(event.x-2, event.y-2, event.x+2, event.y+2, 
                        fill="black", tags="signature")
    
    def draw(self, event):
        """绘制线条"""
        if not self.is_drawing:
            return
        
        # 检查坐标是否在画布范围内
        if event.x < 0 or event.x > self.width or event.y < 0 or event.y > self.height:
            return
        
        # 记录点数据
        point_data = {
            'x': event.x,
            'y': event.y,
            'timestamp': time.time() * 1000,
            'pressure': 1.0
        }
        
        self.points.append(point_data)
        self.current_stroke.append(point_data)
        
        # 绘制线条
        if self.last_x is not None and self.last_y is not None:
            self.create_line(self.last_x, self.last_y, event.x, event.y,
                           width=2, fill="black", tags="signature", capstyle=tk.ROUND, smooth=True)
        
        self.last_x = event.x
        self.last_y = event.y
    
    def stop_draw(self, event):
        """停止绘制"""
        if self.is_drawing:
            self.is_drawing = False
            self.all_strokes.append(self.current_stroke)
            self.current_stroke = []
            self.last_x = None
            self.last_y = None
            
            # 如果有回调函数，调用它
            if self.on_signature_complete:
                self.on_signature_complete()
    
    def clear_canvas(self):
        """清空画布"""
        self.delete("signature")
        self.points = []
        self.all_strokes = []
        self.current_stroke = []
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
    
    def get_signature_data(self) -> Dict:
        """获取签名数据"""
        return {
            'points': self.points,
            'strokes': self.all_strokes,
            'canvas_width': self.width,
            'canvas_height': self.height,
            'duration': self._calculate_duration(),
            'total_points': len(self.points),
            'stroke_count': len(self.all_strokes)
        }
    
    def _calculate_duration(self) -> float:
        """计算签名总持续时间"""
        if len(self.points) < 2:
            return 0.0
        
        start_time = self.points[0]['timestamp']
        end_time = self.points[-1]['timestamp']
        return end_time - start_time
    
    def load_signature_data(self, signature_data: Dict):
        """加载签名数据到画布（用于显示参考签名）"""
        self.clear_canvas()
        
        points = signature_data.get('points', [])
        if not points:
            return
        
        # 绘制签名
        for i, point in enumerate(points):
            if i > 0:
                prev_point = points[i-1]
                self.create_line(prev_point['x'], prev_point['y'], 
                               point['x'], point['y'],
                               width=2, fill="blue", tags="signature", 
                               capstyle=tk.ROUND, smooth=True)
            else:
                self.create_oval(point['x']-2, point['y']-2, 
                               point['x']+2, point['y']+2,
                               fill="blue", tags="signature")
    
    def get_signature_stats(self) -> Dict:
        """获取签名统计信息"""
        if not self.points:
            return {
                'duration': 0.0,
                'total_points': 0,
                'stroke_count': 0,
                'average_speed': 0.0,
                'bounding_box': None
            }
        
        # 计算边界框
        x_coords = [p['x'] for p in self.points]
        y_coords = [p['y'] for p in self.points]
        bounding_box = {
            'min_x': min(x_coords),
            'max_x': max(x_coords),
            'min_y': min(y_coords),
            'max_y': max(y_coords),
            'width': max(x_coords) - min(x_coords),
            'height': max(y_coords) - min(y_coords)
        }
        
        # 计算平均速度
        total_distance = 0.0
        total_time = 0.0
        
        for i in range(1, len(self.points)):
            prev_point = self.points[i-1]
            curr_point = self.points[i]
            
            dx = curr_point['x'] - prev_point['x']
            dy = curr_point['y'] - prev_point['y']
            distance = (dx**2 + dy**2) ** 0.5
            
            dt = curr_point['timestamp'] - prev_point['timestamp']
            
            total_distance += distance
            total_time += dt
        
        average_speed = total_distance / total_time if total_time > 0 else 0.0
        
        return {
            'duration': self._calculate_duration(),
            'total_points': len(self.points),
            'stroke_count': len(self.all_strokes),
            'average_speed': average_speed,
            'bounding_box': bounding_box
        }
    
    def is_signature_empty(self) -> bool:
        """检查签名是否为空"""
        return len(self.points) == 0
    
    def export_to_json(self) -> str:
        """导出签名为JSON字符串"""
        return json.dumps(self.get_signature_data(), ensure_ascii=False, indent=2)
    
    def import_from_json(self, json_str: str):
        """从JSON字符串导入签名数据"""
        try:
            signature_data = json.loads(json_str)
            self.load_signature_data(signature_data)
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
        except Exception as e:
            print(f"导入签名数据错误: {e}")
    
    def set_canvas_size(self, width: int, height: int):
        """设置画布大小"""
        self.width = width
        self.height = height
        self.configure(width=width, height=height)
    
    def get_drawing_bounds(self) -> Optional[Dict]:
        """获取绘图的边界"""
        if not self.points:
            return None
        
        x_coords = [p['x'] for p in self.points]
        y_coords = [p['y'] for p in self.points]
        
        return {
            'min_x': min(x_coords),
            'max_x': max(x_coords),
            'min_y': min(y_coords),
            'max_y': max(y_coords),
            'center_x': (min(x_coords) + max(x_coords)) / 2,
            'center_y': (min(y_coords) + max(y_coords)) / 2
        }

# ===================== 主应用程序 =====================
class SignatureVerificationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("基于动态时间规整算法的签名认证系统")
        self.root.geometry("1200x800")
        
        # 初始化核心组件
        try:
            self.db = DatabaseManager()
            self.dtw = DTWAlgorithm()
        except Exception as e:
            messagebox.showerror("错误", f"数据库连接失败: {e}")
            self.root.quit()
            return
        
        # 界面变量
        self.username = tk.StringVar()
        self.user_id = tk.StringVar()
        
        # 当前签名数据
        self.current_signature = None
        self.reference_signature = None
        self.current_comparison_result = None
        
        # 创建界面
        self.create_widgets()
        self.refresh_users_list()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 配置网格权重
        main_frame.grid_rowconfigure(0, weight=1)  # 上方区域占1/2
        main_frame.grid_rowconfigure(1, weight=2)  # 下方区域占2/2
        main_frame.grid_columnconfigure(0, weight=1)  # 左侧占1/2
        main_frame.grid_columnconfigure(1, weight=1)  # 右侧占1/2
        
        # 左上区域 - 用户信息输入（占左上四分之一）
        self.create_user_input_area(main_frame)
        
        # 右上区域 - 签名画布（占右上四分之一）
        self.create_signature_canvas(main_frame)
        
        # 下方区域 - 对比结果显示（占下方二分之一）
        self.create_comparison_area(main_frame)
    
    def create_user_input_area(self, parent):
        """创建用户输入区域"""
        # 左上框架
        left_frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # 配置左框架网格权重
        left_frame.grid_rowconfigure(2, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_columnconfigure(1, weight=1)
        
        # 用户名输入（第一行）
        tk.Label(left_frame, text="用户名:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(left_frame, textvariable=self.username, width=20).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 用户ID输入（第二行）
        tk.Label(left_frame, text="用户ID:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(left_frame, textvariable=self.user_id, width=20).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # 按钮区域（第三行）
        button_frame = tk.Frame(left_frame)
        button_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=10)
        
        tk.Button(button_frame, text="注册签名", command=self.register_signature, 
                 bg="#4CAF50", fg="white", width=10).grid(row=0, column=0, padx=5)
        tk.Button(button_frame, text="验证签名", command=self.verify_signature, 
                 bg="#2196F3", fg="white", width=10).grid(row=0, column=1, padx=5)
        tk.Button(button_frame, text="删除用户", command=self.delete_user, 
                 bg="#f44336", fg="white", width=10).grid(row=0, column=2, padx=5)
        
        # 用户列表显示（第四行）
        tk.Label(left_frame, text="数据库已有用户:", font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        # 创建用户列表的文本框和滚动条
        list_frame = tk.Frame(left_frame)
        list_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.users_text = tk.Text(list_frame, width=30, height=8, yscrollcommand=scrollbar.set)
        self.users_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.users_text.yview)
    
    def create_signature_canvas(self, parent):
        """创建签名画布区域"""
        # 右上框架
        right_frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # 配置右框架网格权重
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)
        
        # 标题
        tk.Label(right_frame, text="签名输入画布", font=("Arial", 12, "bold")).grid(row=0, column=0, pady=5)
        
        # 签名画布
        self.signature_canvas = SignatureCanvas(right_frame, width=400, height=200)
        self.signature_canvas.grid(row=1, column=0, padx=10, pady=10)
        
        # 清空签名按钮
        tk.Button(right_frame, text="清空签名", command=self.clear_signature,
                 bg="#FF9800", fg="white", width=15).grid(row=2, column=0, pady=5)
    
    def create_comparison_area(self, parent):
        """创建对比结果显示区域"""
        # 下方框架
        bottom_frame = tk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        bottom_frame.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        
        # 配置底部框架网格权重
        bottom_frame.grid_rowconfigure(1, weight=1)  # matplotlib图形占主要空间
        bottom_frame.grid_columnconfigure(0, weight=1)
        
        # 标题
        title_frame = tk.Frame(bottom_frame)
        title_frame.grid(row=0, column=0, sticky="ew")
        tk.Label(title_frame, text="DTW算法对比结果", font=("Arial", 12, "bold")).pack(pady=5)
        
        # 结果显示
        result_frame = tk.Frame(bottom_frame)
        result_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        # 创建matplotlib图形
        self.create_comparison_plot(result_frame)
        
        # 验证结果显示
        self.result_label = tk.Label(bottom_frame, text="等待验证...", 
                                   font=("Arial", 11, "bold"))
        self.result_label.grid(row=2, column=0, pady=5)
    
    def create_comparison_plot(self, parent):
        """创建对比图表"""
        # 创建matplotlib图形
        self.fig = Figure(figsize=(10, 4), dpi=80)
        self.ax1 = self.fig.add_subplot(121)
        self.ax2 = self.fig.add_subplot(122)
        
        self.ax1.set_title("当前签名轨迹")
        self.ax1.set_xlabel("X坐标")
        self.ax1.set_ylabel("Y坐标")
        self.ax1.grid(True, alpha=0.3)
        
        self.ax2.set_title("DTW路径对比")
        self.ax2.set_xlabel("参考签名索引")
        self.ax2.set_ylabel("当前签名索引")
        self.ax2.grid(True, alpha=0.3)
        
        # 将matplotlib图表嵌入tkinter
        self.canvas_plot = FigureCanvasTkAgg(self.fig, parent)
        self.canvas_plot.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 初始化空图表
        self.clear_comparison_plot()
    
    def clear_comparison_plot(self):
        """清空对比图表"""
        self.ax1.clear()
        self.ax2.clear()
        
        # 反转Y轴方向，使与画布一致
        self.ax1.invert_yaxis()
        
        self.ax1.set_title("当前签名轨迹")
        self.ax1.set_xlabel("X坐标")
        self.ax1.set_ylabel("Y坐标")
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_xlim(0, 400)
        self.ax1.set_ylim(0, 200)  # 正常Y轴范围，但通过invert_yaxis()反转方向
        
        self.ax2.set_title("DTW路径对比")
        self.ax2.set_xlabel("参考签名索引")
        self.ax2.set_ylabel("当前签名索引")
        self.ax2.grid(True, alpha=0.3)
        
        self.canvas_plot.draw()
    
    def update_comparison_plot(self, signature_data, reference_data=None, dtw_result=None):
        """更新对比图表"""
        self.ax1.clear()
        self.ax2.clear()
        
        # 当前签名轨迹（对齐后）
        if signature_data and 'points' in signature_data:
            # 提取特征并对齐
            features1 = self.dtw.extract_features(signature_data)
            if features1:
                features1 = self.dtw._align_signature_start(features1)
                
                x_coords = [f[0] for f in features1]
                y_coords = [-f[1] for f in features1]  # 直接加负号反转Y坐标
                
                self.ax1.plot(x_coords, y_coords, 'b-', linewidth=2, label='当前签名')
                self.ax1.scatter(0, 0, c='green', s=50, label='起点', zorder=5)
                if x_coords and y_coords:
                    self.ax1.scatter(x_coords[-1], y_coords[-1], c='red', s=50, label='终点', zorder=5)
                
                # 参考签名轨迹（对齐后）
                if reference_data and 'points' in reference_data:
                    features2 = self.dtw.extract_features(reference_data)
                    if features2:
                        features2 = self.dtw._align_signature_start(features2)
                        ref_x = [f[0] for f in features2]
                        ref_y = [-f[1] for f in features2]  # 直接加负号反转Y坐标
                        self.ax1.plot(ref_x, ref_y, 'g--', linewidth=1.5, alpha=0.7, label='参考签名')
                
                self.ax1.legend()
        
        self.ax1.set_title("签名轨迹对比（起点对齐）")
        self.ax1.set_xlabel("X坐标")
        self.ax1.set_ylabel("Y坐标")
        self.ax1.grid(True, alpha=0.3)
        
        # 动态设置坐标轴范围以适应对齐后的签名
        self.ax1.set_xlim(-50, 350)
        self.ax1.set_ylim(-150, 150)
        
        # DTW路径图
        if dtw_result and 'dtw_path' in dtw_result and dtw_result['dtw_path']:
            path = dtw_result['dtw_path']
            seq1_indices = [p[0] for p in path]
            seq2_indices = [p[1] for p in path]
            
            self.ax2.plot(seq2_indices, seq1_indices, 'r-', linewidth=2, alpha=0.7, label='DTW路径')
            self.ax2.scatter(seq2_indices[0], seq1_indices[0], c='green', s=50, label='起点', zorder=5)
            self.ax2.scatter(seq2_indices[-1], seq1_indices[-1], c='red', s=50, label='终点', zorder=5)
            self.ax2.legend()
            
            # 添加相似度信息
            similarity = dtw_result.get('similarity', 0)
            passed = dtw_result.get('passed', False)
            status = "通过" if passed else "失败"
            color = "green" if passed else "red"
            
            self.ax2.text(0.5, 0.95, f'相似度: {similarity:.3f} | 验证结果: {status}', 
                         transform=self.ax2.transAxes, ha='center', va='top',
                         bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))
        
        self.ax2.set_title("DTW对齐路径")
        self.ax2.set_xlabel("参考签名索引")
        self.ax2.set_ylabel("当前签名索引")
        self.ax2.grid(True, alpha=0.3)
        
        self.canvas_plot.draw()
    
    def register_signature(self):
        """注册签名"""
        username = self.username.get().strip()
        user_id = self.user_id.get().strip()
        
        if not username:
            messagebox.showwarning("警告", "请输入用户名")
            return
        
        if self.signature_canvas.is_signature_empty():
            messagebox.showwarning("警告", "请先在画布上签名")
            return
        
        try:
            # 检查用户ID是否提供，如果没有则注册新用户
            if user_id:
                # 验证用户身份
                if not self.db.verify_user(user_id, username):
                    messagebox.showerror("错误", "用户ID或用户名不正确")
                    return
                
                # 保存签名
                signature_data = self.signature_canvas.get_signature_data()
                if self.db.save_signature(user_id, signature_data):
                    messagebox.showinfo("成功", "签名注册成功！")
                    self.clear_signature()
                else:
                    messagebox.showerror("错误", "签名保存失败")
            else:
                # 注册新用户
                new_user_id = self.db.register_user(username)
                if new_user_id:
                    # 保存签名
                    signature_data = self.signature_canvas.get_signature_data()
                    if self.db.save_signature(new_user_id, signature_data):
                        messagebox.showinfo("成功", f"用户注册成功！\n您的用户ID是: {new_user_id}\n请妥善保存此ID用于后续操作")
                        self.user_id.set(new_user_id)
                        self.clear_signature()
                    else:
                        messagebox.showerror("错误", "签名保存失败")
                else:
                    messagebox.showerror("错误", "用户注册失败，用户名可能已存在")
            
            # 刷新用户列表
            self.refresh_users_list()
            
        except Exception as e:
            messagebox.showerror("错误", f"操作失败: {e}")
    
    def verify_signature(self):
        """验证签名"""
        username = self.username.get().strip()
        user_id = self.user_id.get().strip()
        
        if not username or not user_id:
            messagebox.showwarning("警告", "请输入用户名和用户ID")
            return
        
        if self.signature_canvas.is_signature_empty():
            messagebox.showwarning("警告", "请先在画布上签名")
            return
        
        try:
            # 验证用户身份
            if not self.db.verify_user(user_id, username):
                messagebox.showerror("错误", "用户ID或用户名不正确")
                return
            
            # 获取用户参考签名
            reference_signatures = self.db.get_user_signatures(user_id)
            if not reference_signatures:
                messagebox.showerror("错误", "该用户没有注册的签名")
                return
            
            # 获取当前签名
            current_signature_data = self.signature_canvas.get_signature_data()
            
            # 计算与所有参考签名的相似度，取最佳匹配
            best_similarity = 0.0
            best_result = None
            best_reference = None
            
            for ref_signature in reference_signatures:
                result = self.dtw.calculate_similarity(current_signature_data, ref_signature)
                if result['similarity'] > best_similarity:
                    best_similarity = result['similarity']
                    best_result = result
                    best_reference = ref_signature
            
            if best_result:
                self.current_comparison_result = best_result
                self.reference_signature = best_reference
                self.current_signature = current_signature_data
                
                # 更新对比图表
                self.update_comparison_plot(current_signature_data, best_reference, best_result)
                
                # 显示结果
                similarity = best_result['similarity']
                passed = best_result['passed']
                dtw_distance = best_result['dtw_distance']
                
                if passed:
                    self.result_label.config(text="✓ 验证通过", fg="green")
                else:
                    self.result_label.config(text="✗ 验证失败", fg="red")
            
        except Exception as e:
            messagebox.showerror("错误", f"验证失败: {e}")
    
    def delete_user(self):
        """删除用户"""
        username = self.username.get().strip()
        user_id = self.user_id.get().strip()
        
        if not username or not user_id:
            messagebox.showwarning("警告", "请输入用户名和用户ID")
            return
        
        # 确认删除
        result = messagebox.askyesno("确认删除", 
                                   f"确定要删除用户 {username}(ID: {user_id}) 吗？\n这将删除该用户的所有签名数据。")
        if not result:
            return
        
        try:
            # 验证用户身份
            if not self.db.verify_user(user_id, username):
                messagebox.showerror("错误", "用户ID或用户名不正确")
                return
            
            # 删除用户
            if self.db.delete_user(user_id):
                messagebox.showinfo("成功", "用户及其所有签名数据已删除")
                self.username.set("")
                self.user_id.set("")
                self.clear_signature()
                
                # 刷新用户列表
                self.refresh_users_list()
            else:
                messagebox.showerror("错误", "删除用户失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"删除失败: {e}")
    

    
    def clear_signature(self):
        """清空签名"""
        self.signature_canvas.clear_canvas()
        self.clear_comparison_plot()
        self.result_label.config(text="等待验证...", fg="black")
        self.current_signature = None
        self.reference_signature = None
        self.current_comparison_result = None
    
    def refresh_users_list(self):
        """刷新用户列表显示"""
        try:
            users_info = self.db.get_all_users_info()
            
            self.users_text.delete(1.0, tk.END)
            
            if users_info:
                for user in users_info:
                    user_info = f"用户名: {user['username']}\n"
                    user_info += f"签名数量: {user['signature_count']}\n"
                    user_info += "-" * 25 + "\n"
                    
                    self.users_text.insert(tk.END, user_info)
            else:
                self.users_text.insert(tk.END, "暂无用户数据")
                
        except Exception as e:
            print(f"刷新用户列表失败: {e}")
    
    def on_closing(self):
        """关闭程序时的清理工作"""
        try:
            if hasattr(self, 'db'):
                self.db.close()
        except Exception as e:
            print(f"关闭数据库连接时出错: {e}")
        
        self.root.destroy()

# ===================== 数据库初始化脚本 =====================
def init_database():
    """初始化数据库表结构"""
    try:
        # 这里可以根据需要添加数据库初始化代码
        print("请确保已创建以下表结构：")
        print("""
CREATE TABLE user (
    id INT PRIMARY KEY,
    username VARCHAR(100) NOT NULL
);

CREATE TABLE signatures (
    id INT AUTO_INCREMENT PRIMARY KEY,
    userid INT,
    signature LONGTEXT,  -- 使用LONGTEXT以支持更多数据
    FOREIGN KEY (userid) REFERENCES user(id) ON DELETE CASCADE
);
        """)
        return True
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        return False

# ===================== 主程序入口 =====================
def main():
    """主函数"""
    # 初始化数据库（如果需要）
    # init_database()
    
    root = tk.Tk()
    
    # 创建应用实例
    try:
        app = SignatureVerificationApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("启动错误", f"程序启动失败: {e}")
        root.destroy()

if __name__ == "__main__":
    main()