"""
# 模板代码，复制即用
from SnakeFramework import *

# 创建窗口
screen = Screen(800, 600, title="我的游戏", fps=60)

# 定义游戏循环函数
def handle_event(event):
    pass

def update(dt):
    pass

def draw(win):
    win.fill((0, 0, 0))

# 启动游戏
screen.run(handle_event, update, draw)
"""

import os
import time
from datetime import datetime
import pygame
import random
import cv2
import numpy as np
from moviepy import VideoFileClip

# 资源目录路径
IMAGE_PATH = "assets/images/"
MUSIC_PATH = "assets/music/"
SOUND_PATH = "assets/sounds/"


class Input:
    """全局输入状态，由 Screen 每帧自动更新
    用法:
        Input.mouse_pos       → (x, y)
        Input.mouse_left      → 当前帧左键刚按下
        Input.mouse_right     → 当前帧右键刚按下
        Input.mouse_released  → 当前帧鼠标刚释放
        Input.key_pressed(k)  → 当前帧某个键刚按下
        Input.key_held(k)     → 某个键是否按住
        Input.key_released(k) → 当前帧某个键刚释放
    """
    mouse_x = 0
    mouse_y = 0
    mouse_left = False
    mouse_right = False
    mouse_released = False
    _keys_held = set()
    _keys_pressed = set()
    _keys_released = set()

    @classmethod
    def mouse_pos(cls):
        return cls.mouse_x, cls.mouse_y

    @classmethod
    def key_pressed(cls, key):
        return key in cls._keys_pressed

    @classmethod
    def key_held(cls, key):
        return key in cls._keys_held

    @classmethod
    def key_released(cls, key):
        return key in cls._keys_released

    @classmethod
    def _reset_frame(cls):
        """每帧开始前重置瞬时状态"""
        cls.mouse_left = False
        cls.mouse_right = False
        cls.mouse_released = False
        cls._keys_pressed.clear()
        cls._keys_released.clear()

    @classmethod
    def _handle_event(cls, event):
        """根据事件更新输入状态"""
        if event.type == pygame.MOUSEMOTION:
            cls.mouse_x, cls.mouse_y = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN:
            cls.mouse_x, cls.mouse_y = event.pos
            if event.button == 1:
                cls.mouse_left = True
            elif event.button == 3:
                cls.mouse_right = True
        elif event.type == pygame.MOUSEBUTTONUP:
            cls.mouse_released = True
        elif event.type == pygame.KEYDOWN:
            cls._keys_held.add(event.key)
            cls._keys_pressed.add(event.key)
        elif event.type == pygame.KEYUP:
            cls._keys_held.discard(event.key)
            cls._keys_released.add(event.key)


class Music:
    """背景音乐管理

    用法:
        Music.play("assets/bgm.mp3", volume=0.5, loop=-1)
        Music.pause()
        Music.resume()
        Music.stop()
    """

    _initialized = False

    @classmethod
    def _init(cls):
        if not cls._initialized:
            pygame.mixer.init()
            cls._initialized = True

    @classmethod
    def play(cls, filepath, volume=1.0, loop=-1):
        cls._init()
        pygame.mixer.music.load(filepath)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loop)

    @classmethod
    def pause(cls):
        pygame.mixer.music.pause()

    @classmethod
    def resume(cls):
        pygame.mixer.music.unpause()

    @classmethod
    def stop(cls):
        pygame.mixer.music.stop()

    @classmethod
    def set_volume(cls, volume):
        pygame.mixer.music.set_volume(volume)


class Sound:
    """音效管理

    用法:
        sfx = Sound("assets/click.wav", volume=0.8)
        sfx.play()
    """

    def __init__(self, filepath, volume=1.0):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        self._sound = pygame.mixer.Sound(filepath)
        self._sound.set_volume(volume)

    def play(self):
        self._sound.play()

    def set_volume(self, volume):
        self._sound.set_volume(volume)


