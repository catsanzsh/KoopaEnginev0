from ursina import *
from ursina.shaders import lit_with_shadows_shader
from random import randint
import math

app = Ursina()
# Game states
class GameState:
    MENU = 0
    PLAYING = 1
    PAUSED = 2

current_state = GameState.MENU

class MainMenu(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='quad',
            scale=(2, 1),
            color=color.clear,
            position=(0, 0, 0)
        )
        self.background = Entity(
            parent=self,
            model='quad',
            texture='white_cube',
            color=color.black66,
            scale=(2, 1),
            position=(0, 0, 0.01)
        )
        self.title = Text(
            parent=self,
            text='PROJECT SM64 DREAMIN EDITION',
            scale=3,
            position=(0, 0.3, -0.1),
            origin=(0, 0),
            color=color.yellow
        )
        self.subtitle = Text(
            parent=self,
            text='M1 MAC PORT',
            scale=2,
            position=(0, 0.2, -0.1),
            origin=(0, 0),
            color=color.white
        )
        button_y_positions = [0.05, -0.05, -0.15, -0.25]
        button_texts = ['Play', 'Settings', 'Credits', 'Quit']
        button_colors = [color.green, color.azure, color.orange, color.red]
        self.buttons = []
        for i, (text, y_pos, btn_color) in enumerate(zip(button_texts, button_y_positions, button_colors)):
            btn = Button(
                parent=self,
                text=text,
                scale=(0.3, 0.08),
                position=(0, y_pos, -0.1),
                color=btn_color,
                highlight_color=color.white66
            )
            self.buttons.append(btn)
        self.buttons[0].on_click = self.start_game
        self.buttons[1].on_click = self.show_settings
        self.buttons[2].on_click = self.show_credits
        self.buttons[3].on_click = self.quit_game
        self.star = Entity(
            parent=self,
            model='circle',  # Changed back to 2D circle for UI
            color=color.yellow,
            scale=0.05,
            position=(0.6, 0.3, -0.05)
        )
        self.t = 0

    def update(self):
        self.t += time.dt
        self.star.x = 0.6 + math.sin(self.t * 2) * 0.1
        self.star.y = 0.3 + math.cos(self.t * 3) * 0.05
        self.star.rotation_z += 100 * time.dt

    def start_game(self):
        global current_state
        current_state = GameState.PLAYING
        self.disable()
        start_game()

    def show_settings(self):
        print("Settings menu would appear here")

    def show_credits(self):
        self.disable()
        credits_menu.enable()

    def quit_game(self):
        application.quit()

class CreditsMenu(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='quad',
            scale=(2, 1),
            color=color.clear,
            position=(0, 0, 0),
            enabled=False
        )
        self.background = Entity(
            parent=self,
            model='quad',
            color=color.black66,
            scale=(2, 1),
            position=(0, 0, 0.01)
        )
        self.title = Text(
            parent=self,
            text='CREDITS',
            scale=3,
            position=(0, 0.3, -0.1),
            origin=(0, 0),
            color=color.yellow
        )
        credit_text = """Game Development: You
Inspired by: Super Mario 64
Engine: Ursina
Main Menu Added by: CatGPT"""
        self.credits = Text(
            parent=self,
            text=credit_text,
            scale=1.5,
            position=(0, -0.2, -0.1),
            origin=(0, 0),
            color=color.white
        )
        self.back_button = Button(
            parent=self,
            text='Back to Menu',
            scale=(0.3, 0.08),
            position=(0, -0.35, -0.1),
            color=color.red,
            highlight_color=color.white66
        )
        self.back_button.on_click = self.back_to_menu

    def back_to_menu(self):
        self.disable()
        main_menu.enable()

def setup_scene():
    global ground, mountain, chomp, boulders, bobombs, bridge, floating_island, power_star, score_text
    window.color = color.light_gray
    ground = Entity(
        model='plane', 
        scale=(50,1,50), 
        texture='white_cube', 
        texture_scale=(10,10), 
        collider='box'
    )
    mountain = MountainTerrain()
    chomp = ChainChomp()
    boulders = [RollingBoulder((x*10,5,40), (x*10,5,55)) for x in range(-2,3)]
    bobombs = [Bobomb((randint(-20,20),3,randint(25,45))) for _ in range(10)]
    bridge = Entity(
        model='cube', 
        scale=(15,0.2,3), 
        position=(0,8,25),
        texture='white_cube',
        collider='box',
        rotation=(0,0,5)
    )
    floating_island = Entity(
        model='cube',
        scale=(5,1,5),
        position=(0,25,40),
        texture='white_cube',
        collider='box'
    )
    power_star = Entity(
        model='sphere',
        color=color.yellow,
        scale=0.5,
        position=floating_island.position + Vec3(0,2,0),
        collider='mesh'
    )
    score_text = Text(text='Stars: 0', position=(-0.85, 0.45), origin=(-0.5,-0.5))
    Sky(texture='sky_default')

