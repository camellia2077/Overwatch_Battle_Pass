# workflows.py

import time
import random

# ==============================================================================
# 4. “退出者”类 - 负责退出比赛流程
# ==============================================================================
class GameExiter:
    """负责执行从比赛中退出到主菜单的整个流程的类。"""
    def __init__(self, watcher, executor, steps_config):
        """
        初始化退出者。
        :param watcher: 一个OCRWatcher实例，用于查找按钮。
        :param executor: 一个PyAutoGuiExecutor实例，用于点击按钮。
        :param steps_config: 一个包含退出步骤的配置列表。
        """
        self.watcher = watcher 
        self.executor = executor
        self.steps = steps_config

    def find_and_click_button(self, text_to_find, region, timeout=5):
        """
        在指定区域内查找包含特定文本的按钮，并点击它。
        :param text_to_find: 按钮上的目标文字。
        :param region: 在哪个屏幕区域内查找。
        :param timeout: 查找的超时时间（秒）。
        :return: 如果成功找到并点击，返回True，否则返回False。
        """
        print(f"[退出者] 正在寻找按钮 '{text_to_find}'...")
        start_time = time.time()
        # 在超时时间内持续尝试
        while time.time() - start_time < timeout:
            # 调用观察者的通用识别方法获取区域内的所有文字和它们的位置
            ocr_results = self.watcher.read_text_from_region(region)
            
            # 遍历所有识别结果
            for (bbox, text, prob) in ocr_results:
                # 如果识别到的文本包含目标文本（移除空格后比较）
                if text_to_find in text.replace(" ", ""):
                    print(f"[退出者] 找到按钮 '{text}' (置信度: {prob:.2f})! 准备精确点击。")
                    # bbox是[[左上], [右上], [右下], [左下]]的坐标
                    top_left = bbox[0]
                    bottom_right = bbox[2]
                    # 计算按钮的中心点（相对于截图区域的坐标）
                    center_x_relative = (top_left[0] + bottom_right[0]) / 2
                    center_y_relative = (top_left[1] + bottom_right[1]) / 2
                    # 获取区域本身的左上角绝对坐标
                    region_x, region_y, _, _ = region
                    # 计算出按钮中心的绝对屏幕坐标
                    absolute_center_x = int(region_x + center_x_relative)
                    absolute_center_y = int(region_y + center_y_relative)
                    
                    # 移动并点击
                    self.executor.human_like_move_to(absolute_center_x, absolute_center_y, duration=0.3)
                    self.executor.click()
                    return True # 成功，返回
            time.sleep(1) # 暂停1秒后再次尝试
        
        print(f"[退出者] 警告：在 {timeout} 秒内未找到按钮 '{text_to_find}'。")
        return False

    def run_exit_sequence(self):
        """
        执行完整的退出流程。
        """
        print("\n--- [退出者] 开始执行退出流程 ---")
        # 1. 按下 'esc' 键打开菜单
        self.executor.human_like_press('esc')
        time.sleep(random.uniform(0.2, 0.3))
        
        # 2. 循环执行预设的点击步骤（例如：点击“离开比赛”，然后点击“确认”）
        for step in self.steps:
            self.find_and_click_button(step['text'], step['region'])
            time.sleep(random.uniform(0.2, 0.3))
            
        # 3. 执行一系列按键来跳过结算画面（这些按键是针对特定游戏设计的）
        print("[退出者] 执行键盘快捷键以跳过结算...")
        time.sleep(random.uniform(0.5, 0.75))
        self.executor.human_like_press('space')
        self.executor.human_like_press('space')
        print("[退出者] 等待结算动画...")
        time.sleep(random.uniform(0.3, 0.4)) 
        print("[退出者] 按下空格键以重新聚焦按钮...")
        time.sleep(random.uniform(0.2, 0.4)) 
        self.executor.human_like_press('space')
        self.executor.human_like_press('space')
        self.executor.human_like_press('space')
        print("\n--- [退出者] 退出流程执行完毕！---")

# ==============================================================================
# 5. “启动者”类 - 负责开始新游戏
# ==============================================================================
class GameStarter:
    """负责点击“开始游戏”按钮，启动新一轮游戏的类。"""
    def __init__(self, executor, start_region):
        """
        初始化启动者。
        :param executor: 一个PyAutoGuiExecutor实例，用于移动和点击。
        :param start_region: “开始游戏”按钮的大致区域。
        """
        self.executor = executor
        self.start_region = start_region

    def start_new_game(self):
        """
        开始一轮新游戏。
        """
        print("\n--- [启动者] 开始新一轮游戏 ---")
        x, y, w, h = self.start_region
        # 在按钮区域内生成一个随机坐标，避免每次都点同一个点
        random_x = random.randint(x, x + w)
        random_y = random.randint(y, y + h)
        print(f"[启动者] 准备点击“开始”按钮区域内的随机点: ({random_x}, {random_y})")
        
        # 移动并点击
        self.executor.human_like_move_to(random_x, random_y, duration=0.5)
        self.executor.click()
        print("[启动者] 已点击开始，等待游戏加载...")