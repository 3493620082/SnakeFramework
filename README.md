# SnakeFramework - Pygame 游戏开发框架

## 📖 简介

SnakeFramework 是一个轻量级的 Pygame 游戏开发框架，遵循"大道至简"的设计理念，封装了游戏开发中常用的功能模块，让开发者能够快速上手并高效开发 2D 游戏。

### 核心理念
- **简单易用**：最小化学习成本，复制即用
- **功能完备**：涵盖窗口管理、输入处理、精灵动画、音效播放、场景管理等核心功能
- **灵活扩展**：支持面向过程和面向对象两种编程风格

---

## 🚀 快速开始

### 最小示例

```python
from SnakeFramework import *

# 创建窗口
screen = Screen(800, 600, title="我的游戏", fps=60)

# 创建精灵
player = Sprite("assets/player.png", x=100, y=100)

# 游戏循环
def handle_event(event):
    if event.type == pygame.QUIT:
        screen.running = False

def update(dt):
    player.x += 100 * dt  # 每秒移动100像素

def draw(win):
    win.fill((0, 0, 0))
    player.draw(win)

screen.run(handle_event, update, draw)
```

---

## 📦 核心模块

### 1. Screen - 窗口管理

游戏窗口的创建和主循环管理。

```python
# 创建窗口
screen = Screen(800, 600, title="我的游戏", fps=60)

# 方式1：函数式编程
def handle_event(event):
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        screen.running = False

def update(dt):
    pass

def draw(win):
    win.fill((0, 0, 0))

screen.run(handle_event, update, draw)

# 方式2：面向对象
class MyGame(Screen):
    def on_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.running = False
    
    def on_update(self, dt):
        pass
    
    def on_draw(self):
        self.win.fill((0, 0, 0))

MyGame(800, 600).run()
```

#### 参数说明
| 参数 | 类型 | 说明 |
|------|------|------|
| `width` | int | 窗口宽度 |
| `height` | int | 窗口高度 |
| `title` | str | 窗口标题（默认："Pygame Screen"） |
| `fps` | int | 帧率（默认：60） |

---

### 2. Input - 输入管理

全局输入状态，自动更新，无需手动维护。

```python
# 鼠标状态
pos = Input.mouse_pos()      # (x, y)
if Input.mouse_left:         # 左键刚按下
    print("左键点击")
if Input.mouse_right:        # 右键刚按下
    print("右键点击")
if Input.mouse_released:     # 鼠标刚释放
    print("鼠标释放")

# 键盘状态
if Input.key_pressed(pygame.K_SPACE):   # 空格键刚按下
    print("跳起")
if Input.key_held(pygame.K_RIGHT):      # 右箭头按住
    print("向右移动")
if Input.key_released(pygame.K_LEFT):   # 左箭头刚释放
    print("停止左移")
```

#### 常用按键常量
```python
pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT
pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE
pygame.K_a 到 pygame.K_z
pygame.K_0 到 pygame.K_9
```

---

### 3. Sprite - 精灵（支持动画）

游戏角色的基本单元，支持静态图片和帧动画。

#### 3.1 创建精灵

```python
# 方式1：从图片文件加载
player = Sprite("assets/player.png", x=100, y=200)

# 方式2：从 Surface 对象创建
surf = pygame.Surface((32, 32))
box = Sprite(surf, x=50, y=50)

# 方式3：创建空白画布
placeholder = Sprite(width=64, height=64, color=(255, 0, 0))
```

#### 3.2 位置和尺寸

```python
# 位置操作
player.x = 100
player.y = 200
player.position = (100, 200)
player.center = (400, 300)
player.move(10, 5)
player.move_to(200, 300)

# 尺寸读取
width = player.width   # 或 player.w
height = player.height # 或 player.h
size = player.size     # (width, height)
```

#### 3.3 碰撞检测

```python
# 矩形碰撞
if player.collides_with(enemy):
    print("碰撞了！")

# 点碰撞（矩形区域）
if player.contains_point((100, 200)):
    print("点在精灵内")

# 像素级碰撞（精确到非透明像素）
if player.contains_point_alpha((100, 200)):
    print("点中了不透明像素")
```

#### 3.4 鼠标事件

```python
# 绑定点击和悬停事件
btn = Sprite("button.png", x=100, y=100)

def on_click():
    print("按钮被点击")

def on_hover():
    print("鼠标悬停中")

btn.on_left_click(on_click)
btn.on_right_click(lambda: print("右键点击"))
btn.on_mouse(on_hover)

# 需要在 update 中调用精灵的 update 才能触发事件
def update(dt):
    btn.update(dt)
```

#### 3.5 动画系统 ✨

**定义动画**

```python
# 加载图片路径列表
frames = [
    "assets/run_1.png",
    "assets/run_2.png",
    "assets/run_3.png",
    "assets/run_4.png"
]

# 设置动画：动画名, 总帧数, 图片列表
player.setAnim("run", 30, frames)
player.setAnim("idle", 60, ["idle1.png", "idle2.png"])
```

**播放动画**