class Sprite(pygame.sprite.Sprite):
    """精灵基类 —— 封装了 pygame 精灵的常用功能，支持动画

    用法:
        # 1. 传图片路径（字符串）
        plane = Sprite("assets/plane.png")
        plane = Sprite("assets/plane.png", x=100, y=200)

        # 2. 传 Surface 对象
        surf = pygame.Surface((32, 32))
        box = Sprite(surf, x=50, y=50)

        # 3. 只指定宽高（创建空白画布）
        placeholder = Sprite(width=64, height=64)

        # 4. 动画用法
        plane.setAnim("run", 30, ["run1.png", "run2.png", "run3.png"])
        plane.play("run", loop=True)
    """

    def __init__(self, image=None, x=0, y=0, width=0, height=0, color=None):
        super().__init__()
        # 第1种：传字符串 → 作为图片路径加载
        if isinstance(image, str):
            img = pygame.image.load(image)
            self.image = img.convert_alpha() if pygame.display.get_init() else img
        # 第2种：传 Surface 对象 → 直接使用
        elif image is not None:
            self.image = image
        # 第3种：都不传 → 根据 width/height 创建画布
        else:
            self.image = pygame.Surface((width, height), pygame.SRCALPHA)
        if color:
            self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self._left_click_callback = None
        self._right_click_callback = None
        self._hover_callback = None
        self._was_hovered = False

        # ==================== 动画属性 ====================
        self.current_anim = None  # 当前播放的动画名
        self.current_frame = 0  # 当前帧索引
        self.frame_counter = 0  # 帧计数器
        self.anim_data = {}  # {动画名: {"frames": [Surface], "total_frames": int, "frames_per_img": int}}
        self.play_loop = False  # 是否循环播放
        self.paused = False  # 暂停状态

    def on_left_click(self, callback):
        """绑定左键点击回调：左键按下且命中精灵时执行 callback()"""
        self._left_click_callback = callback

    def on_right_click(self, callback):
        """绑定右键点击回调：右键按下且命中精灵时执行 callback()"""
        self._right_click_callback = callback

    def on_mouse(self, callback):
        """绑定鼠标悬停回调：鼠标在精灵上时每帧执行 callback()"""
        self._hover_callback = callback

    # ==================== 位置 ====================
    @property
    def x(self):
        return self.rect.x

    @x.setter
    def x(self, value):
        self.rect.x = value

    @property
    def y(self):
        return self.rect.y

    @y.setter
    def y(self, value):
        self.rect.y = value

    @property
    def position(self):
        return self.rect.topleft

    @position.setter
    def position(self, value):
        self.rect.topleft = value

    @property
    def center(self):
        return self.rect.center

    @center.setter
    def center(self, value):
        self.rect.center = value

    # ==================== 尺寸 ====================
    @property
    def width(self):
        return self.rect.width

    @property
    def height(self):
        return self.rect.height

    @property
    def w(self):
        return self.rect.width

    @property
    def h(self):
        return self.rect.height

    @property
    def size(self):
        return self.rect.size

    # ==================== 碰撞检测 ====================
    def collides_with(self, other):
        """检测是否与另一个精灵碰撞（矩形碰撞）"""
        return self.rect.colliderect(other.rect)

    def contains_point(self, point):
        """检测一个点是否在精灵矩形内"""
        return self.rect.collidepoint(point)

    def contains_point_alpha(self, point):
        """像素级碰撞：检测点是否命中精灵的非透明像素"""
        if not self.rect.collidepoint(point):
            return False
        # 将屏幕坐标转换为精灵图片内的局部坐标
        local_x = point[0] - self.rect.x
        local_y = point[1] - self.rect.y
        # 检查该像素的 alpha 通道（不在图片范围内返回 False）
        if 0 <= local_x < self.rect.width and 0 <= local_y < self.rect.height:
            return self.image.get_at((local_x, local_y)).a > 0
        return False

    # ==================== 移动 ====================
    def move(self, dx, dy):
        """移动精灵"""
        self.rect.x += dx
        self.rect.y += dy

    def move_to(self, x, y):
        """移动到指定位置"""
        self.rect.topleft = (x, y)

    # ==================== 动画方法 ====================

    def setAnim(self, anim_name, total_frames, frame_paths):
        """
        设置动画，自动加载图片为 Surface 对象

        参数:
            anim_name: 动画名（字符串）
            total_frames: 总时长（帧数）
            frame_paths: 图片路径列表

        说明:
            - 总帧数平均分配到每张图片
            - 图片预加载，转为 Surface 存储
            - 建议所有图片统一尺寸，否则可能拉伸或裁剪
        """
        if not frame_paths:
            return

        # 加载所有图片
        frames = []
        for path in frame_paths:
            try:
                img = pygame.image.load(path)
                # 如果显示已初始化，转换 alpha 通道
                if pygame.display.get_init():
                    img = img.convert_alpha()
                frames.append(img)
            except pygame.error as e:
                print(f"[Sprite] 加载图片失败: {path}, 错误: {e}")
                # 如果加载失败，创建一个占位 Surface
                placeholder = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
                placeholder.fill((255, 0, 255, 128))  # 半透明紫色作为占位
                frames.append(placeholder)

        # 计算每张图片的帧数
        frames_per_img = total_frames // len(frames)
        if frames_per_img == 0:
            frames_per_img = 1  # 至少每张图片显示1帧

        self.anim_data[anim_name] = {
            "frames": frames,
            "total_frames": total_frames,
            "frames_per_img": frames_per_img
        }

    def play(self, anim_name, loop=False):
        """
        播放动画

        参数:
            anim_name: 动画名
            loop: 是否循环播放（默认 False）

        说明:
            - 重置帧计数器，从头播放
            - 自动重置暂停状态
            - 如果播放新动画，旧动画自动停止
        """
        if anim_name not in self.anim_data:
            print(f"[Sprite] 动画 '{anim_name}' 不存在")
            return

        # 重置状态
        self.current_anim = anim_name
        self.current_frame = 0
        self.frame_counter = 0
        self.play_loop = loop
        self.paused = False

        # 立即显示第一帧
        anim = self.anim_data[anim_name]
        self.image = anim["frames"][0]

    def stop(self):
        """停止当前动画，停留在当前帧（不重置显示）"""
        self.current_anim = None
        self.current_frame = 0
        self.frame_counter = 0
        self.play_loop = False
        self.paused = False

    def pause(self):
        """暂停播放"""
        if self.current_anim is not None:
            self.paused = True

    def resume(self):
        """恢复播放"""
        if self.current_anim is not None:
            self.paused = False

    def is_playing(self):
        """是否正在播放动画"""
        return self.current_anim is not None and not self.paused

    def get_now_anim_name(self):
        """获取当前播放的动画名"""
        return self.current_anim

    def remove_anim(self, anim_name):
        """移除指定动画，如果当前正在播放该动画则自动停止"""
        if anim_name in self.anim_data:
            if self.current_anim == anim_name:
                self.stop()
            del self.anim_data[anim_name]

    def clear_anims(self):
        """清除所有动画，如果正在播放则自动停止"""
        if self.current_anim is not None:
            self.stop()
        self.anim_data.clear()

    def get_anim_list(self):
        """获取所有动画名列表"""
        return list(self.anim_data.keys())

    # ==================== 内部动画更新 ====================

    def _update_animation(self):
        """内部方法：推进动画帧"""
        # 检查是否在播放状态
        if self.current_anim is None or self.paused:
            return

        anim = self.anim_data.get(self.current_anim)
        if anim is None:
            self.stop()
            return

        frames = anim["frames"]
        frames_per_img = anim["frames_per_img"]

        # 推进帧计数器
        self.frame_counter += 1

        # 计算当前应该显示哪一张图片
        img_index = self.frame_counter // frames_per_img

        # 检查是否到达末尾
        if img_index >= len(frames):
            if self.play_loop:
                # 循环模式：重置计数器
                self.frame_counter = 0
                img_index = 0
            else:
                # 非循环模式：停止播放，停留在最后一帧
                self.current_anim = None
                self.current_frame = len(frames) - 1
                return

        # 更新当前帧和显示的图片
        self.current_frame = img_index
        self.image = frames[img_index]

    # ==================== 更新 & 绘制 ====================
    def update(self, dt=0):
        """每帧更新：自动推进动画 + 检测左键、右键、悬停回调"""
        # 1. 推进动画
        self._update_animation()

        # 2. 鼠标事件检测
        hovered = self.contains_point_alpha(Input.mouse_pos())

        if self._left_click_callback and Input.mouse_left and hovered:
            self._left_click_callback()
        if self._right_click_callback and Input.mouse_right and hovered:
            self._right_click_callback()
        if self._hover_callback and hovered:
            self._hover_callback()

        self._was_hovered = hovered

    def draw(self, screen):
        """将精灵绘制到屏幕上"""
        screen.blit(self.image, self.rect)


