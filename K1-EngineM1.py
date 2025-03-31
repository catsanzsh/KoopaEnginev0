#!/usr/bin/env python3
"""
Bob-omb Battlefield-Inspired Mini Game in Ursina

Note for M1 Mac users:
- If you encounter issues, run Python under Rosetta 2.
- e.g. Right-click Terminal -> Get Info -> "Open using Rosetta".
"""

from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math, time, random

app = Ursina()
window.title = "Mini Bob-omb Battlefield"
window.borderless = False

# -------------------------------------------------------------------
# GLOBAL VARIABLES
# -------------------------------------------------------------------
game_running = False
player = None
health = 0
score = 0

spawn_point = Vec3(0, 5, 0)
game_entities = []
hazards = []
boss = None
star_entity = None

# HUD
health_text = None
score_text = None

# Invulnerability
last_hit_time = 0
INVULN_DURATION = 1.0

# -------------------------------------------------------------------
# UI SETUP
# -------------------------------------------------------------------
menu_ui = Entity(parent=camera.ui)
title_text = Text("Super Ursina 64\n(Bob-omb Battlefield)", parent=menu_ui, origin=(0,0), y=0.3, scale=2)
start_button = Button(text="Start Game", parent=menu_ui, color=color.azure, scale=(0.2, 0.075), y=0)
quit_button = Button(text="Quit", parent=menu_ui, color=color.azure, scale=(0.2, 0.075), y=-0.1)

pause_menu = Entity(parent=camera.ui, enabled=False, ignore_paused=True)
pause_text = Text("PAUSED", parent=pause_menu, origin=(0,0), scale=2, y=0.1)
resume_button = Button(text="Resume", parent=pause_menu, color=color.orange, scale=(0.18, 0.07), y=0)
menu_button = Button(text="Main Menu", parent=pause_menu, color=color.orange, scale=(0.18, 0.07), y=-0.1)

for ui_element in pause_menu.children:
    ui_element.ignore_paused = True

# -------------------------------------------------------------------
# FUNCTIONS
# -------------------------------------------------------------------
def start_game():
    global game_running, player, health, score, health_text, score_text
    global game_entities, hazards, boss, star_entity

    menu_ui.enabled = False
    game_running = True

    # Reset game state
    health = 3
    score = 0
    for ent in game_entities:  # Clear existing entities
        destroy(ent)
    game_entities.clear()
    hazards.clear()
    if boss: destroy(boss)
    if star_entity: destroy(star_entity)
    boss = None
    star_entity = None

    create_level_geometry()
    Sky()

    player = FirstPersonController(
        model='cube',
        scale=(1,1.7,1),
        origin_y=-0.5,
        collider='box',
        speed=6,
        position=spawn_point
    )
    player.gravity = 1
    player.cursor.visible = False
    game_entities.append(player)

    spawn_boulders()
    spawn_chain_chomp()

    boss = Entity(
        model='sphere',
        color=color.magenta,
        collider='sphere',
        scale=2,
        position=(0, 6.5, 25),
        name="Big Bob-omb"
    )
    game_entities.append(boss)

    # Initialize HUD
    if health_text: destroy(health_text)
    if score_text: destroy(score_text)
    health_text = Text(f"Health: {health}", parent=camera.ui, origin=(-0.5, 0.5), scale=1.5, position=(-0.4, 0.45))
    score_text = Text(f"Stars: {score}", parent=camera.ui, origin=(0.5, 0.5), scale=1.5, position=(0.4, 0.45))

    application.paused = False
    pause_menu.enabled = False
    mouse.locked = True

def create_level_geometry():
    ground = Entity(
        model='plane',
        texture='grass',
        texture_scale=(50,50),
        collider='mesh',
        scale=(50,1,50),
        color=color.lime.tint(-.25),
        position=(0,0,0)
    )
    game_entities.append(ground)

    for i in range(1,6):
        step = Entity(
            model='plane',
            collider='mesh',
            texture='grass',
            texture_scale=(8,8),
            scale=(8,1,8),
            position=(0,i*1.2,i*5),
            color=color.lime.tint(-.25 + i*0.03)
        )
        game_entities.append(step)

    for x in range(-25,26,5):
        fence_post = Entity(
            model='cube',
            collider='box',
            scale=(0.5,3,0.5),
            color=color.brown,
            position=(x,1,-25)
        )
        game_entities.append(fence_post)

def spawn_boulders():
    for i in range(3):
        boulder = Entity(
            model='sphere',
            color=color.gray,
            collider='sphere',
            scale=1.5,
            position=(random.uniform(-2,2), 7, 25+random.uniform(-1,1)),
            name=f"Boulder{i}"
        )
        hazards.append(boulder)
        game_entities.append(boulder)

def spawn_chain_chomp():
    chomp = Entity(
        model='sphere',
        color=color.black,
        collider='sphere',
        scale=2,
        position=(-10,1,5),
        name="Chain Chomp"
    )
    hazards.append(chomp)
    game_entities.append(chomp)

