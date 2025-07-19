# vision.py

import easyocr
import cv2
import numpy as np
from difflib import SequenceMatcher
import mss
import time

# ==============================================================================
# 2. 定义“观察者”类 - 负责识别
# ==============================================================================
class OCRWatcher:
    """
    一个负责监控屏幕特定区域并使用EasyOCR识别文字的类。
    """
    def __init__(self, similarity_threshold=0.8):
        """
        初始化OCR观察者。
        :param similarity_threshold: 字符串相似度的阈值。
        """
        self.threshold = similarity_threshold
        print("正在初始化 OCR 引擎 (首次运行可能需要下载模型)...")
        # 初始化EasyOCR，指定识别简体中文和英文
        self.reader = easyocr.Reader(['ch_sim', 'en'])
        self.sct = mss.mss() # 初始化mss，用于快速截图
        print("OCR 引擎准备就绪。")

    def read_text_from_region(self, region):
        """
        从屏幕的指定区域截图，进行图像预处理，然后识别其中的文字。
        这是一个可复用的核心功能。
        :param region: 一个元组 (x, y, width, height) 定义了截图区域。
        :return: EasyOCR的识别结果列表。
        """
        # 定义mss需要的监控区域格式
        monitor = {"top": region[1], "left": region[0], "width": region[2], "height": region[3]}
        # 使用mss进行截图
        sct_img = self.sct.grab(monitor)
        # 将截图数据转换为OpenCV可以处理的numpy数组格式
        frame = np.array(sct_img)
        # 将彩色图像（BGRA）转换为灰度图像，简化图像信息，有助于OCR
        gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
        # 应用二值化阈值处理。像素值低于150的变为0（黑色），高于150的变为255（白色）
        # 这可以增强文字和背景的对比度
        _, threshold_img = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        # 使用EasyOCR读取处理后的图像中的文字
        return self.reader.readtext(threshold_img) 

    def wait_for_text(self, target_text, monitor_region, retry_interval=0.75):
        """
        持续监控一个区域，直到识别出的文字与目标文字足够相似。
        :param target_text: 等待出现的目标文字。
        :param monitor_region: 要监控的屏幕区域。
        :param retry_interval: 每次识别失败后等待的秒数。
        """
        print(f"\n[观察者] 开始监控屏幕区域 {monitor_region}...")
        print(f"等待检测到文字与 '{target_text}' 的相似度高于 {self.threshold*100}%")
        while True:
            # 调用核心函数进行文字识别
            ocr_results = self.read_text_from_region(monitor_region)
            # 将所有识别到的文本片段连接成一个字符串，并移除空格
            detected_text = "".join([res[1] for res in ocr_results]).replace(" ", "")
            
            # 使用SequenceMatcher计算目标文本和检测到文本的相似度
            similarity = SequenceMatcher(None, target_text, detected_text).ratio()
            
            # 如果相似度达到或超过阈值
            if similarity >= self.threshold:
                print(f"\n[观察者] 成功! 检测到 '{detected_text}' (相似度 {similarity:.2f})")
                break # 退出循环
            else:
                # 如果检测到了文字但相似度不够
                if detected_text:
                    print(f"[观察者] 未达标... 当前识别: '{detected_text}' (相似度 {similarity:.2f}, {retry_interval}秒后重试)")
                # 如果没有检测到任何文字
                else:
                    print(f"[观察者] 未检测到任何文字... ({retry_interval}秒后重试)")
                # 等待一段时间再重试
                time.sleep(retry_interval)