class Text:
    """文字渲染 —— 简化字体操作

    用法:
        score_text = Text("Score: 0", x=10, y=10, font_size=32, color=(255, 255, 255))
        score_text.draw(screen)

        # 更新文字内容
        score_text.set_text("Score: 100")

        # 使用系统字体
        Text("你好", x=100, y=100, font_size=24, font_path="C:/Windows/Fonts/msyh.ttc")
    """

    def __init__(self, text="", x=0, y=0, font_size=24, color=(255, 255, 255), font_path="C:/Windows/Fonts/msyh.ttc"):
        if not pygame.font.get_init():
            pygame.font.init()
        self._text = text
        self.x = x
        self.y = y
        self.font_size = font_size
        self.color = color
        self._font = pygame.font.Font(font_path, font_size)
        self._surface = None
        self._left_click_callback = None
        self._right_click_callback = None
        self._hover_callback = None
        self._render()

    def _render(self):
        self._surface = self._font.render(self._text, True, self.color)

    @property
    def text(self):
        return self._text

    def set_text(self, text):
        """更新文字内容"""
        self._text = text
        self._render()

    def on_left_click(self, callback):
        """绑定左键点击回调：左键按下且命中文字时执行 callback()"""
        self._left_click_callback = callback

    def on_right_click(self, callback):
        """绑定右键点击回调：右键按下且命中文字时执行 callback()"""
        self._right_click_callback = callback

    def on_mouse(self, callback):
        """绑定鼠标悬停回调：鼠标在文字上时每帧执行 callback()"""
        self._hover_callback = callback

    def contains_point(self, point):
        """检测一个点是否在文字矩形内"""
        x, y = point
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

    @property
    def width(self):
        return self._surface.get_width()

    @property
    def height(self):
        return self._surface.get_height()

    @property
    def w(self):
        return self._surface.get_width()

    @property
    def h(self):
        return self._surface.get_height()

    def move(self, dx, dy):
        """相对移动"""
        self.x += dx
        self.y += dy

    def move_to(self, x, y):
        """移动到指定位置"""
        self.x = x
        self.y = y

    def update(self, dt=0):
        """每帧更新：自动检测左键、右键、悬停回调"""
        hovered = self.contains_point(Input.mouse_pos())

        if self._left_click_callback and Input.mouse_left and hovered:
            self._left_click_callback()
        if self._right_click_callback and Input.mouse_right and hovered:
            self._right_click_callback()
        if self._hover_callback and hovered:
            self._hover_callback()

    def draw(self, screen):
        """绘制文字到屏幕"""
        screen.blit(self._surface, (self.x, self.y))


