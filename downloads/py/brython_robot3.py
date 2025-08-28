'''
from brython_robot4 import init, load_scene_from_url, get_url_parameter
from browser import aio

# 機器人行為腳本
async def robot_actions(robot):
    print("開始執行機器人程式，探索並採收所有胡蘿蔔。")
    # 新增旗標來控制回溯
    exploration_done = False
    
    async def explore_and_collect():
        nonlocal exploration_done

        # 在當前格子採收所有胡蘿蔔，直到該格清空
        while robot.background_is("pale_grass"):
            robot.pick_carrot()

        # 將當前格子標記為已走過
        robot.visited.add((robot.base.x, robot.base.y))

        # 定義四個方向，依序檢查
        for _ in range(4):
            # 檢查前方是否暢通且未走過
            if robot.front_is_clear() and not robot.front_is_visited():
                await robot.move(1)
                # 遞迴呼叫，繼續探索新的格子
                await explore_and_collect()
                
                # 如果探索已完成，就直接返回，不執行回溯
                if exploration_done:
                    return
                    
                # 遞迴結束後，回溯一步
                await robot.move_backward()
            
            # 如果前方不符合條件，就左轉，檢查下一個方向
            await robot.turn_left()

        # 當所有方向都探索完畢，標記探索完成
        exploration_done = True
        return
    
    # 執行探索函式
    await explore_and_collect()
    
    # 所有的探索和回溯動作都結束後，才會執行這裡的程式碼
    print("所有可達格子都已探索完畢。")
    print(f"程式執行完畢。總共採收了 {robot.carrots_collected} 個胡蘿蔔。")

# 程式啟動點
async def main():
    world_url = get_url_parameter('world')
    if world_url:
        scene_data = await load_scene_from_url(world_url)
        # 設定機器人容量上限為 50
        world, robot = init(scene_data, robot_config={"max_carrots": 50})
    else:
        # 預設場景也設定容量上限
        world, robot = init(robot_config={"max_carrots": 50})

    if robot:
        await robot_actions(robot)

# 啟動主程式
aio.run(main())
'''

# 以下為brython_robot4.py的內容
# -------------------------------------------------------------
from browser import document, html, timer, window, ajax, aio
import json

CELL_SIZE = 40
WALL_THICKNESS = 6
IMG_PATH = "https://mde.tw/cp2025/reeborg/src/images/"
DEFAULT_SCENE = {
    "robots": [{
        "x": 1,
        "y": 1,
        "orientation": 0,
        "objects": {
            "carrot": "infinite"
        }
    }],
    "walls": {
        "10,1": ["east"], "10,2": ["east"], "10,3": ["east"], "10,4": ["east"],
        "10,5": ["east"], "10,6": ["east"], "10,7": ["east"], "10,8": ["east"],
        "10,9": ["east"], "10,10": ["east", "north"], "9,10": ["north"],
        "8,10": ["north"], "7,10": ["north"], "6,10": ["north"], "5,10": ["north"],
        "4,10": ["north"], "3,10": ["north"], "2,10": ["north"], "1,10": ["north"]
    },
    "goal": {"objects": {}},
    "objects": {
        "5,3": {"carrot": 1}, "5,4": {"carrot": 1}, "5,5": {"carrot": 1},
        "5,6": {"carrot": 1}, "5,8": {"carrot": 1}, "4,8": {"carrot": 1},
        "4,7": {"carrot": 2}, "4,5": {"carrot": 1}, "4,4": {"carrot": 2},
        "6,7": {"carrot": 1}, "6,6": {"carrot": 3}, "6,5": {"carrot": 1},
        "6,4": {"carrot": 1}, "6,3": {"carrot": 1}, "7,8": {"carrot": 1},
        "7,7": {"carrot": 1}, "7,6": {"carrot": 1}, "7,4": {"carrot": 3},
        "8,7": {"carrot": 1}, "8,6": {"carrot": 1}, "8,5": {"carrot": 1},
        "3,8": {"carrot": 1}, "3,7": {"carrot": 1}, "3,6": {"carrot": 1},
        "3,5": {"carrot": 1}, "3,4": {"carrot": 1}, "8,8": {"carrot": 2},
        "8,4": {"carrot": 1}, "7,3": {"carrot": 1}, "3,3": {"carrot": 1},
        "8,3": {"carrot": 1}
    }
}

