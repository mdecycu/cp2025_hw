from browser import document, html, timer

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
        # 清空畫布
        ctx.clearRect(0, 0, self.width * CELL_SIZE, self.height * CELL_SIZE)
        # 逐格畫背景，依是否有 carrot 決定用 pale_grass 或 grass
        for y in range(self.height):
            for x in range(self.width):
                coord = f"{x+1},{y+1}"
                if coord in self.objects and "carrot" in self.objects[coord]:
                    src = IMG_PATH + "pale_grass.png"
                else:
                    src = IMG_PATH + "grass.png"
                # 因為 drawImage 是非同步，我們用 closure 保留當前x,y,src
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
            # 北牆：最上方（貼在頂格子正上緣）
            self._draw_image(ctx, IMG_PATH + "north.png", x, self.height - 1,
                             CELL_SIZE, WALL_THICKNESS, offset_y=0)
            # 南牆：最下方（貼在底格子正下緣）
            self._draw_image(ctx, IMG_PATH + "north.png", x, 0,
                             CELL_SIZE, WALL_THICKNESS, offset_y=CELL_SIZE - WALL_THICKNESS)
        for y in range(self.height):
            # 西牆：最左邊（貼格子內側左緣）
            self._draw_image(ctx, IMG_PATH + "east.png", 0, y,
                             WALL_THICKNESS, CELL_SIZE, offset_x=0)
            # 東牆：最右邊（貼格子內側右緣）
            self._draw_image(ctx, IMG_PATH + "east.png", self.width - 1, y,
                             WALL_THICKNESS, CELL_SIZE, offset_x=CELL_SIZE - WALL_THICKNESS)

        # 額外畫場景牆面
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
                    # 畫胡蘿蔔圖像
                    self._draw_image(ctx, IMG_PATH + "carrot.png", x - 1, y - 1, CELL_SIZE, CELL_SIZE)

                    # 用數字圖片替代文字顯示數量 1_t.png 為背景透明數字
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

class AnimatedRobot:
    def __init__(self, world, x, y, orientation=0):
        self.world = world
        self.x = x - 1
        self.y = y - 1
        self.facing_order = ["E", "N", "W", "S"]
        self.facing = self.facing_order[orientation % 4]
        self.robot_ctx = world.layers["robots"].getContext("2d")
        self.trace_ctx = world.layers["traces"].getContext("2d")
        self.queue = []
        self.running = False
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

    def move(self, steps=1):
        def action(next_done):
            def step():
                nonlocal steps
                if steps == 0:
                    next_done()
                    return
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

                # 邊界檢查
                if not (0 <= next_x < self.world.width and 0 <= next_y < self.world.height):
                    print("已經撞牆，停止移動！（超出邊界）")
                    next_done()
                    return

                current_coord = f"{self.x + 1},{self.y + 1}"
                next_coord = f"{next_x + 1},{next_y + 1}"

                # 判斷目前格子是否有面向移動方向的牆壁
                walls_here = self.world.walls.get(current_coord, [])
                if facing_dir in walls_here:
                    print(f"已經撞牆，停止移動！（{current_coord} 有 {facing_dir} 牆）")
                    next_done()
                    return

                # 判斷下一格是否有面向反方向的牆壁
                opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}
                walls_next = self.world.walls.get(next_coord, [])
                if opposite[facing_dir] in walls_next:
                    print(f"已經撞牆，停止移動！（{next_coord} 有 {opposite[facing_dir]} 牆）")
                    next_done()
                    return

                # 沒有牆壁阻擋，可以移動
                self.x, self.y = next_x, next_y
                self._draw_trace(from_x, from_y, self.x, self.y)
                self._draw_robot()
                steps -= 1
                timer.set_timeout(step, 200)

            step()
        self.queue.append(action)
        self._run_queue()

    def turn_left(self):
        def action(done):
            idx = self.facing_order.index(self.facing)
            self.facing = self.facing_order[(idx + 1) % 4]
            self._draw_robot()
            timer.set_timeout(done, 300)
        self.queue.append(action)
        self._run_queue()

    def _run_queue(self):
        if self.running or not self.queue:
            return
        self.running = True
        action = self.queue.pop(0)
        action(lambda: self._done())

    def _done(self):
        self.running = False
        self._run_queue()


def init(scene=None):
    """初始化世界與機器人，若無場景資料則用預設"""
    if scene is None:
        scene = DEFAULT_SCENE

    robots = scene.get("robots", [])
    walls = scene.get("walls", {})
    objects = scene.get("objects", {})

    # 自動計算畫布大小 (最大x,最大y)
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

    # 只初始化第一台機器人
    if robots:
        rdata = robots[0]
        robot = AnimatedRobot(world, rdata["x"], rdata["y"], rdata.get("orientation", 0))
    else:
        robot = None
    return world, robot
