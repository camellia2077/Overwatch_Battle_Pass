import tkinter as tk
import time

class RegionSelector:
    def __init__(self, root):
        self.root = root
        self.start_x = None
        self.start_y = None
        self.rect = None

        # 创建一个全屏的画布
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.canvas = tk.Canvas(root, width=screen_width, height=screen_height, cursor="cross")
        self.canvas.pack()

        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)

        # 最终的区域结果
        self.region = None

    def on_mouse_press(self, event):
        # 记录拖拽的起始点
        self.start_x = event.x
        self.start_y = event.y
        # 创建一个矩形，初始大小为0
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2, fill='blue')

    def on_mouse_drag(self, event):
        # 当鼠标拖动时，实时更新矩形的终点坐标
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_mouse_release(self, event):
        # 当鼠标松开时，记录终点，计算最终区域
        end_x, end_y = (event.x, event.y)
        
        left = min(self.start_x, end_x)
        top = min(self.start_y, end_y)
        width = abs(self.start_x - end_x)
        height = abs(self.start_y - end_y)
        
        self.region = (left, top, width, height)
        # 销毁窗口
        self.root.quit()

# --- 主程序入口 ---
if __name__ == '__main__':
    root = tk.Tk()
    time.sleep(4)
    # --- 配置窗口 ---
    # 隐藏窗口的标题栏和边框
    root.overrideredirect(True)
    # 设置窗口为半透明 (值范围 0.0 到 1.0)
    root.attributes('-alpha', 0.3)
    # 将窗口置于所有其他窗口之上
    root.attributes('-topmost', True)
    
    # 获取屏幕尺寸并设置窗口全屏
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f'{screen_width}x{screen_height}+0+0')

    print("="*40)
    print("      可视化区域选择工具")
    print("="*40)
    print("\n你的屏幕已出现一个半透明覆盖层。")
    print("请直接在屏幕上拖动鼠标左键来选择区域。")
    print("松开鼠标后，程序将自动计算并退出。")

    app = RegionSelector(root)
    # 运行tkinter事件循环
    root.mainloop()

    # 在窗口销毁后，打印结果
    if app.region:
        print("\n" + "="*40)
        print("      计算完成！")
        print("="*40)
        print(f"\n你可以将下面这行代码直接复制到你的主程序中：")
        print(f"MONITOR_REGION = {app.region}")
        print("\n工具已自动退出。")
    else:
        print("\n未能成功选择区域。")
    
    # 彻底退出
    root.destroy()