class World:
    def __init__(self, width, height, walls=None, objects=None):
        self.width = width
        self.height = height
        self.walls = walls if walls else {}
        self.objects = objects if objects else {}
        self.layers = self._create_layers()
        self._init_html()
        self._draw_grid()
        self._draw_walls()
        self._draw_background()

    def _create_layers(self):
        return {
            "grid": html.CANVAS(width=self.width * CELL_SIZE, height=self.height * CELL_SIZE),
            "background": html.CANVAS(width=self.width * CELL_SIZE, height=self.height * CELL_SIZE),
            "traces": html.CANVAS(width=self.width * CELL_SIZE, height=self.height * CELL_SIZE),
            "walls": html.CANVAS(width=self.width * CELL_SIZE, height=self.height * CELL_SIZE),
            "objects": html.CANVAS(width=self.width * CELL_SIZE, height=self.height * CELL_SIZE),
            "robots": html.CANVAS(width=self.width * CELL_SIZE, height=self.height * CELL_SIZE),
        }

    def _init_html(self):
        container = html.DIV(style={
            "position": "relative",
            "width": f"{self.width * CELL_SIZE}px",
            "height": f"{self.height * CELL_SIZE}px"
        })
        for z, canvas in enumerate(self.layers.values()):
            canvas.style = {
                "position": "absolute",
                "top": "0px",
                "left": "0px",
                "zIndex": str(z)
            }
            container <= canvas
        document["brython_div1"].clear()
        document["brython_div1"] <= container

    def _draw_grid(self):
        ctx = self.layers["grid"].getContext("2d")
        ctx.strokeStyle = "#cccccc"
        for i in range(self.width + 1):
            ctx.beginPath()
            ctx.moveTo(i * CELL_SIZE, 0)
            ctx.lineTo(i * CELL_SIZE, self.height * CELL_SIZE)
            ctx.stroke()
        for j in range(self.height + 1):
            ctx.beginPath()
            ctx.moveTo(0, j * CELL_SIZE)
            ctx.lineTo(self.width * CELL_SIZE, j * CELL_SIZE)
            ctx.stroke()

    def _draw_image(self, ctx, src, x, y, w, h, offset_x=0, offset_y=0):
        img = html.IMG()
        img.src = src
        def onload(evt):
            px = x * CELL_SIZE + offset_x
            py = (self.height - 1 - y) * CELL_SIZE + offset_y
            ctx.drawImage(img, px, py, w, h)
        img.bind("load", onload)

    def _draw_background(self):
        ctx = self.layers["background"].getContext("2d")
        ctx.clearRect(0, 0, self.width * CELL_SIZE, self.height * CELL_SIZE)
        for y in range(self.height):
            for x in range(self.width):
                coord = f"{x+1},{y+1}"
                if coord in self.objects and "carrot" in self.objects[coord]:
                    src = IMG_PATH + "pale_grass.png"
                else:
                    src = IMG_PATH + "grass.png"
                def draw(x=x, y=y, src=src):
                    img = html.IMG()
                    img.src = src
                    def onload(evt):
                        px = x * CELL_SIZE
                        py = (self.height - 1 - y) * CELL_SIZE
                        ctx.drawImage(img, px, py, CELL_SIZE, CELL_SIZE)
                    img.bind("load", onload)
                draw()

    def _draw_walls(self):
        ctx = self.layers["walls"].getContext("2d")
        for x in range(self.width):
            self._draw_image(ctx, IMG_PATH + "north.png", x, self.height - 1,
                             CELL_SIZE, WALL_THICKNESS, offset_y=0)
            self._draw_image(ctx, IMG_PATH + "north.png", x, 0,
                             CELL_SIZE, WALL_THICKNESS, offset_y=CELL_SIZE - WALL_THICKNESS)
        for y in range(self.height):
            self._draw_image(ctx, IMG_PATH + "east.png", 0, y,
                             WALL_THICKNESS, CELL_SIZE, offset_x=0)
            self._draw_image(ctx, IMG_PATH + "east.png", self.width - 1, y,
                             WALL_THICKNESS, CELL_SIZE, offset_x=CELL_SIZE - WALL_THICKNESS)
        for coord, dirs in self.walls.items():
            x, y = map(int, coord.split(","))
            for d in dirs:
                if d == "north":
                    self._draw_image(ctx, IMG_PATH + "north.png", x - 1, y - 1,
                                     CELL_SIZE, WALL_THICKNESS, offset_y=0)
                elif d == "east":
                    self._draw_image(ctx, IMG_PATH + "east.png", x - 1, y - 1,
                                     WALL_THICKNESS, CELL_SIZE, offset_x=CELL_SIZE - WALL_THICKNESS)

    def draw_objects(self):
        ctx = self.layers["objects"].getContext("2d")
        ctx.clearRect(0, 0, self.width * CELL_SIZE, self.height * CELL_SIZE)
        for coord, items in self.objects.items():
            x, y = map(int, coord.split(","))
            for obj, count in items.items():
                if obj == "carrot":
                    self._draw_image(ctx, IMG_PATH + "carrot.png", x - 1, y - 1, CELL_SIZE, CELL_SIZE)
                    if 1 <= count <= 9:
                        num_img = f"{IMG_PATH}{count}_t.png"
                        self._draw_image(
                            ctx,
                            num_img,
                            x - 1, y - 1,
                            20, 20,
                            offset_x=CELL_SIZE - 22,
                            offset_y=CELL_SIZE - 22
                        )
                        
    def object_at_coord(self, x, y, obj_name="carrot"):
        """檢查指定座標是否有指定物件。"""
        coord = f"{x},{y}"
        cell = self.objects.get(coord, {})
        return obj_name in cell and cell[obj_name] > 0

