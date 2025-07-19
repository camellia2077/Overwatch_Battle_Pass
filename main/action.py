# 导入所有需要的库
import pyautogui
import pydirectinput
import time
import random
import easyocr
import cv2  # OpenCV
import numpy as np
from difflib import SequenceMatcher
import mss # 导入mss

# ==============================================================================
# 1. 配置常量 
# ==============================================================================
# --- OCR 配置 ---
MONITOR_REGION = (895, 1003, 283, 45)  
TARGET_TEXT = "精通科目开启"
SIMILARITY_THRESHOLD = 0.80

# --- 自动化动作配置 ---
INGAME_SENSITIVITY_MULTIPLIER = 20.0  

# --- 退出流程配置 ---
EXIT_SEQUENCE_STEPS = [
    {'text': '离开比赛', 'region': (872, 633, 439, 49)},  
    {'text': '确认', 'region': (966, 571, 100, 49)},      
]
# --- 重新开始配置 ---
START_GAME_REGION = (375, 513, 166, 160)


# ==============================================================================
# 2. 定义“观察者”类 - 负责识别 
# ==============================================================================
class OCRWatcher:
    """一个负责监控屏幕特定区域并识别文字的类 。"""
    def __init__(self, similarity_threshold=0.8):
        self.threshold = similarity_threshold
        print("正在初始化 OCR 引擎 (首次运行可能需要下载模型)...")
        self.reader = easyocr.Reader(['ch_sim', 'en'])
        self.sct = mss.mss() # 初始化mss
        print("OCR 引擎准备就绪。")

    def read_text_from_region(self, region):
        """从指定区域截图并识别文字（可复用的核心功能）。"""
        monitor = {"top": region[1], "left": region[0], "width": region[2], "height": region[3]}
        sct_img = self.sct.grab(monitor)
        frame = np.array(sct_img)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGRA2GRAY)
        _, threshold_img = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
        # 返回详细结果，供不同场景使用
        return self.reader.readtext(threshold_img) 

    def wait_for_text(self, target_text, monitor_region, retry_interval=1.25): # 检测间隔
        print(f"\n[观察者] 开始监控屏幕区域 {monitor_region}...")
        print(f"等待检测到文字与 '{target_text}' 的相似度高于 {self.threshold*100}%")
        while True:
            # 调用复用函数，只获取文字
            ocr_results = self.read_text_from_region(monitor_region)
            detected_text = "".join([res[1] for res in ocr_results]).replace(" ", "")
            
            similarity = SequenceMatcher(None, target_text, detected_text).ratio()
            if similarity >= self.threshold:
                print(f"\n[观察者] 成功! 检测到 '{detected_text}' (相似度 {similarity:.2f})")
                break
            else:
                if detected_text:
                    print(f"[观察者] 未达标... 当前识别: '{detected_text}' (相似度 {similarity:.2f}, {retry_interval}秒后重试)")
                else:
                    print(f"[观察者] 未检测到任何文字... ({retry_interval}秒后重试)")
                time.sleep(retry_interval)

# ==============================================================================
# 3. 定义“执行者”类 
# ==============================================================================
class ActionExecutor:
    # 游戏内执行
    def __init__(self, sensitivity_multiplier):
        self.multiplier = sensitivity_multiplier
    def human_like_press(self, key):
        pydirectinput.keyDown(key)
        time.sleep(random.uniform(0.06, 0.14))
        pydirectinput.keyUp(key)
        print(f"[PDI执行者] 模拟人类按下按键: {key}")
    def human_like_move_to(self, target_x, target_y, duration=0.5):
        print(f"[PDI执行者] 计划移动到绝对坐标: ({target_x}, {target_y})")
        current_x, current_y = pyautogui.position()
        raw_offset_x = target_x - current_x
        raw_offset_y = target_y - current_y
        offset_x = raw_offset_x * self.multiplier
        offset_y = raw_offset_y * self.multiplier
        print(f"[PDI执行者] 原始偏移: ({raw_offset_x}, {raw_offset_y}), 应用倍率({self.multiplier}x)后: ({int(offset_x)}, {int(offset_y)})")
        steps = int(duration / 0.01)
        if steps <= 0: steps = 1
        step_x = offset_x / steps
        step_y = offset_y / steps
        for i in range(steps):
            jitter_x = random.randint(-2, 2)
            jitter_y = random.randint(-2, 2)
            pydirectinput.moveRel(int(step_x + jitter_x), int(step_y + jitter_y), relative=True)
            time.sleep(random.uniform(0.005, 0.015))
    def run_action_sequence(self):
        print("\n--- [PDI执行者] 开始执行游戏内动作序列 ---")
        #time.sleep(0.5)
        self.human_like_press('shift')
        time.sleep(random.uniform(0.4, 0.5))
        #move_distance = random.randint(190, 210)
        #direction = random.choice([-1, 1])
        #direction_text = "向左" if direction == -1 else "向右"
        #print(f"[PDI执行者] 计算{direction_text}移动 {move_distance} 像素的目标位置...")
        #current_pos = pyautogui.position()
        #target_x = current_pos.x + (move_distance * direction)
        #target_y = current_pos.y
        #self.human_like_move_to(target_x, target_y, duration=0.5)
        #time.sleep(random.uniform(0.3, 0.5))
        #self.human_like_press('e')
        print("\n--- [PDI执行者] 游戏内动作序列执行完毕！ ---")
    def click(self):
        pydirectinput.click()
        print("[PDI执行者] 点击。")
