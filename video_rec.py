import pygame
import cv2
import numpy as np
from pathlib import Path
import os

class VideoExporter:
    def __init__(self, output_path="output.mp4", fps=30):
        self.frames = []
        self.output_path = output_path
        self.fps = fps
        self.frame_size = (800,500)  # 用于校验后续帧尺寸是否一致
        # 初始化视频写入器
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 编码格式
        self.writer = cv2.VideoWriter(
            self.output_path,
            self.fourcc,
            self.fps,
            self.frame_size
        )

    def add_frame(self, surface: pygame.Surface):
        """添加 Pygame Surface 到帧列表"""
        # 转换为 OpenCV 兼容的格式
        frame = pygame.surfarray.array3d(surface)  # 获取三维数组 (width, height, 3)
        frame = frame.transpose([1, 0, 2])        # 转置为 (height, width, 3)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # RGB转BGR
        
        # 首次添加时记录尺寸，后续校验一致性
        if self.frame_size is None:
            self.frame_size = (frame.shape[1], frame.shape[0])  # (width, height)
        else:
            assert (frame.shape[1], frame.shape[0]) == self.frame_size
        
        self.writer.write(frame)

    def export(self):
        """导出为视频文件"""

        # 创建输出目录
        Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.writer.release()
        print(f"视频已保存至: {os.path.abspath(self.output_path)}")