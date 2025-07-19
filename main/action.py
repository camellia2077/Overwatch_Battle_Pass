# action.py

# ==============================================================================
# 0. 导入所有需要的库
# ==============================================================================
import winsound
import time
import random
import sys
# 从拆分出去的模块中导入我们需要的类
from vision import OCRWatcher
from executors import ActionExecutor, PyAutoGuiExecutor
from workflows import GameExiter, GameStarter

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

def countdown_second(seconds):
    print(f"程序会在{seconds} s后运行,请切换到英雄精通难度选择界面")
    times = 0
    for i in range(seconds,0,-1):
        times += 1
        print(f"倒计时 {i} s")
        factor_frequency = 150
        winsound.Beep(200 + factor_frequency * times, 800)
        time.sleep(1)
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
        sleep_seconds = 5
        countdown_second(sleep_seconds)

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
            
            # 将当前轮次写入num.log文件（'w'模式会覆盖旧内容）
            with open(log_filename, 'w') as f:
                f.write(log_entry)
            
            print(f"\n\n=============== 第 {run_count} 轮流程结束 ===============\n\n")

            # 每运行40轮，就休息60秒
            if run_count > 0 and run_count % 40 == 0:
                print(f"已连续运行 {run_count} 轮，程序将休息 60 秒后开始下一轮...")
                time.sleep(40)
            
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