def cleanup_game():
    global player, health_text, score_text, game_entities, hazards, boss, star_entity
    for ent in game_entities[:]:  # Use copy to avoid modification during iteration
        destroy(ent)
    game_entities.clear()
    hazards.clear()
    if boss: destroy(boss)
    if star_entity: destroy(star_entity)
    if health_text: destroy(health_text)
    if score_text: destroy(score_text)
    boss = None
    star_entity = None
    health_text = None
    score_text = None
    if player:
        destroy(player)
        player = None

def game_over(message="Game Over"):
    global game_running
    game_running = False
    application.paused = False
    mouse.locked = False
    end_color = color.red if "Over" in message else color.yellow
    end_text = Text(message, parent=camera.ui, origin=(0,0), scale=2, color=end_color)
    invoke(go_to_menu, delay=2)
    invoke(destroy, end_text, delay=2)

def go_to_menu():
    cleanup_game()
    menu_ui.enabled = True
    pause_menu.enabled = False
    application.paused = False
    mouse.locked = False

def toggle_pause():
    if not game_running:
        return
    if application.paused:
        pause_menu.enabled = False
        application.paused = False
        mouse.locked = True
    else:
        application.paused = True
        pause_menu.enabled = True
        mouse.locked = False

# -------------------------------------------------------------------
# BUTTON HANDLERS
# -------------------------------------------------------------------
start_button.on_click = start_game
quit_button.on_click = application.quit
resume_button.on_click = toggle_pause
menu_button.on_click = go_to_menu

# -------------------------------------------------------------------
# PAUSE HANDLER
# -------------------------------------------------------------------
pause_handler = Entity(ignore_paused=True)
def pause_handler_input(key):
    if key == 'escape':
        toggle_pause()
pause_handler.input = pause_handler_input

# -------------------------------------------------------------------
# UPDATE LOOP
# -------------------------------------------------------------------
def update():
    global health, score, last_hit_time, star_entity

    if not game_running or application.paused:
        return

    if player and player.y < -10:
        damage_player(1)
        if health <= 0:
            game_over("Game Over")
            return
        respawn_player()

    animate_hazards()
    handle_boss_encounter()
    check_collisions()

    if star_entity and player and star_entity.enabled:
        if distance(player, star_entity) < 1:
            score += 1
            score_text.text = f"Stars: {score}"
            destroy(star_entity)
            star_entity = None
            game_over("You got the Star!")

def damage_player(amount):
    global health, last_hit_time
    current_time = time.time()
    if current_time - last_hit_time < INVULN_DURATION:
        return
    health -= amount
    health_text.text = f"Health: {health}"
    if player:
        player.blink(color.red)
    last_hit_time = current_time

def respawn_player():
    if player and health > 0:
        player.position = spawn_point
        player.rotation = Vec3(0,0,0)

def animate_hazards():
    for hazard in hazards[:]:  # Use copy to avoid modification during iteration
        if not hazard.enabled:
            continue
        if "Boulder" in hazard.name:
            hazard.z -= 4 * time.dt
            hazard.rotation_x += 180 * time.dt
            if hazard.z < -10:
                hazard.position = (random.uniform(-2,2), 7, 25+random.uniform(-1,1))
        elif hazard.name == "Chain Chomp":
            hazard.rotation_y += 120 * time.dt
            hazard.x = -10 + math.sin(time.time()) * 3

def check_collisions():
    if not player or not player.enabled:
        return
    current_time = time.time()
    for hazard in hazards[:]:
        if not hazard.enabled:
            continue
        if distance(player, hazard) < (hazard.scale_x/2 + 0.7):
            damage_player(1)
            if health <= 0:
                game_over("Game Over")
                return

def handle_boss_encounter():
    global boss, star_entity
    if not boss or not boss.enabled or not player:
        return

    dist_to_boss = distance(player, boss)
    if not hasattr(boss, 'hp'):
        boss.hp = 3

    boss.rotation_y += 40 * time.dt

    if dist_to_boss < 3 and boss.hp > 0:
        boss.hp -= 1
        boss.blink(color.red)
        knockback = (player.position - boss.position).normalized() * 2
        player.position += knockback
        if boss.hp <= 0:
            spawn_star_at(boss.position + Vec3(0, 3, 0))
            destroy(boss)
            boss = None
            confetti = Entity(
                model='quad',
                texture='white_cube',
                color=color.random_color(),
                position=boss.position if boss else Vec3(0, 6.5, 25),
                scale=10
            )
            destroy(confetti, delay=1)

def spawn_star_at(position):
    global star_entity
    if star_entity:
        destroy(star_entity)
    star_entity = Entity(
        model='sphere',
        color=color.yellow,
        scale=1,
        position=position
    )
    def star_spin():
        if star_entity and star_entity.enabled:
            star_entity.rotation_y += 90 * time.dt
            star_entity.y = position.y + math.sin(time.time()*4)*0.5
    star_entity.update = star_spin
    game_entities.append(star_entity)

# -------------------------------------------------------------------
# RUN
# -------------------------------------------------------------------
app.run()