class Screen:
    """游戏窗口 —— 封装窗口创建与主循环

    用法1（函数式）:
        def handle_event(event):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                screen.running = False

        def update(dt):
            pass

        def draw(win):
            win.fill((0, 0, 0))

        screen = Screen(800, 600, title="我的游戏", fps=60)
        screen.run(handle_event, update, draw)

    用法2（面向对象）:
        class MyGame(Screen):
            def on_event(self, event): ...
            def on_update(self, dt): ...
            def on_draw(self): ...

        MyGame(800, 600).run()
    """

    def __init__(self, width, height, title="Pygame Screen", fps=60, full=False):
        pygame.init()
        self.width = width
        self.height = height
        if full:
            self.win = pygame.display.set_mode((width, height), flags=pygame.FULLSCREEN)
        else:
            self.win = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.running = True
        self._setup_log()
        self._init_assets_dirs()

    def _setup_log(self):
        """初始化日志文件：不存在则创建，存在则追加分隔线"""
        if os.path.exists(Utils.LOG_FILE):
            Utils.log_info(f"\n{'=' * 50}\n游戏启动\n{'=' * 50}")
        else:
            with open(Utils.LOG_FILE, "w", encoding="utf-8") as f:
                f.write(f"[{Utils._get_timestamp()}] 日志文件创建\n")

    def _init_assets_dirs(self):
        """初始化资源目录：缺少哪个创建哪个"""
        for path in (IMAGE_PATH, MUSIC_PATH, SOUND_PATH):
            os.makedirs(path, exist_ok=True)

    def on_event(self, event):
        """子类重写：处理事件（每帧每个事件触发一次）"""

    def on_update(self, dt):
        """子类重写：每帧更新逻辑，dt 为帧间隔（秒）"""

    def on_draw(self):
        """子类重写：每帧绘制逻辑"""

    def quit(self):
        """退出游戏"""
        self.running = False

    def run(self, on_event=None, on_update=None, on_draw=None):
        """启动主循环。
        可传入三个回调函数（函数式），不传则走子类重写（面向对象）。
        """
        while self.running:
            tick_ms = self.clock.tick(self.fps)
            dt = tick_ms / 1000.0

            # 检测帧率：低于 55 帧写入 warning 日志
            if tick_ms > 0:
                actual_fps = 1000.0 / tick_ms
                if actual_fps < 55:
                    self._log_warning(actual_fps)

            # 每帧开始：重置 Input 瞬时状态，收集事件
            Input._reset_frame()
            events = pygame.event.get()
            for event in events:
                Input._handle_event(event)

            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                if on_event:
                    on_event(event)
                else:
                    self.on_event(event)
            if on_update:
                on_update(dt)
            else:
                self.on_update(dt)
            if on_draw:
                on_draw(self.win)
            else:
                self.on_draw()
            pygame.display.flip()
        pygame.quit()

    def _log_warning(self, actual_fps):
        """写入帧率警告"""
        Utils.log_warning(f"帧率过低: {actual_fps:.1f} FPS")