class AnimatedRobot:
    def __init__(self, world, x, y, orientation=0):
        self.world = world
        self.x = x - 1
        self.y = y - 1
        self.facing_order = ["E", "N", "W", "S"]
        self.facing = self.facing_order[orientation % 4]
        self.robot_ctx = world.layers["robots"].getContext("2d")
        self.trace_ctx = world.layers["traces"].getContext("2d")
        self._draw_robot()

    def _robot_image(self):
        return {
            "E": "blue_robot_e.png",
            "N": "blue_robot_n.png",
            "W": "blue_robot_w.png",
            "S": "blue_robot_s.png"
        }[self.facing]

    def _draw_robot(self):
        self.robot_ctx.clearRect(0, 0, self.world.width * CELL_SIZE, self.world.height * CELL_SIZE)
        self.world._draw_image(self.robot_ctx, IMG_PATH + self._robot_image(),
                               self.x, self.y, CELL_SIZE, CELL_SIZE)

    def _draw_trace(self, from_x, from_y, to_x, to_y):
        ctx = self.trace_ctx
        ctx.strokeStyle = "#d33"
        ctx.lineWidth = 2
        ctx.beginPath()
        fx = from_x * CELL_SIZE + CELL_SIZE / 2
        fy = (self.world.height - 1 - from_y) * CELL_SIZE + CELL_SIZE / 2
        tx = to_x * CELL_SIZE + CELL_SIZE / 2
        ty = (self.world.height - 1 - to_y) * CELL_SIZE + CELL_SIZE / 2
        ctx.moveTo(fx, fy)
        ctx.lineTo(tx, ty)
        ctx.stroke()

    async def move(self, steps=1):
        for _ in range(steps):
            from_x, from_y = self.x, self.y
            dx, dy = 0, 0
            facing_dir = None
            if self.facing == "E":
                dx = 1
                facing_dir = "east"
            elif self.facing == "W":
                dx = -1
                facing_dir = "west"
            elif self.facing == "N":
                dy = 1
                facing_dir = "north"
            elif self.facing == "S":
                dy = -1
                facing_dir = "south"
            next_x = self.x + dx
            next_y = self.y + dy
            if not (0 <= next_x < self.world.width and 0 <= next_y < self.world.height):
                print("已經撞牆，停止移動！（超出邊界）")
                return
            current_coord = f"{self.x + 1},{self.y + 1}"
            next_coord = f"{next_x + 1},{next_y + 1}"
            walls_here = self.world.walls.get(current_coord, [])
            if facing_dir in walls_here:
                print(f"已經撞牆，停止移動！（{current_coord} 有 {facing_dir} 牆）")
                return
            opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}
            walls_next = self.world.walls.get(next_coord, [])
            if opposite[facing_dir] in walls_next:
                print(f"已經撞牆，停止移動！（{next_coord} 有 {opposite[facing_dir]} 牆）")
                return

            self.x, self.y = next_x, next_y
            self._draw_trace(from_x, from_y, self.x, self.y)
            self._draw_robot()
            await aio.sleep(0.05)
        self._draw_robot()

    async def turn_left(self):
        idx = self.facing_order.index(self.facing)
        self.facing = self.facing_order[(idx + 1) % 4]
        self._draw_robot()
        await aio.sleep(0.05)