```python
# 循环播放
player.play("run", loop=True)

# 播放一次
player.play("jump", loop=False)

# 控制播放
player.pause()          # 暂停
player.resume()         # 恢复
player.stop()           # 停止，停留在当前帧

# 状态查询
if player.is_playing():
    print(f"正在播放: {player.get_now_anim_name()}")
```

**动画管理**

```python
# 移除指定动画
player.remove_anim("run")

# 清除所有动画
player.clear_anims()

# 获取所有动画名
anim_list = player.get_anim_list()
```

**完整动画示例**

```python
# 创建角色
hero = Sprite("idle.png", x=400, y=300)

# 定义动画
hero.setAnim("idle", 60, ["idle1.png", "idle2.png", "idle3.png"])
hero.setAnim("run", 30, ["run1.png", "run2.png", "run3.png", "run4.png"])
hero.setAnim("jump", 20, ["jump1.png", "jump2.png", "jump3.png"])

# 默认播放待机
hero.play("idle", loop=True)

def update(dt):
    # 必须在 update 中调用精灵的 update 推进动画
    hero.update(dt)
    
    # 根据按键切换动画
    if Input.key_held(pygame.K_RIGHT):
        hero.play("run", loop=True)
        hero.x += 200 * dt
    elif Input.key_held(pygame.K_LEFT):
        hero.play("run", loop=True)
        hero.x -= 200 * dt
    elif Input.key_pressed(pygame.K_SPACE):
        hero.play("jump", loop=False)
    elif not hero.is_playing():
        hero.play("idle", loop=True)
```

**帧分配机制**

总帧数平均分配到每张图片：
- 例如：3张图片，总帧数30帧
- 每张图片显示：30 ÷ 3 = 10帧
- 播放顺序：图片1(10帧) → 图片2(10帧) → 图片3(10帧)

> ⚠️ **注意**：建议同一动画的所有帧尺寸一致，否则可能出现拉伸或裁剪。

---

### 4. Text - 文字渲染

```python
# 创建文字
score = Text("Score: 0", x=10, y=10, font_size=32, color=(255, 255, 255))

# 更新内容
score.set_text("Score: 100")

# 位置操作
score.move(10, 0)
score.move_to(100, 200)

# 鼠标事件（同 Sprite）
def on_click():
    print("文字被点击")

score.on_left_click(on_click)

# 绘制
def draw(win):
    score.draw(win)
```

#### 参数说明
| 参数 | 类型 | 说明 |
|------|------|------|
| `text` | str | 文字内容（默认：""） |
| `x, y` | int | 位置（默认：0, 0） |
| `font_size` | int | 字号（默认：24） |
| `color` | tuple | RGB 颜色（默认：(255, 255, 255)） |
| `font_path` | str | 字体路径（默认：微软雅黑） |

---

### 5. Music - 背景音乐

```python
# 播放音乐（循环）
Music.play("assets/bgm.mp3", volume=0.5, loop=-1)

# 控制播放
Music.pause()
Music.resume()
Music.stop()
Music.set_volume(0.8)  # 0.0 ~ 1.0
```

#### 参数说明
| 参数 | 类型 | 说明 |
|------|------|------|
| `filepath` | str | 音乐文件路径 |
| `volume` | float | 音量 0.0-1.0（默认：1.0） |
| `loop` | int | 循环次数（-1 无限循环，默认：-1） |

---

### 6. Sound - 音效

```python
# 创建音效
sfx = Sound("assets/click.wav", volume=0.8)

# 播放音效
sfx.play()
sfx.set_volume(0.5)
```

---

### 7. Utils - 工具类

#### 随机概率判断

```python
if Utils.chance(30):  # 30% 概率触发
    print("暴击！")

if Utils.chance():    # 100% 触发
    print("总是执行")
```

#### 鼠标光标控制

```python
Utils.hide_mouse(False)  # 隐藏鼠标
Utils.hide_mouse(True)   # 显示鼠标
```

#### 日志系统

```python
Utils.log_info("游戏启动")
Utils.log_warning("帧率过低: 45 FPS")
Utils.log_error("图片加载失败: assets/hero.png")
# 日志输出到 console.log 文件
```

---

### 8. Scene - 场景管理

场景系统用于组织游戏的不同界面（主菜单、游戏、设置等）。

#### 8.1 创建场景

```python
# 创建场景
menu = Scene("menu", bg_color=(50, 50, 80))
game = Scene("game", bg_color=(0, 0, 0))

# 添加元素
title = Text("主菜单", x=300, y=100, font_size=48)
menu.add_text(title)

start_btn = Sprite("start.png", x=350, y=200)
start_btn.on_left_click(lambda: manager.switch_to("game"))
menu.add_sprite(start_btn)
```

#### 8.2 场景管理器

```python
# 创建管理器
manager = SceneManager(screen.win)

# 注册场景
manager.register_scene(menu)
manager.register_scene(game)

# 切换场景
manager.switch_to("menu")      # 立即切换
manager.switch_to_async("game") # 下一帧切换

# 场景栈（返回功能）
manager.push_scene("game")     # 压栈切换
manager.go_back()              # 返回上一个场景

# 替换当前场景
manager.replace_scene("settings")
```