class Utils:
    """通用工具类 —— 存放常用静态方法"""

    @staticmethod
    def chance(percent=100):
        """
        随机概率判断

        参数:
            percent: 1-100 的整数，表示概率百分比，默认 100

        返回:
            True: 随机数 <= percent（事件发生）
            False: 随机数 > percent（事件不发生）

        用法:
            if Utils.chance(30):   # 30% 概率触发
                print("暴击！")

            if Utils.chance():     # 100% 概率触发（总是执行）
                print("总是执行")
        """
        # 参数校验：确保在 1-100 范围内
        if percent < 1:
            percent = 1
        elif percent > 100:
            percent = 100

        return random.randint(1, 100) <= percent

    @staticmethod
    def hide_mouse(visible: bool):
        """
        设置鼠标光标是否可见

        参数:
            visible: True 隐藏鼠标，False 显示鼠标

        用法:
            Utils.hide_mouse(True)      # 隐藏鼠标
            Utils.hide_mouse(False)     # 显示鼠标
        """
        pygame.mouse.set_visible(not visible)

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        """
        将十六进制颜色字符串转为RGB元组
        :param hex_color: 颜色字符串，支持 #fff / #ffffff 格式
        :return: (red, green, blue) 0-255 整数元组
        """
        # 去除开头#号
        hex_str = hex_color.lstrip("#")

        # 处理3位简写 #abc → aabbcc
        if len(hex_str) == 3:
            hex_str = "".join(ch * 2 for ch in hex_str)
        elif len(hex_str) != 6:
            raise ValueError("十六进制颜色格式错误，请使用 #fff 或 #ffffff")

        # 分段截取红、绿、蓝
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)

        return (r, g, b)

    # ==================== 日志 ====================

    LOG_FILE = "console.log"

    @staticmethod
    def _get_timestamp():
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def log_info(message):
        """
        写入 info 级别日志

        参数:
            message: 日志内容

        用法:
            Utils.log_info("游戏启动")
        """
        ts = Utils._get_timestamp()
        with open(Utils.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] INFO {message}\n")

    @staticmethod
    def log_warning(message):
        """
        写入 warning 级别日志

        参数:
            message: 日志内容

        用法:
            Utils.log_warning("帧率过低: 45.2 FPS")
        """
        ts = Utils._get_timestamp()
        with open(Utils.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] WARNING {message}\n")

    @staticmethod
    def log_error(message):
        """
        写入 error 级别日志

        参数:
            message: 日志内容

        用法:
            Utils.log_error("资源加载失败: assets/images/hero.png")
        """
        ts = Utils._get_timestamp()
        with open(Utils.LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] ERROR {message}\n")


# ==================== Scene 场景类 ====================

