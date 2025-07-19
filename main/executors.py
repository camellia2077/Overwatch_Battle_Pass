# executors.py

import pyautogui
import pydirectinput
import time
import random

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
        :param key: 要按下的键（例如 'shift'）。
        """
        pydirectinput.keyDown(key)
        time.sleep(random.uniform(0.2, 0.3)) # 模拟按键按下的时长
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
    def human_like_move_to(self, target_x, target_y, duration=0.15):
        """
        使用pyautogui平滑地移动鼠标到目标坐标。
        :param target_x: 目标X坐标。
        :param target_y: 目标Y坐标。
        :param duration: 鼠标移动持续时间。
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