#### 8.3 场景生命周期

```python
def on_enter():
    print("进入场景")

def on_exit():
    print("退出场景")

def on_update(dt):
    # 自定义更新逻辑
    pass

def on_draw(screen):
    # 自定义绘制逻辑
    pass

# 绑定回调
scene.on_enter = on_enter
scene.on_exit = on_exit
scene.on_update = on_update
scene.on_draw = on_draw
```

#### 8.4 主循环集成

```python
# 方式1：手动调用
def update(dt):
    manager.update(dt)

def draw(win):
    manager.draw()

# 方式2：使用 Screen 的面向对象方式
class MyGame(Screen):
    def __init__(self):
        super().__init__(800, 600)
        self.manager = SceneManager(self.win)
        self.manager.register_scene(menu_scene)
        self.manager.switch_to("menu")
    
    def on_update(self, dt):
        self.manager.update(dt)
    
    def on_draw(self):
        self.manager.draw()
```

---

### 9. Video - 视频播放

Video类初始化的时候传入视频文件的路径即可  
- play()播放视频  
- stop()结束播放  
- pause()暂停  
- resume()继续播放  
- on_stop()播放结束回调函数：传入一个函数，在视频播放结束后会自动调用这个函数  
**注：目前视频播放功能有个小bug，第一次播放可能会出现音画不同步的问题，第二次就好了。先了解具体原因可以联系作者，这里就不过多描述了，或者用户也可以自行查看源代码。**
```python
video = Video("assets/video.mp3")
video.play()

def func():
    print("视频播放结束了")
video.on_stop(func)

def update(dt):
    video.update(dt)

def draw(win):
    video.draw(win)
```

## 🎮 完整游戏示例

```python
from SnakeFramework import *
import pygame

# 创建窗口
screen = Screen(800, 600, title="角色控制器", fps=60)

# 创建玩家
path = "assets/minotaur/Walking/"
frames = [
    f"{path}frame_0.png",
    f"{path}frame_2.png",
    f"{path}frame_4.png",
    f"{path}frame_6.png",
    f"{path}frame_8.png",
    f"{path}frame_10.png",
    f"{path}frame_12.png",
    f"{path}frame_14.png",
    f"{path}frame_16.png"
]

player = Sprite(frames[0], x=350, y=250)
player.setAnim("walk", 180, frames)
player.play("walk", loop=True)

# 状态信息
info = Text("状态: 行走", x=10, y=10, font_size=24, color=(255, 255, 0))

def handle_event(event):
    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        screen.running = False

def update(dt):
    # 更新动画
    player.update(dt)
    
    # WASD 控制移动
    speed = 200
    dx, dy = 0, 0
    if Input.key_held(pygame.K_w):
        dy = -speed * dt
    if Input.key_held(pygame.K_s):
        dy = speed * dt
    if Input.key_held(pygame.K_a):
        dx = -speed * dt
    if Input.key_held(pygame.K_d):
        dx = speed * dt
    
    if dx != 0 or dy != 0:
        player.move(dx, dy)
        info.set_text(f"位置: ({player.x:.0f}, {player.y:.0f})")

def draw(win):
    win.fill((50, 50, 80))
    player.draw(win)
    info.draw(win)

# 启动游戏
screen.run(handle_event, update, draw)
```

---

## 📂 资源目录结构

```
项目根目录/
├── assets/
│   ├── images/          # 图片资源
│   ├── music/           # 背景音乐
│   └── sounds/          # 音效文件
├── SnakeFramework.py    # 框架文件
└── main.py             # 游戏主程序
```

> 框架会自动创建缺失的资源目录。

---

## 📝 日志系统

框架自动记录运行日志到 `console.log`：

```
[2026-06-26 14:30:15] INFO 游戏启动
[2026-06-26 14:30:20] INFO 切换到场景: game
[2026-06-26 14:30:25] WARNING 帧率过低: 45.2 FPS
[2026-06-26 14:30:30] ERROR 图片加载失败: assets/hero.png
```

---

## ⚠️ 常见问题

### 1. 动画不播放？
**原因**：没有在 `update` 中调用精灵的 `update(dt)`

```python
def update(dt):
    # ❌ 错误：忘记调用
    pass

def update(dt):
    # ✅ 正确
    player.update(dt)
```

### 2. 图片加载失败？
- 检查路径是否正确（相对路径相对于 Python 运行目录）
- 确保文件存在
- 尝试使用绝对路径

### 3. 中文文字显示乱码？
- 指定中文字体路径
```python
Text("你好", font_path="C:/Windows/Fonts/msyh.ttc")
```

### 4. 像素级碰撞不准确？
- 确保精灵图片有透明通道（PNG 格式）
- 碰撞检测基于当前帧的图片

### 5. 内存占用过大？
- 控制动画帧数
- 降低图片分辨率
- 删除不需要的动画：`remove_anim()`

---

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**让游戏开发更简单！** 🎮✨