class Scene:
    """
    场景容器 —— 作为一个独立的游戏场景，包含自己的精灵、文本、逻辑和背景

    用法（面向过程风格）:
        # 1. 创建场景
        menu_scene = Scene("menu")

        # 2. 添加精灵/文本
        title = Text("主菜单", x=100, y=50, font_size=48)
        menu_scene.add_text(title)

        start_btn = Sprite("start.png", x=150, y=200)
        start_btn.on_left_click(lambda: manager.switch_to("game"))
        menu_scene.add_sprite(start_btn)

        # 3. 设置更新/绘制/事件回调（可选）
        def menu_update(dt):
            # 每帧执行的自定义逻辑
            pass
        menu_scene.on_update = menu_update

        # 4. 注册到管理器
        manager.register_scene(menu_scene)
        manager.switch_to("menu")
    """

    def __init__(self, name, bg_image=None, bg_color=(0, 0, 0), bg_music=None):
        """
        参数:
            name: 场景名称（唯一标识）
            bg_image: 背景图片路径（可选）
            bg_color: 背景颜色，默认黑色（如果没设置背景图则使用）
            bg_music: 背景音乐路径（可选，进入场景时自动播放）
        """
        self.name = name
        self.bg_color = bg_color
        self.bg_music = bg_music
        self.bg_sprite = None

        # 如果传入了背景图，创建背景精灵
        if bg_image:
            self.bg_sprite = Sprite(bg_image)

        # 场景中的元素
        self.sprites = pygame.sprite.Group()
        self.texts = []
        self._custom_sprites = []  # 用于存储非 Sprite 对象的引用（如字典形式的精灵）

        # 自定义回调（用户可覆盖）
        self.on_enter = None  # 进入场景时执行
        self.on_exit = None  # 退出场景时执行
        self.on_event = None  # 事件处理
        self.on_update = None  # 更新逻辑（会自动调用精灵和文本的update）
        self.on_draw = None  # 绘制逻辑（会自动绘制精灵和文本）

        # 内部状态
        self.manager = None  # 由 SceneManager 设置
        self._entered = False  # 是否已进入

    # ==================== 添加元素 ====================

    def add_sprite(self, sprite):
        """
        添加精灵到场景

        参数:
            sprite: Sprite 对象

        返回:
            sprite 本身（支持链式调用）
        """
        self.sprites.add(sprite)
        return sprite

    def add_text(self, text):
        """
        添加文本到场景

        参数:
            text: Text 对象

        返回:
            text 本身（支持链式调用）
        """
        self.texts.append(text)
        return text

    def add_sprites(self, *sprites):
        """
        批量添加精灵

        参数:
            *sprites: 多个 Sprite 对象

        返回:
            self（支持链式调用）
        """
        for s in sprites:
            self.sprites.add(s)
        return self

    def add_texts(self, *texts):
        """
        批量添加文本

        参数:
            *texts: 多个 Text 对象

        返回:
            self（支持链式调用）
        """
        for t in texts:
            self.texts.append(t)
        return self

    def add_custom_sprite(self, sprite_data):
        """
        添加自定义精灵数据（非 Sprite 对象）
        用于：存储字典形式的精灵数据，需要用户自己管理绘制

        参数:
            sprite_data: 任意对象（字典、列表等）

        返回:
            sprite_data 本身
        """
        self._custom_sprites.append(sprite_data)
        return sprite_data

    def remove_sprite(self, sprite):
        """
        从场景中移除精灵

        参数:
            sprite: Sprite 对象
        """
        self.sprites.remove(sprite)

    def remove_text(self, text):
        """
        从场景中移除文本

        参数:
            text: Text 对象
        """
        if text in self.texts:
            self.texts.remove(text)

    def remove_custom_sprite(self, sprite_data):
        """
        移除自定义精灵数据

        参数:
            sprite_data: 要移除的数据对象
        """
        if sprite_data in self._custom_sprites:
            self._custom_sprites.remove(sprite_data)

    def clear(self):
        """清空场景中的所有元素"""
        self.sprites.empty()
        self.texts.clear()
        self._custom_sprites.clear()

    # ==================== 查找元素 ====================

    def find_sprite_by_position(self, x, y):
        """
        根据坐标查找精灵

        参数:
            x, y: 坐标位置

        返回:
            Sprite 对象 或 None
        """
        for sprite in self.sprites:
            if sprite.contains_point((x, y)):
                return sprite
        return None

    def find_text_by_position(self, x, y):
        """
        根据坐标查找文本

        参数:
            x, y: 坐标位置

        返回:
            Text 对象 或 None
        """
        for text in self.texts:
            if text.contains_point((x, y)):
                return text
        return None

    def get_sprites(self):
        """获取所有精灵（返回迭代器）"""
        return self.sprites.sprites()

    def get_texts(self):
        """获取所有文本"""
        return self.texts.copy()

    # ==================== 生命周期（由 SceneManager 调用） ====================

    def _do_enter(self):
        """内部：执行进入场景"""
        # 播放背景音乐
        if self.bg_music:
            Music.play(self.bg_music, loop=-1)

        if self.on_enter:
            self.on_enter()

        self._entered = True

    def _do_exit(self):
        """内部：执行退出场景"""
        if self.on_exit:
            self.on_exit()

        self._entered = False

    def _do_event(self, event):
        """内部：执行事件处理"""
        # 先执行用户自定义的事件处理
        if self.on_event:
            self.on_event(event)

    def _do_update(self, dt):
        """内部：执行更新"""
        # 更新所有精灵
        self.sprites.update(dt)
        # 更新所有文本
        for text in self.texts:
            text.update(dt)
        # 用户自定义更新
        if self.on_update:
            self.on_update(dt)

    def _do_draw(self, screen):
        """内部：执行绘制"""
        # 绘制背景
        if self.bg_sprite:
            self.bg_sprite.draw(screen)
        else:
            screen.fill(self.bg_color)

        # 绘制所有精灵
        self.sprites.draw(screen)
        # 绘制所有文本
        for text in self.texts:
            text.draw(screen)

        # 用户自定义绘制
        if self.on_draw:
            self.on_draw(screen)


