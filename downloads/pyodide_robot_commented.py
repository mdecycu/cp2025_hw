# 匯入 js 模組（Pyodide 提供）以操作瀏覽器 DOM，匯入 asyncio 處理非同步
import js, asyncio

# 每格的像素尺寸
CELL_SIZE = 40

# 牆壁的厚度
WALL_THICKNESS = 6

# 機器人與牆的圖片來源路徑
IMG_PATH = "https://mde.tw/cp2025/reeborg/src/images/"

# 定義世界（地圖）類別
class World:
    # 類別變數，用來快取圖片物件，避免重複下載
    _image_cache = {}

    # 建構子，接收地圖寬度與高度
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.layers = self._create_layers()  # 建立各層 canvas（格線、牆、物件、機器人）
        self._init_html()  # 初始化 HTML 並將 canvas 插入頁面

    # 建立 4 層 canvas：grid, walls, objects, robots
    def _create_layers(self):
        return {
            "grid": js.document.createElement("canvas"),
            "walls": js.document.createElement("canvas"),
            "objects": js.document.createElement("canvas"),
            "robots": js.document.createElement("canvas"),
        }

    # 初始化 HTML 畫面
    def _init_html(self):
        # 建立容器 <div>，設定相對定位與寬高
        container = js.document.createElement("div")
        container.style.position = "relative"
        container.style.width = f"{self.width * CELL_SIZE}px"
        container.style.height = f"{self.height * CELL_SIZE}px"

        # 將每一層 canvas 設定大小與樣式並加入 container
        for z, canvas in enumerate(self.layers.values()):
            canvas.width = self.width * CELL_SIZE
            canvas.height = self.height * CELL_SIZE
            canvas.style.position = "absolute"
            canvas.style.top = "0px"
            canvas.style.left = "0px"
            canvas.style.zIndex = str(z)
            container.appendChild(canvas)

        # 建立按鈕容器，並加入兩個控制按鈕
        button_container = js.document.createElement("div")
        button_container.style.marginTop = "10px"
        button_container.style.textAlign = "center"

        move_button = js.document.createElement("button")
        move_button.innerHTML = "Move Forward"
        move_button.style.margin = "5px"
        move_button.style.padding = "10px 20px"
        move_button.style.fontSize = "16px"
        button_container.appendChild(move_button)

        turn_button = js.document.createElement("button")
        turn_button.innerHTML = "Turn Left"
        turn_button.style.margin = "5px"
        turn_button.style.padding = "10px 20px"
        turn_button.style.fontSize = "16px"
        button_container.appendChild(turn_button)

        # 將 container 與按鈕插入指定的 HTML 元素
        brython_div = js.document.getElementById("brython_div1")
        if not brython_div:
            raise RuntimeError("🚨 'brython_div1' element not found in HTML!")
        brython_div.innerHTML = ""
        brython_div.appendChild(container)
        brython_div.appendChild(button_container)

        # 保存按鈕物件供後續事件綁定
        self.move_button = move_button
        self.turn_button = turn_button
    # 繪製格線背景層
    def _draw_grid(self):
        ctx = self.layers["grid"].getContext("2d")  # 取得 grid 層的繪圖上下文
        ctx.strokeStyle = "#cccccc"  # 設定線條顏色為淡灰色

        # 繪製垂直線條
        for i in range(self.width + 1):
            ctx.beginPath()
            ctx.moveTo(i * CELL_SIZE, 0)
            ctx.lineTo(i * CELL_SIZE, self.height * CELL_SIZE)
            ctx.stroke()

        # 繪製水平線條
        for j in range(self.height + 1):
            ctx.beginPath()
            ctx.moveTo(0, j * CELL_SIZE)
            ctx.lineTo(self.width * CELL_SIZE, j * CELL_SIZE)
            ctx.stroke()

    # 在指定 canvas 上繪製圖片，通常是 robot 或 wall
    def _draw_image(self, ctx, img_key, x, y, w, h, offset_x=0, offset_y=0):
        img = World._image_cache.get(img_key)  # 從快取中取出圖片
        if img and img.complete and img.naturalWidth > 0:  # 確保圖片已載入完成
            px = x * CELL_SIZE + offset_x
            py = (self.height - 1 - y) * CELL_SIZE + offset_y  # 注意 y 軸方向翻轉
            ctx.drawImage(img, px, py, w, h)
            return True
        else:
            print(f"⚠️ Image '{img_key}' not ready for drawing.")
            return False

    # 繪製地圖邊界的牆壁（上下為 north，左右為 east）
    async def _draw_walls(self):
        ctx = self.layers["walls"].getContext("2d")
        ctx.clearRect(0, 0, self.width * CELL_SIZE, self.height * CELL_SIZE)  # 清除原本的牆
        success = True  # 記錄是否成功繪製所有牆壁

        # 上下邊界畫 north 牆
        for x in range(self.width):
            success &= self._draw_image(ctx, "north", x, self.height - 1, CELL_SIZE, WALL_THICKNESS)
            success &= self._draw_image(ctx, "north", x, 0, CELL_SIZE, WALL_THICKNESS, offset_y=CELL_SIZE - WALL_THICKNESS)

        # 左右邊界畫 east 牆
        for y in range(self.height):
            success &= self._draw_image(ctx, "east", 0, y, WALL_THICKNESS, CELL_SIZE)
            success &= self._draw_image(ctx, "east", self.width - 1, y, WALL_THICKNESS, CELL_SIZE, offset_x=CELL_SIZE - WALL_THICKNESS)

        return success

    # 非同步預先載入所有圖片（robot 四方向 + 牆壁圖片）
    async def _preload_images(self):
        image_files = {
            "blue_robot_e": "blue_robot_e.png",
            "blue_robot_n": "blue_robot_n.png",
            "blue_robot_w": "blue_robot_w.png",
            "blue_robot_s": "blue_robot_s.png",
            "north": "north.png",
            "east": "east.png",
        }

        promises = []

        for key, filename in image_files.items():
            # 若已快取且圖片已載入成功則跳過
            if key in World._image_cache and World._image_cache[key].complete:
                continue

            # 建立 <img> 元素
            img = js.document.createElement("img")
            img.crossOrigin = "Anonymous"  # 設定跨域允許下載
            img.src = IMG_PATH + filename  # 設定圖片來源 URL
            World._image_cache[key] = img  # 加入快取

            # 包裝成 Promise 等待圖片載入
            def make_promise(img_element):
                def executor(resolve, reject):
                    def on_load(event):
                        img_element.removeEventListener("load", on_load)
                        img_element.removeEventListener("error", on_error)
                        resolve(img_element)
                    def on_error(event):
                        img_element.removeEventListener("load", on_load)
                        img_element.removeEventListener("error", on_error)
                        reject(f"Failed to load image: {img_element.src}")
                    img_element.addEventListener("load", on_load)
                    img_element.addEventListener("error", on_error)
                    if img_element.complete and img_element.naturalWidth > 0:
                        resolve(img_element)
                return js.Promise.new(executor)

            promises.append(make_promise(img))

        if not promises:
            return True  # 如果全部圖片已載入完成

        try:
            # 等待所有圖片都載入
            await js.await_promise(js.Promise.all(promises))
            return True
        except Exception as e:
            print(f"🚨 Error during image preloading: {str(e)}")
            return False
    # 非同步設定整個世界，包含圖片預載入與繪製格線、牆壁等
    async def setup(self):
        # 嘗試最多三次圖片預載入
        for _ in range(3):
            if await self._preload_images():
                break
            await asyncio.sleep(0.5)  # 等待一段時間後重試
        else:
            print("🚨 Failed to preload images after retries.")
            return False  # 如果三次都失敗就中止設定

        await asyncio.sleep(0)  # 讓出 event loop 一次（可確保畫面更新）

        self._draw_grid()  # 繪製底部格線

        # 嘗試最多三次繪製牆壁
        for _ in range(3):
            if await self._draw_walls():
                break
            await asyncio.sleep(0.5)
        else:
            print("🚨 Failed to draw walls after retries.")
            return False

        # 最後確認機器人預設圖片是否就緒
        robot_img_key = "blue_robot_e"
        if not (World._image_cache.get(robot_img_key) and World._image_cache[robot_img_key].complete):
            print(f"🚨 Robot image '{robot_img_key}' still not ready after setup!")
            return False

        return True  # 所有準備工作完成

