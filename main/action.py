# action_with_logging_and_comments.py

# ==============================================================================
# 0. 导入所有需要的库
# ==============================================================================
import pyautogui                    # 用于GUI自动化，如移动鼠标、获取屏幕尺寸等（主要用于菜单/UI交互）
import pydirectinput                # 专为游戏设计的输入库，能更好地模拟底层输入，兼容性更强（主要用于游戏内操作）
import time                         # 提供时间相关的功能，如暂停程序(time.sleep)
import random                       # 用于生成随机数，让人机交互看起来更自然
import easyocr                      # 一个强大的OCR库，用于从图片中识别文字
import cv2                          # OpenCV库，用于图像处理，如颜色转换、二值化等，以提高OCR识别率
import numpy as np                  # 用于处理图像数据（OpenCV返回的数据格式）
from difflib import SequenceMatcher # 用于比较两个字符串的相似度
import mss                          # 用于高效截取屏幕，比pyautogui的截图速度快很多
import sys                          # 用于访问系统相关的参数和函数，这里用来重定向标准输出

# ==============================================================================
# 1. 配置常量
# ==============================================================================
# --- OCR 配置 ---
# 定义了需要监控的屏幕区域 (左上角x, 左上角y, 宽度, 高度)
MONITOR_REGION = (895, 1003, 283, 45)  
# 定义了OCR需要识别的目标文字
TARGET_TEXT = "精通科目开启"
# 定义了识别出的文字与目标文字的相似度阈值，高于此值才算成功
SIMILARITY_THRESHOLD = 0.80

# --- 自动化动作配置 ---
# 游戏内灵敏度乘数。因为pydirectinput的moveRel是相对移动，需要一个乘数来匹配游戏内的鼠标灵敏度设置
INGAME_SENSITIVITY_MULTIPLIER = 20.0  

# --- 退出流程配置 ---
# 这是一个列表，定义了退出游戏比赛的步骤。每个步骤包含要查找的按钮文字和搜索区域
EXIT_SEQUENCE_STEPS = [
    {'text': '离开比赛', 'region': (872, 633, 439, 49)},  
    {'text': '确认', 'region': (966, 571, 100, 49)},      
]
# --- 重新开始配置 ---
# 定义了“开始游戏”按钮所在的大致区域，程序会在此区域内随机点击
START_GAME_REGION = (375, 513, 166, 160)


# ==============================================================================
# 1.5. 定义日志记录类
# ==============================================================================
class Logger:
    """
    一个日志记录类，可以将print输出同时发送到控制台和指定的日志文件。
    实现原理是重载 sys.stdout，将所有输出流导向此类的一个实例。
    """
    def __init__(self, filename="output.log"):
        """
        初始化Logger。
        :param filename: 要写入的日志文件名。
        """
        self.terminal = sys.stdout  # 保存原始的stdout（即控制台）
        # 以写入模式('w')打开日志文件，并指定utf-8编码以支持中文
        self.log = open(filename, "w", encoding="utf-8") 
        print(f"日志功能已启动，所有控制台输出将被记录到 {filename}")

    def write(self, message):
        """
        重写write方法，使得调用print时会执行此方法。
        :param message: print函数要输出的内容。
        """
        self.terminal.write(message)  # 首先，在原始控制台打印内容
        self.log.write(message)       # 然后，将相同内容写入日志文件

    def flush(self):
        """
        重写flush方法，这是确保数据写入磁盘所必需的。
        """
        self.terminal.flush()
        self.log.flush()

    def close(self):
        """
        关闭日志文件。
        """
        self.log.close()