class SmartRobot:
    def __init__(self, base_robot, max_carrots=25):
        self.base = base_robot
        self.world = base_robot.world
        self.carrots_collected = 0
        self.visited = set()
        self.visited.add((self.base.x, self.base.y))
        self.max_carrots = max_carrots
        self.BOX_SIZE = 5

    async def move(self, steps=1):
        for _ in range(steps):
            if self.front_is_clear():
                await self.base.move(1)
                self.visited.add((self.base.x, self.base.y))
            else:
                break
        self._draw_robot()

    async def move_backward(self, speedup=False):
        if speedup:
            self.base.facing = self.base.facing_order[(self.base.facing_order.index(self.base.facing) + 2) % 4]
            self.base.x, self.base.y = self._get_next_coord()
            self._draw_robot()
        else:
            await self.turn_left()
            await self.turn_left()
            await self.move(1)
            await self.turn_left()
            await self.turn_left()

    async def turn_left(self, speedup=False):
        self.base.facing = self.base.facing_order[(self.base.facing_order.index(self.base.facing) + 1) % 4]
        self.base._draw_robot()
        if not speedup:
            await aio.sleep(0.05)

    async def turn_right(self, speedup=False):
        await self.turn_left(speedup=True)
        await self.turn_left(speedup=True)
        await self.turn_left(speedup=speedup)

    def _get_next_coord(self):
        dx, dy = 0, 0
        if self.base.facing == "E":
            dx = 1
        elif self.base.facing == "W":
            dx = -1
        elif self.base.facing == "N":
            dy = 1
        elif self.base.facing == "S":
            dy = -1
        return self.base.x + dx, self.base.y + dy
        
    def _draw_robot(self):
        ctx = self.base.robot_ctx
        ctx.clearRect(0, 0, self.world.width * CELL_SIZE, self.world.height * CELL_SIZE)
        self.world._draw_image(ctx, IMG_PATH + self.base._robot_image(),
                               self.base.x, self.base.y, CELL_SIZE, CELL_SIZE)

        # 這裡開始是調整繪圖參數
        boxes_filled = self.carrots_collected // self.BOX_SIZE
        remaining = self.carrots_collected % self.BOX_SIZE

        if self.carrots_collected > 25:
            # 當總數超過 25 時，顯示總數
            self._draw_text(ctx, str(self.carrots_collected), self.base.x, self.base.y)
        else:
            if boxes_filled > 0:
                # 繪製盒數圖示，調整位置往左上角移動
                boxes_to_draw = min(boxes_filled, 5)
                box_img = f"{boxes_to_draw}_t.png"
                # 調整 offset_x 參數，使其更靠左
                offset_x = 5 
                offset_y = 5 
                self.world._draw_image(ctx, IMG_PATH + box_img,
                                       self.base.x, self.base.y, 20, 20,
                                       offset_x=offset_x, offset_y=offset_y)
            
            if remaining > 0:
                # 繪製剩餘胡蘿蔔數圖示，調整位置往右上角移動
                carrot_img = f"carrot_{remaining}_t.png"
                # 調整 offset_x 參數，使其更靠右
                offset_x = CELL_SIZE - 25
                offset_y = 5
                self.world._draw_image(ctx, IMG_PATH + carrot_img,
                                       self.base.x, self.base.y, 20, 20,
                                       offset_x=offset_x, offset_y=offset_y)

    def _draw_text(self, ctx, text, x, y):
        ctx.font = "12px Arial"
        ctx.fillStyle = "black"
        ctx.textAlign = "right"
        ctx.textBaseline = "bottom"
        px = x * CELL_SIZE + CELL_SIZE - 5
        py = (self.world.height - 1 - y) * CELL_SIZE + CELL_SIZE - 5
        ctx.fillText(text, px, py)
        
    def background_is(self, background_type):
        coord = f"{self.base.x + 1},{self.base.y + 1}"
        has_carrot = "carrot" in self.world.objects.get(coord, {})

        if background_type == "pale_grass":
            return has_carrot
        elif background_type == "grass":
            return not has_carrot
        else:
            return False
            
    def is_visited(self):
        return (self.base.x, self.base.y) in self.visited

    def front_is_visited(self):
        dx, dy = 0, 0
        if self.base.facing == "E":
            dx = 1
        elif self.base.facing == "W":
            dx = -1
        elif self.base.facing == "N":
            dy = 1
        elif self.base.facing == "S":
            dy = -1
        next_x, next_y = self.base.x + dx, self.base.y + dy
        return (next_x, next_y) in self.visited

    def pick_carrot(self):
        if self.carrots_collected >= self.max_carrots:
            print("容量已滿，無法再採收更多農作物！")
            return
        coord = f"{self.base.x + 1},{self.base.y + 1}"
        cell = self.world.objects.get(coord, {})
        count = cell.get("carrot", 0)
        if isinstance(count, int) and count > 0:
            cell["carrot"] -= 1
            if cell["carrot"] <= 0:
                del cell["carrot"]
            self.carrots_collected += 1
            self.world.draw_objects()
            self._draw_robot()
            
            # 新增的輸出語句，計算並列印盒數
            boxes = self.carrots_collected // self.BOX_SIZE
            print(f"採收成功！目前總數: {self.carrots_collected}（盒數：{boxes}）")
        else:
            print("這裡沒有胡蘿蔔！")

    def object_here(self, obj_name="carrot"):
        return self.world.object_at_coord(self.base.x + 1, self.base.y + 1, obj_name)

    def put_carrot(self):
        if self.carrots_collected <= 0:
            print("沒有胡蘿蔔可以放置！")
            return
        coord = f"{self.base.x + 1},{self.base.y + 1}"
        cell = self.world.objects.get(coord, {})
        cell.setdefault("carrot", 0)
        cell["carrot"] += 1
        self.carrots_collected -= 1
        self.world.objects[coord] = cell
        self.world.draw_objects()
        self._draw_robot()
        print(f"放置胡蘿蔔成功！目前總數: {self.carrots_collected}")

    def put(self, obj_name="carrot"):
        if obj_name == "carrot":
            self.put_carrot()
        else:
            print(f"目前不支援放置物件：{obj_name}")

    def wall_in_front(self):
        dx, dy = 0, 0
        facing_dir = None
        if self.base.facing == "E":
            dx, facing_dir = 1, "east"
        elif self.base.facing == "W":
            dx, facing_dir = -1, "west"
        elif self.base.facing == "N":
            dy, facing_dir = 1, "north"
        elif self.base.facing == "S":
            dy, facing_dir = -1, "south"
        next_x, next_y = self.base.x + dx, self.base.y + dy
        if not (0 <= next_x < self.world.width and 0 <= next_y < self.world.height):
            return True
        current_coord = f"{self.base.x + 1},{self.base.y + 1}"
        next_coord = f"{next_x + 1},{next_y + 1}"
        opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}
        walls_here = self.world.walls.get(current_coord, [])
        walls_next = self.world.walls.get(next_coord, [])
        return facing_dir in walls_here or opposite[facing_dir] in walls_next

    def front_is_clear(self):
        return not self.wall_in_front()