class SceneManager:
    """
    场景管理器 —— 管理多个场景的切换

    用法:
        manager = SceneManager(screen)

        # 注册场景
        manager.add_scene("menu", Scene("menu", bg_color=(50, 50, 80)))
        manager.add_scene("game", Scene("game", bg_color=(0, 0, 0)))

        # 或者直接注册已创建的场景
        my_scene = Scene("settings")
        manager.register_scene(my_scene)

        # 切换场景
        manager.switch_to("menu")

        # 在主循环中调用
        manager.process_events(pygame.event.get())
        manager.update(dt)
        manager.draw()
    """

    def __init__(self, screen):
        """
        参数:
            screen: pygame 显示表面（Screen.win）
        """
        self.screen = screen
        self._scenes = {}  # {name: Scene}
        self._current_scene = None  # 当前场景对象
        self._current_name = None  # 当前场景名称
        self._pending_name = None  # 待切换的场景名
        self._history = []  # 场景切换历史（用于返回）

    # ==================== 注册场景 ====================

    def add_scene(self, name, scene):
        """
        添加场景（场景可以是 Scene 实例或 Scene 子类实例）

        参数:
            name: 场景名称（覆盖 scene.name）
            scene: Scene 实例

        返回:
            scene 本身
        """
        scene.name = name
        scene.manager = self
        self._scenes[name] = scene
        print(f"[SceneManager] 已添加场景: {name}")
        return scene

    def register_scene(self, scene):
        """
        注册场景（使用 scene.name 作为键名）

        参数:
            scene: Scene 实例

        返回:
            scene 本身
        """
        scene.manager = self
        self._scenes[scene.name] = scene
        print(f"[SceneManager] 已注册场景: {scene.name}")
        return scene

    def remove_scene(self, name):
        """
        移除场景

        参数:
            name: 场景名称
        """
        if name in self._scenes:
            # 如果当前正在使用该场景，先退出
            if self._current_name == name:
                self._scenes[name]._do_exit()
                self._current_scene = None
                self._current_name = None
            del self._scenes[name]
            print(f"[SceneManager] 已移除场景: {name}")

    # ==================== 切换场景 ====================

    def switch_to(self, name):
        """
        切换到指定场景（立即执行）

        参数:
            name: 目标场景名称
        """
        if name not in self._scenes:
            print(f"[SceneManager] 错误: 场景 '{name}' 不存在")
            return

        # 退出当前场景
        if self._current_scene:
            self._current_scene._do_exit()

        # 进入新场景
        self._current_name = name
        self._current_scene = self._scenes[name]
        self._current_scene._do_enter()
        Utils.log_info(f"切换到场景: {name}")
        print(f"[SceneManager] 切换到: {name}")

    def switch_to_async(self, name):
        """
        异步切换场景（下一帧执行）
        用于：在事件回调中切换场景时避免冲突

        参数:
            name: 目标场景名称
        """
        self._pending_name = name

    def push_scene(self, name):
        """
        压栈切换：保存当前场景到历史，再切换到新场景
        用 go_back() 可返回

        参数:
            name: 目标场景名称
        """
        if self._current_name:
            self._history.append(self._current_name)
        self.switch_to(name)

    def go_back(self):
        """
        返回上一个场景（从历史中弹出）
        """
        if self._history:
            prev = self._history.pop()
            self.switch_to(prev)
        else:
            print("[SceneManager] 没有历史场景可返回")

    def replace_scene(self, name):
        """
        替换当前场景（不保存历史）
        等同于 switch_to 但不打印切换日志

        参数:
            name: 目标场景名称
        """
        if name not in self._scenes:
            print(f"[SceneManager] 错误: 场景 '{name}' 不存在")
            return

        # 退出当前场景
        if self._current_scene:
            self._current_scene._do_exit()

        # 进入新场景
        self._current_name = name
        self._current_scene = self._scenes[name]
        self._current_scene._do_enter()
        Utils.log_info(f"替换到场景: {name}")

    # ==================== 获取场景 ====================

    def get_current(self):
        """
        获取当前场景对象

        返回:
            Scene 对象 或 None
        """
        return self._current_scene

    def get_current_name(self):
        """
        获取当前场景名称

        返回:
            场景名称字符串 或 None
        """
        return self._current_name

    def get_scene(self, name):
        """
        根据名称获取场景

        参数:
            name: 场景名称

        返回:
            Scene 对象 或 None
        """
        return self._scenes.get(name)

    def get_all_scenes(self):
        """
        获取所有场景名称列表

        返回:
            场景名称列表
        """
        return list(self._scenes.keys())

    def has_scene(self, name):
        """
        检查场景是否存在

        参数:
            name: 场景名称

        返回:
            bool
        """
        return name in self._scenes

    # ==================== 主循环调用 ====================

    def process_events(self, events):
        """
        处理事件（在主循环中调用）

        参数:
            events: pygame 事件列表
        """
        # 处理延迟切换
        if self._pending_name:
            self.switch_to(self._pending_name)
            self._pending_name = None

        if self._current_scene:
            for event in events:
                self._current_scene._do_event(event)

    def update(self, dt):
        """
        更新当前场景（在主循环中调用）

        参数:
            dt: 帧间隔时间（秒）
        """
        if self._current_scene:
            self._current_scene._do_update(dt)

    def draw(self):
        """绘制当前场景（在主循环中调用）"""
        if self._current_scene:
            self._current_scene._do_draw(self.screen)