# Robot 類別：控制機器人狀態、圖像與動作
class Robot:
    def __init__(self, world, x, y):
        self.world = world
        self.x = x - 1  # 將座標轉為從 0 開始的索引
        self.y = y - 1
        self.facing = "E"  # 預設面朝東（右）
        self._facing_order = ["E", "N", "W", "S"]  # 轉向順序
        self.robot_ctx = world.layers["robots"].getContext("2d")  # 機器人所在圖層
        self.trace_ctx = world.layers["objects"].getContext("2d")  # 移動軌跡圖層
        self._draw_robot()  # 初始化繪製機器人

    # 根據目前朝向取得對應圖片 key
    def _robot_image_key(self):
        return f"blue_robot_{self.facing.lower()}"

    # 在畫布上畫出機器人圖像
    def _draw_robot(self):
        self.robot_ctx.clearRect(0, 0, self.world.width * CELL_SIZE, self.world.height * CELL_SIZE)
        self.world._draw_image(self.robot_ctx, self._robot_image_key(), self.x, self.y, CELL_SIZE, CELL_SIZE)

    # 畫出移動時留下的線條軌跡
    def _draw_trace(self, from_x, from_y, to_x, to_y):
        ctx = self.trace_ctx
        ctx.strokeStyle = "#d33"  # 深紅色軌跡
        ctx.lineWidth = 2
        ctx.beginPath()
        # 計算起點與終點中心點的座標
        fx = from_x * CELL_SIZE + CELL_SIZE / 2
        fy = (self.world.height - 1 - from_y) * CELL_SIZE + CELL_SIZE / 2
        tx = to_x * CELL_SIZE + CELL_SIZE / 2
        ty = (self.world.height - 1 - to_y) * CELL_SIZE + CELL_SIZE / 2
        ctx.moveTo(fx, fy)
        ctx.lineTo(tx, ty)
        ctx.stroke()

    # 非同步向前走指定步數（預設為 1）
    async def walk(self, steps=1):
        for _ in range(steps):
            from_x, from_y = self.x, self.y  # 記錄目前位置
            dx, dy = 0, 0  # 預設不移動

            # 根據目前方向決定移動向量
            if self.facing == "E": dx = 1
            elif self.facing == "W": dx = -1
            elif self.facing == "N": dy = 1
            elif self.facing == "S": dy = -1

            # 計算下一格位置
            next_x = self.x + dx
            next_y = self.y + dy

            # 確認不會超出邊界
            if 0 <= next_x < self.world.width and 0 <= next_y < self.world.height:
                self.x, self.y = next_x, next_y  # 移動位置
                self._draw_trace(from_x, from_y, self.x, self.y)  # 畫出軌跡
                self._draw_robot()  # 更新機器人圖像
                await asyncio.sleep(0.2)  # 加入動畫延遲
            else:
                print("🚨 Hit a wall, stop moving!")
                break  # 碰到牆就停止走路

    # 非同步向左轉 90 度
    async def turn_left(self):
        idx = self._facing_order.index(self.facing)  # 找到當前朝向的索引
        self.facing = self._facing_order[(idx + 1) % 4]  # 往左轉：取下一個方向（循環）
        self._draw_robot()  # 重新繪製朝向
        await asyncio.sleep(0.3)  # 加入動畫延遲