async def load_scene_from_url(url):
    future = aio.Future()
    def on_complete(req):
        if req.status == 200:
            try:
                scene_data = json.loads(req.text)
                print(scene_data)
                future.set_result(scene_data)
            except Exception as e:
                print(f"解析 JSON 失敗: {e}")
                future.set_result(DEFAULT_SCENE)
        else:
            print(f"加載場景失敗: {req.status}")
            future.set_result(DEFAULT_SCENE)
    req = ajax.ajax()
    req.open('GET', url, True)
    req.bind('complete', on_complete)
    req.send()
    return await future

def get_url_parameter(name):
    query = window.location.search
    if not query:
        return None
    params = {}
    query = query[1:]
    pairs = query.split('&')
    for pair in pairs:
        if '=' in pair:
            key, value = pair.split('=', 1)
            params[key] = value
    return params.get(name)

def create_buttons(robot):
    brython_div = document["brython_div1"]
    button_container = html.DIV()
    button_container.style.marginTop = "15px"
    button_container.style.textAlign = "center"
    control_table = html.TABLE()
    def make_cell(button=None):
        td = html.TD()
        td.style.textAlign = "center"
        td.style.padding = "5px"
        if button:
            td <= button
        return td
    def make_button(label, callback):
        btn = html.BUTTON(label)
        btn.style.width = "60px"
        btn.style.height = "30px"
        btn.bind("click", lambda ev: aio.run(callback()))
        return btn
    row1 = html.TR()
    row1 <= make_cell()
    row1 <= make_cell(make_button("前進", lambda: robot.move(1)))
    row1 <= make_cell()
    control_table <= row1
    row2 = html.TR()
    row2 <= make_cell(make_button("左轉", lambda: robot.turn_left()))
    row2 <= make_cell(make_button("採收", lambda: robot.pick_carrot()))
    row2 <= make_cell(make_button("右轉", lambda: robot.turn_right()))
    control_table <= row2
    row3 = html.TR()
    row3 <= make_cell()
    row3 <= make_cell(make_button("後退", lambda: robot.move_backward()))
    row3 <= make_cell()
    control_table <= row3
    button_container <= control_table
    brython_div <= button_container