class Player(Entity):
    def __init__(self):
        super().__init__(
            model='cube',
            color=color.red,
            scale=(1,2,1),
            position=(0,5,0),
            collider='box',
            shader=lit_with_shadows_shader
        )
        self.speed = 8
        self.jump_height = 6
        self.gravity = 1.5
        self.velocity = Vec3(0,0,0)
        self.camera_pivot = Entity(parent=self, y=2)
        self.grounded = False
        self.invincible = False
        self.invincible_timer = 0
        camera.parent = self.camera_pivot
        camera.position = (0, 1, -8)
        camera.rotation = (15, 0, 0)

    def update(self):
        if current_state != GameState.PLAYING:
            return
        movement = self.camera_pivot.forward * (held_keys['w'] - held_keys['s']) + \
                   self.camera_pivot.right * (held_keys['d'] - held_keys['a'])
        if movement.length() > 0:
            movement = movement.normalized()
        self.velocity.x = movement.x * self.speed
        self.velocity.z = movement.z * self.speed
        self.velocity.y -= self.gravity * time.dt  # Fixed gravity calculation [[6]]
        self.grounded = self.intersects(ground).hit
        if self.grounded and self.velocity.y < 0:
            self.velocity.y = 0
        self.position += self.velocity * time.dt
        if self.y < -10:
            self.position = (0,10,0)
            self.velocity = Vec3(0,0,0)  # Reset velocity on respawn [[7]]
            self.invincible = True
            self.invincible_timer = 2
        self.camera_pivot.rotation_y += mouse.velocity[0] * 30
        self.camera_pivot.rotation_x = clamp(
            self.camera_pivot.rotation_x - mouse.velocity[1] * 30,
            -60, 60
        )
        if self.invincible:
            self.invincible_timer -= time.dt
            if self.invincible_timer <= 0:
                self.invincible = False

    def input(self, key):
        if current_state != GameState.PLAYING:
            return
        if key == 'space' and self.grounded:
            self.velocity.y = self.jump_height
        if key == 'escape':
            global current_state
            current_state = GameState.MENU
            mouse.locked = False
            main_menu.enable()

class MountainTerrain(Entity):
    def __init__(self):
        super().__init__(
            model='cube',
            scale=(30,10,30),
            position=(0,5,30),
            rotation=(0,0,15),
            texture='white_cube',
            collider='mesh'
        )

class Bobomb(Entity):
    def __init__(self, position):
        super().__init__(
            model='sphere',
            color=color.black,
            scale=0.8,
            position=position,
            collider='sphere'
        )
        self.speed = 2.5

    def update(self):
        if current_state != GameState.PLAYING:
            return
        self.rotation_y += 70 * time.dt
        if distance(self, player) < 5 and not player.invincible:
            direction = (player.position - self.position).normalized()
            self.position += direction * self.speed * time.dt  # Fixed movement vector [[3]]

class ChainChomp(Entity):
    def __init__(self):
        super().__init__(
            model='sphere',
            color=color.black,
            scale=1.5,
            position=(10,3,15),
            collider='sphere'
        )
        self.chain = [Entity(model='sphere', color=color.gray, scale=0.15) for _ in range(8)]
        self.anchor = Entity(position=(10,5,15))
        self.t = 0

    def update(self):
        if current_state != GameState.PLAYING:
            return
        self.t += time.dt * 1.5
        self.position = self.anchor.position + Vec3(math.sin(self.t*2)*4, 0, math.cos(self.t*2)*4)
        for i, link in enumerate(self.chain):
            link.position = lerp(self.anchor.position, self.position, i/len(self.chain))

class RollingBoulder(Entity):
    def __init__(self, path_start, path_end):
        super().__init__(
            model='sphere',
            texture='white_cube',
            scale=2,
            position=path_start,
            collider='sphere'
        )
        self.path = [path_start, path_end]
        self.speed = 4
        self.direction = 1

    def update(self):
        if current_state != GameState.PLAYING:
            return
        target = self.path[0] if self.direction == -1 else self.path[1]
        direction = (target - self.position).normalized()
        self.position += direction * self.speed * time.dt  # Fixed movement logic [[3]]
        self.rotation_y += 150 * time.dt
        if distance(self, target) < 1:
            self.direction *= -1

score = 0
player = None
main_menu = MainMenu()
credits_menu = CreditsMenu()
ground = None
mountain = None
chomp = None
boulders = None
bobombs = None
bridge = None
floating_island = None
power_star = None
score_text = None

def update():
    if current_state != GameState.PLAYING:
        return
    global score
    hit_info = player.intersects()
    if hit_info.hit:
        if hit_info.entity == power_star:
            score += 1
            score_text.text = f'Stars: {score}'
            power_star.blink(color.white, duration=0.5)
            # Fixed star respawn position [[5]]
            power_star.position = Vec3(randint(-20,20), 5, randint(25,45)) 
        elif isinstance(hit_info.entity, Bobomb) and not player.invincible:
            player.position = Vec3(0,10,0)
            player.velocity = Vec3(0,0,0)  # Reset velocity on hit [[7]]
            player.invincible = True
            player.invincible_timer = 2
            destroy(hit_info.entity)
            bobombs.remove(hit_info.entity)

def start_game():
    global player, score
    score = 0
    setup_scene()
    player = Player()
    mouse.locked = True

app.run()