# 綁定控制方式（鍵盤與按鈕）給指定的 robot 實例
def _bind_controls(robot: Robot):

    # 鍵盤控制事件處理函數
    def handle_key(event):
        try:
            if event.key == 'j':  # 按下 j 鍵 → 前進一步
                asyncio.create_task(robot.walk(1))
            elif event.key == 'i':  # 按下 i 鍵 → 左轉
                asyncio.create_task(robot.turn_left())
        except Exception as e:
            print(f"🚨 Error in key handler: {e}")

    # 按鈕「Move Forward」的事件處理器
    def handle_move_button(event):
        try:
            asyncio.create_task(robot.walk(1))  # 非同步前進一步
        except Exception as e:
            print(f"🚨 Error in move button handler: {e}")

    # 按鈕「Turn Left」的事件處理器
    def handle_turn_button(event):
        try:
            asyncio.create_task(robot.turn_left())  # 非同步左轉
        except Exception as e:
            print(f"🚨 Error in turn button handler: {e}")

    # 使用 JavaScript 的 global scope 綁定 Python 函式
    js.window.py_handle_key = handle_key
    js.document.addEventListener('keydown', js.Function("event", "py_handle_key(event);"))

    # 將 Python 處理函數掛到 JS 全域 window，供 onclick 呼叫
    js.window.py_handle_move_button = handle_move_button
    js.window.py_handle_turn_button = handle_turn_button

    # 為世界中的按鈕元件綁定事件
    robot.world.move_button.addEventListener('click', js.Function("event", "py_handle_move_button(event);"))
    robot.world.turn_button.addEventListener('click', js.Function("event", "py_handle_turn_button(event);"))