# ==============================================================================
# 2. 定义“观察者”类 - 负责识别
# ==============================================================================
class OCRWatcher:
    """
    一个负责监控屏幕特定区域并使用EasyOCR识别文字的类。
    它是整个自动化流程的“眼睛”。
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

    def wait_for_text(self, target_text, monitor_region, retry_interval=1.25):
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

# ==============================================================================
# 3. 定义“执行者”类 - 负责操作
# ==============================================================================
class ActionExecutor:
    """
    游戏内动作执行者。
    使用 pydirectinput 库，它通常比 pyautogui 更适合在全屏游戏内模拟输入。
    """
    def __init__(self, sensitivity_multiplier):
        """
        初始化执行者。
        :param sensitivity_multiplier: 鼠标移动的灵敏度修正值。
        """
        self.multiplier = sensitivity_multiplier

    def human_like_press(self, key):
        """
        模拟人类按下并释放按键的行为，中间有短暂的随机延迟。
        :param key: 要按下的键（例如 'w', 'shift'）。
        """
        pydirectinput.keyDown(key)
        time.sleep(random.uniform(0.06, 0.14)) # 模拟按键按下的时长
        pydirectinput.keyUp(key)
        print(f"[PDI执行者] 模拟人类按下按键: {key}")

    def human_like_move_to(self, target_x, target_y, duration=0.5):
        """
        以类似人类的方式将鼠标移动到绝对屏幕坐标。
        它通过计算相对位移，并应用灵敏度乘数，然后分步移动来实现。
        注意：pydirectinput.moveRel 使用的是相对位移。
        :param target_x: 目标点的X坐标。
        :param target_y: 目标点的Y坐标。
        :param duration: 移动过程的大致持续时间。
        """
        print(f"[PDI执行者] 计划移动到绝对坐标: ({target_x}, {target_y})")
        current_x, current_y = pyautogui.position() # 获取当前鼠标绝对坐标
        # 计算需要移动的原始像素偏移
        raw_offset_x = target_x - current_x
        raw_offset_y = target_y - current_y
        # 应用灵敏度乘数，将屏幕像素偏移转换为游戏内的移动量
        offset_x = raw_offset_x * self.multiplier
        offset_y = raw_offset_y * self.multiplier
        print(f"[PDI执行者] 原始偏移: ({raw_offset_x}, {raw_offset_y}), 应用倍率({self.multiplier}x)后: ({int(offset_x)}, {int(offset_y)})")
        
        # 将总移动分成许多小步，模拟平滑移动
        steps = int(duration / 0.01)
        if steps <= 0: steps = 1
        step_x = offset_x / steps
        step_y = offset_y / steps

        # 循环执行每一步移动
        for i in range(steps):
            # 添加微小的随机抖动，让移动轨迹更像人类
            jitter_x = random.randint(-2, 2)
            jitter_y = random.randint(-2, 2)
            pydirectinput.moveRel(int(step_x + jitter_x), int(step_y + jitter_y), relative=True)
            time.sleep(random.uniform(0.005, 0.015)) # 每一步之间有微小延迟

    def run_action_sequence(self):
        """
        执行一系列预设的游戏内动作。
        """
        print("\n--- [PDI执行者] 开始执行游戏内动作序列 ---")
        # 示例动作：按下shift键
        self.human_like_press('shift')
        time.sleep(random.uniform(0.4, 0.5))
        # 其他被注释掉的动作可以根据需要启用
        print("\n--- [PDI执行者] 游戏内动作序列执行完毕！ ---")

    def click(self):
        """
        执行一次鼠标点击。
        """
        pydirectinput.click()
        print("[PDI执行者] 点击。")

class PyAutoGuiExecutor:
    """
    游戏外（菜单/UI）动作执行者。
    使用 pyautogui 库，它对于标准的窗口和UI界面操作非常可靠。
    """
    def human_like_move_to(self, target_x, target_y, duration=0.5):
        """
        使用pyautogui平滑地移动鼠标到目标坐标。
        :param target_x: 目标X坐标。
        :param target_y: 目标Y坐标。
        :param duration: 移动持续时间。
        """
        # pyautogui.easeOutQuad 是一种缓动函数，使移动开始快，结束慢，更自然
        pyautogui.moveTo(target_x, target_y, duration=duration, tween=pyautogui.easeOutQuad)
        print(f"[GUI执行者] 移动到: ({target_x}, {target_y})")

    def click(self):
        """
        模拟一次非常人性化的点击（按下 -> 短暂等待 -> 弹起）。
        """
        pyautogui.mouseDown()
        time.sleep(random.uniform(0.05, 0.12))
        pyautogui.mouseUp()
        print("[GUI执行者] 执行人性化点击 (MouseDown -> Sleep -> MouseUp)。")

    def human_like_press(self, key):
        """
        使用pyautogui按下并释放一个键。
        :param key: 要按的键。
        """
        pyautogui.press(key)
        print(f"[GUI执行者] 按下按键: {key}")

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
        time.sleep(random.uniform(0.5, 1.0))
        
        # 2. 循环执行预设的点击步骤（例如：点击“离开比赛”，然后点击“确认”）
        for step in self.steps:
            self.find_and_click_button(step['text'], step['region'])
            time.sleep(random.uniform(0.5, 1.0))
            
        # 3. 执行一系列按键来跳过结算画面（这些按键是针对特定游戏设计的）
        print("[退出者] 执行键盘快捷键以跳过结算...")
        time.sleep(random.uniform(0.5, 0.75))
        self.executor.human_like_press('space')
        self.executor.human_like_press('space')
        print("[退出者] 等待结算动画...")
        time.sleep(random.uniform(2.5, 3.5)) 
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


# ==============================================================================
# 6. 主程序入口
# ==============================================================================
if __name__ == '__main__':
    # 将标准输出重定向到我们的Logger类的实例
    # 这会使得所有print的内容都输出到控制台并写入output.log文件
    stdout_logger = Logger("output.log")
    sys.stdout = stdout_logger
    
    original_stdout = sys.stdout # 保存我们自定义的logger
    
    try:
        # --- 1. 初始化所有需要的对象 ---
        # 初始化OCR观察者，传入相似度阈值
        main_watcher = OCRWatcher(similarity_threshold=SIMILARITY_THRESHOLD)
        # 初始化游戏内动作执行者，传入鼠标灵敏度乘数
        ingame_executor = ActionExecutor(sensitivity_multiplier=INGAME_SENSITIVITY_MULTIPLIER)
        # 初始化菜单/UI执行者
        menu_executor = PyAutoGuiExecutor()
        # 初始化游戏退出者，将观察者、UI执行者和退出步骤配置传入
        main_exiter = GameExiter(watcher=main_watcher, executor=menu_executor, steps_config=EXIT_SEQUENCE_STEPS)
        # 初始化游戏启动者，将UI执行者和开始区域配置传入
        main_starter = GameStarter(executor=menu_executor, start_region=START_GAME_REGION)
        
        # --- 2. 准备开始 ---
        print("程序将在5秒后开始......请切换到游戏窗口。")
        time.sleep(5)

        run_count = 0
        log_filename = "num.log" # 这个文件只记录运行轮次

        # --- 3. 主循环 ---
        # 这是一个无限循环，除非用户手动中断（按Ctrl+C）
        while True:
            # 步骤A: 开始新游戏
            main_starter.start_new_game()
            
            # 步骤B: 等待特定文本出现，表示游戏内某个阶段已开始
            main_watcher.wait_for_text(target_text=TARGET_TEXT, monitor_region=MONITOR_REGION)
            
            # 步骤C: 执行游戏内的主要动作
            ingame_executor.run_action_sequence()
            time.sleep(2) # 动作执行后稍作等待
            
            # 步骤D: 执行退出流程
            main_exiter.run_exit_sequence()

            # --- 4. 记录和休息 ---
            run_count += 1
            timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            log_entry = f"{timestamp_str}\t{run_count}"
            
            # 将当前轮次写入num.log文件（注意'w'模式会覆盖旧内容）
            with open(log_filename, 'w') as f:
                f.write(log_entry)
            
            print(f"\n\n=============== 第 {run_count} 轮流程结束 ===============\n\n")

            # 每运行40轮，就休息60秒
            if run_count > 0 and run_count % 40 == 0:
                print(f"已连续运行 {run_count} 轮，程序将休息 60 秒后开始下一轮...")
                time.sleep(60)
            
    except KeyboardInterrupt:
        # 如果用户在控制台按下了 Ctrl+C
        print("\n程序被用户中断。正在退出...")
    except Exception as e:
        # 捕获其他可能的异常并打印
        print(f"\n程序遇到未处理的异常: {e}")
    finally:
        # 无论程序是正常结束、用户中断还是出错，这个块都会执行
        print("正在关闭日志文件并恢复标准输出...")
        # 恢复原始的stdout，并关闭文件句柄
        if isinstance(original_stdout, Logger):
            sys.stdout = original_stdout.terminal
            original_stdout.close()
        print("程序已完全关闭。")