def on_key(robot, evt):
    if robot is None:
        return
    if evt.key == "j":
        aio.run(robot.move(1))
    elif evt.key == "i":
        aio.run(robot.turn_left())
    elif evt.key == "p":
        robot.pick_carrot()

def init(scene=None, enable_ui=True, robot_config=None):
    if scene is None:
        scene = DEFAULT_SCENE
    robots = scene.get("robots", [])
    walls = scene.get("walls", {})
    objects = scene.get("objects", {})
    max_x = 0
    max_y = 0
    coords = list(walls.keys()) + list(objects.keys())
    for coord in coords:
        x, y = map(int, coord.split(","))
        max_x = max(max_x, x)
        max_y = max(max_y, y)
    for r in robots:
        max_x = max(max_x, r.get("x", 1))
        max_y = max(max_y, r.get("y", 1))
    world = World(max_x, max_y, walls=walls, objects=objects)
    world.draw_objects()
    smart_robot = None
    if robots:
        rdata = robots[0]
        base_robot = AnimatedRobot(world, rdata["x"], rdata["y"], rdata.get("orientation", 0))
        
        final_robot_config = robot_config if robot_config else {}
        max_carrots = final_robot_config.get("max_carrots", 25)
        
        smart_robot = SmartRobot(base_robot, max_carrots)
        if enable_ui:
            create_buttons(smart_robot)
            document.bind("keydown", lambda evt: on_key(smart_robot, evt))
    return world, smart_robot