# 綁定控制方式（鍵盤與按鈕）給指定的 robot 實例
def _bind_controls(robot: Robot):

    # 鍵盤控制事件處理函數
    def handle_key(event):
        try:
            if event.key == 'j':  # 按下 j 鍵 → 前進一步
                asyncio.create_task(robot.walk(1))
            elif event.key == 'i':  # 按下 i 鍵 → 左轉
                asyncio.create_task(robot.turn_left())
        except Exception as e:
            print(f"🚨 Error in key handler: {e}")

    # 按鈕「Move Forward」的事件處理器
    def handle_move_button(event):
        try:
            asyncio.create_task(robot.walk(1))  # 非同步前進一步
        except Exception as e:
            print(f"🚨 Error in move button handler: {e}")

    # 按鈕「Turn Left」的事件處理器
    def handle_turn_button(event):
        try:
            asyncio.create_task(robot.turn_left())  # 非同步左轉
        except Exception as e:
            print(f"🚨 Error in turn button handler: {e}")

    # 使用 JavaScript 的 global scope 綁定 Python 函式
    js.window.py_handle_key = handle_key
    js.document.addEventListener('keydown', js.Function("event", "py_handle_key(event);"))

    # 將 Python 處理函數掛到 JS 全域 window，供 onclick 呼叫
    js.window.py_handle_move_button = handle_move_button
    js.window.py_handle_turn_button = handle_turn_button

    # 為世界中的按鈕元件綁定事件
    robot.world.move_button.addEventListener('click', js.Function("event", "py_handle_move_button(event);"))
    robot.world.turn_button.addEventListener('click', js.Function("event", "py_handle_turn_button(event);"))

# 初始化函式，建立世界與機器人，並完成控制綁定
def init(world_width=10, world_height=10, robot_x=1, robot_y=1):
    """
    方便快速建立一個 World 和 Robot，並且綁定控制鍵與按鈕。
    建立後回傳 (world, robot) tuple，方便呼叫。

    使用方式：
    world, robot = await init(10, 10, 1, 1)
    """

    # 包裝成內部 async 函式（因為 setup() 是 async）
    async def _inner():
        world = World(world_width, world_height)  # 建立世界物件
        if not await world.setup():  # 初始化地圖與牆
            raise RuntimeError("World setup failed!")

        robot = Robot(world, robot_x, robot_y)  # 建立機器人並放置在指定位置
        _bind_controls(robot)  # 綁定控制按鈕與鍵盤事件
        return world, robot  # 回傳物件以便外部使用

    return asyncio.create_task(_inner())  # 使用 asyncio 創建非同步任務