class PyAutoGuiExecutor:
    # 游戏ui执行
    def human_like_move_to(self, target_x, target_y, duration=0.5):
        pyautogui.moveTo(target_x, target_y, duration=duration, tween=pyautogui.easeOutQuad)
        print(f"[GUI执行者] 移动到: ({target_x}, {target_y})")
    def click(self):
        pyautogui.mouseDown()
        time.sleep(random.uniform(0.05, 0.12))
        pyautogui.mouseUp()
        print("[GUI执行者] 执行人性化点击 (MouseDown -> Sleep -> MouseUp)。")
    def human_like_press(self, key):
        pyautogui.press(key)
        print(f"[GUI执行者] 按下按键: {key}")

# ==============================================================================
# 4. “退出者”类
# ==============================================================================
class GameExiter:
    """负责执行退出流程的类。"""
    def __init__(self, watcher, executor, steps_config):
        self.watcher = watcher 
        self.executor = executor
        self.steps = steps_config

    def find_and_click_button(self, text_to_find, region, timeout=5):
        print(f"[退出者] 正在寻找按钮 '{text_to_find}'...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 直接调用 watcher 的通用识别方法
            ocr_results = self.watcher.read_text_from_region(region)
            
            for (bbox, text, prob) in ocr_results:
                if text_to_find in text.replace(" ", ""):
                    print(f"[退出者] 找到按钮 '{text}' (置信度: {prob:.2f})! 准备精确点击。")
                    top_left = bbox[0]
                    bottom_right = bbox[2]
                    center_x_relative = (top_left[0] + bottom_right[0]) / 2
                    center_y_relative = (top_left[1] + bottom_right[1]) / 2
                    region_x, region_y, _, _ = region
                    absolute_center_x = int(region_x + center_x_relative)
                    absolute_center_y = int(region_y + center_y_relative)
                    self.executor.human_like_move_to(absolute_center_x, absolute_center_y, duration=0.3)
                    self.executor.click()
                    return True
            time.sleep(1)
        print(f"[退出者] 警告：在 {timeout} 秒内未找到按钮 '{text_to_find}'。")
        return False

    def run_exit_sequence(self):
        print("\n--- [退出者] 开始执行退出流程 ---")
        self.executor.human_like_press('esc')
        time.sleep(random.uniform(0.5, 1.0))
        for step in self.steps:
            self.find_and_click_button(step['text'], step['region'])
            time.sleep(random.uniform(0.5, 1.0))
        print("[退出者] 执行键盘快捷键以跳过结算...")
        time.sleep(random.uniform(0.5, 0.75))
        self.executor.human_like_press('space')
        self.executor.human_like_press('space')
        print("[退出者] 等待结算动画...")
        time.sleep(random.uniform(2.5, 3.5)) 
        print("[退出者] 按下方向键'下'以重新聚焦按钮...")
        time.sleep(random.uniform(0.2, 0.4)) 
        self.executor.human_like_press('space')
        self.executor.human_like_press('space')
        self.executor.human_like_press('space')
        print("\n--- [退出者] 退出流程执行完毕！---")

# ==============================================================================
# 5. “启动者”类 (无任何变化)
# ==============================================================================
class GameStarter:
    def __init__(self, executor, start_region):
        self.executor = executor
        self.start_region = start_region
    def start_new_game(self):
        print("\n--- [启动者] 开始新一轮游戏 ---")
        x, y, w, h = self.start_region
        random_x = random.randint(x, x + w)
        random_y = random.randint(y, y + h)
        print(f"[启动者] 准备点击“开始”按钮区域内的随机点: ({random_x}, {random_y})")
        self.executor.human_like_move_to(random_x, random_y, duration=0.5)
        self.executor.click()
        print("[启动者] 已点击开始，等待游戏加载...")


# ==============================================================================
# 6. 主程序入口
# ==============================================================================
if __name__ == '__main__':
    main_watcher = OCRWatcher(similarity_threshold=SIMILARITY_THRESHOLD)
    ingame_executor = ActionExecutor(sensitivity_multiplier=INGAME_SENSITIVITY_MULTIPLIER)
    menu_executor = PyAutoGuiExecutor()
    main_exiter = GameExiter(watcher=main_watcher, executor=menu_executor, steps_config=EXIT_SEQUENCE_STEPS)
    main_starter = GameStarter(executor=menu_executor, start_region=START_GAME_REGION)
    
    print("Program will start in 5 seconds......")
    time.sleep(5)

    run_count = 0
    log_filename = "num.log"

    try:
        while True:
            main_starter.start_new_game()
            # 调用 watcher 时传入具体参数
            main_watcher.wait_for_text(target_text=TARGET_TEXT, monitor_region=MONITOR_REGION)
            
            ingame_executor.run_action_sequence()
            time.sleep(2)
            
            main_exiter.run_exit_sequence()

            run_count += 1
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            log_entry = f"{timestamp_str}\t{run_count}"
            with open(log_filename, 'w') as f:
                f.write(log_entry)
            
            print(f"\n\n=============== 第 {run_count} 轮流程结束 ===============\n\n")

            if run_count % 40 == 0:
                print(f"已连续运行 {run_count} 轮，程序将休息 60 秒后开始下一轮...")
                time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n程序被用户中断。正在退出...")