class Video:
    """视频播放器"""

    def __init__(self, video_path):
        import cv2
        import os
        from moviepy import VideoFileClip

        self.video_path = video_path
        self.audio_path = video_path + ".mp3"
        self._audio_loaded = False
        self._on_stop_callback = None

        # ========== 第一步：先处理音频 ==========
        if os.path.exists(self.audio_path):
            self._audio_loaded = True
            Music.play(self.audio_path)  # 默认只播放一遍
            Music.pause()
        else:
            try:
                clip = VideoFileClip(video_path)
                if clip.audio is not None:
                    clip.audio.write_audiofile(
                        self.audio_path,
                        codec='libmp3lame'
                    )
                    Music.play(self.audio_path)  # 默认只播放一遍
                    Music.pause()
                    self._audio_loaded = True
                clip.close()
            except Exception as e:
                self._audio_loaded = True
                Utils.log_error(f"音频提取失败: {e}")

        # ========== 第二步：再处理视频 ==========
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")

        success, video_image = self.cap.read()
        if not success:
            raise ValueError(f"无法读取视频帧: {video_path}")

        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.width = video_image.shape[1]
        self.height = video_image.shape[0]
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

        self.surface = pygame.image.frombuffer(
            video_image.tobytes(),
            video_image.shape[1::-1],
            "BGR"
        )

        self.current_frame = 0

        # 播放控制属性
        self._playing = False
        self._paused = False

        # 帧率控制
        self._accumulated_time = 0.0
        self._frame_duration = 1.0 / self.fps if self.fps > 0 else 0.016

    def on_stop(self, callback):
        """
        设置视频播放结束回调函数

        参数:
            callback: 播放结束时调用的函数
        """
        self._on_stop_callback = callback

    def _next_frame(self):
        """读取下一帧，返回是否成功"""
        import cv2

        success, video_image = self.cap.read()
        if success:
            self.current_frame += 1
            self.surface = pygame.image.frombuffer(
                video_image.tobytes(),
                video_image.shape[1::-1],
                "BGR"
            )
            return True
        else:
            # 视频播放结束
            self._playing = False
            # 停止音乐
            if self._audio_loaded:
                Music.stop()
            # 触发回调
            if self._on_stop_callback:
                self._on_stop_callback()
            return False

    def update(self, dt):
        """
        更新视频播放

        参数:
            dt: 帧间隔时间（秒）
        """
        if not self._playing or self._paused:
            return

        # 累积时间
        self._accumulated_time += dt

        # 判断是否应该播放下一帧
        while self._accumulated_time >= self._frame_duration:
            self._accumulated_time -= self._frame_duration
            self._next_frame()

    def play(self):
        """开始播放"""
        if not self._playing:
            self._playing = True
            self._paused = False
            self._accumulated_time = 0.0
            if self._audio_loaded:
                Music.resume()

    def stop(self):
        """停止播放（重置到第一帧）"""
        import cv2

        self._playing = False
        self._paused = False
        self.current_frame = 0
        self._accumulated_time = 0.0
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        # 重新读取第一帧
        success, video_image = self.cap.read()
        if success:
            self.surface = pygame.image.frombuffer(
                video_image.tobytes(),
                video_image.shape[1::-1],
                "BGR"
            )

        if self._audio_loaded:
            Music.stop()
            Music.play(self.audio_path)  # 默认只播放一遍
            Music.pause()

    def pause(self):
        """暂停播放"""
        if self._playing:
            self._paused = True
            if self._audio_loaded:
                Music.pause()

    def resume(self):
        """恢复播放"""
        if self._playing and self._paused:
            self._paused = False
            self._accumulated_time = 0.0
            if self._audio_loaded:
                Music.resume()

    def draw(self, screen, x=0, y=0):
        """绘制当前帧到屏幕"""
        if self.surface and self._playing:
            screen.blit(self.surface, (x, y))

    def close(self):
        """释放资源"""
        if self.cap:
            self.cap.release()
        if self._audio_loaded:
            Music.stop()