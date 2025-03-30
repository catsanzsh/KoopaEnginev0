from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math, time

# Initialize the Ursina app and window
app = Ursina()
window.title = "Ursina Mario-style Game"
window.borderless = False  # Windowed mode for easier compatibility

# Game state variables
game_running = False
player = None
health = 0
score = 0
spawn_point = Vec3(0, 1, 0)  # Player spawn position (x, y, z)

# Main Menu UI setup
menu_ui = Entity(parent=camera.ui)
title_text = Text("Super Ursina 64", parent=menu_ui, origin=(0,0), y=0.3, scale=2)
start_button = Button(text="Start Game", parent=menu_ui, color=color.azure, scale=(0.2, 0.075), y=0, x=0)
quit_button = Button(text="Quit", parent=menu_ui, color=color.azure, scale=(0.2, 0.075), y=-0.1, x=0)

# Pause Menu UI setup (initially hidden)
pause_menu = Entity(parent=camera.ui, enabled=False, ignore_paused=True)
pause_text = Text("PAUSED", parent=pause_menu, origin=(0,0), scale=2, y=0.1)
resume_button = Button(text="Resume", parent=pause_menu, color=color.orange, scale=(0.18, 0.07), y=0, x=0)
menu_button = Button(text="Main Menu", parent=pause_menu, color=color.orange, scale=(0.18, 0.07), y=-0.1, x=0)
# Ensure pause menu elements respond while game is paused
for ui_element in pause_menu.children:
    ui_element.ignore_paused = True

# HUD elements (will be created when game starts)
health_text = None
score_text = None

# Lists for game entities to manage cleanup
game_entities = []
hazards = []
star_entity = None

def start_game():
    """Start the game: initialize level, player, hazards, and HUD."""
    global game_running, player, health, score, health_text, score_text, game_entities, hazards, star_entity
    # Hide main menu
    menu_ui.enabled = False
    game_running = True
    # Reset game state
    health = 3
    score = 0
    hazards = []
    game_entities = []
    star_entity = None
    # Create environment (ground and sky)
    ground = Entity(model='plane', texture='grass', collider='box', scale=50, color=color.green)
    game_entities.append(ground)
    Sky()  # nice sky background
    # Create player (FirstPersonController for movement)
    player = FirstPersonController(model='cube', y=spawn_point.y, origin_y=-0.5, collider='box', speed=5)
    player.position = spawn_point
    player.cursor.visible = False   # hide crosshair for aesthetics
    player.gravity = 1             # normal gravity
    # Create hazards (a rolling boulder and a Chain Chomp-like enemy)
    boulder = Entity(model='sphere', color=color.gray, collider='sphere', scale=1, position=(5, 0.5, 0))
    chain_chomp = Entity(model='sphere', color=color.black, collider='sphere', scale=1.5, position=(0, 0.75, 4))
    hazards.extend([boulder, chain_chomp])
    game_entities.extend([player, boulder, chain_chomp])
    # Create a collectible power star
    star_entity = Entity(model='sphere', color=color.yellow, scale=0.5, position=(0, 1.5, 8))
    game_entities.append(star_entity)
    # Create HUD texts for health and score
    health_text = Text(f"Health: {health}", parent=camera.ui, origin=(-0.5, 0.5), scale=1.5, position=(-0.4, 0.45))
    score_text = Text(f"Stars: {score}", parent=camera.ui, origin=(0.5, 0.5), scale=1.5, position=(0.4, 0.45))
    # Lock mouse for first-person control
    mouse.locked = True
    # Ensure game is unpaused and pause menu is hidden at start
    application.paused = False
    pause_menu.enabled = False
    print("Game started: Health =", health, "Score =", score)

def cleanup_game():
    """Destroy all game entities and HUD elements (for resetting or exiting the game)."""
    global player, health_text, score_text, game_entities, hazards, star_entity
    for ent in game_entities:
        if ent:
            destroy(ent)
    game_entities.clear()
    hazards.clear()
    star_entity = None
    if health_text:
        destroy(health_text)
    if score_text:
        destroy(score_text)
    player = None

def game_over(message="Game Over"):
    """Handle end-of-game events (either losing all health or winning by collecting star)."""
    global game_running
    game_running = False
    application.paused = False    # ensure not paused
    mouse.locked = False         # free mouse for menu or exit
    # Display end-of-game message
    end_color = color.red if "Over" in message else color.yellow
    end_text = Text(message, parent=camera.ui, origin=(0,0), scale=2, color=end_color)
    print(message)
    # Schedule return to main menu after a short delay
    invoke(go_to_menu, delay=2)
    invoke(destroy, end_text, delay=2)  # remove message after showing

def go_to_menu():
    """Return to the main menu, resetting the game state."""
    global game_running
    cleanup_game()
    menu_ui.enabled = True
    pause_menu.enabled = False
    application.paused = False
    mouse.locked = False
    game_running = False
    print("Returned to main menu. Game reset.")

# Button event bindings
start_button.on_click = start_game
quit_button.on_click = application.quit
resume_button.on_click = lambda: toggle_pause()
menu_button.on_click = lambda: (application.resume(), go_to_menu())

def toggle_pause():
    """Toggle game pause state and show/hide pause menu."""
    if not game_running:
        return
    if application.paused:
        # Resume the game
        pause_menu.enabled = False
        application.resume()   # application.paused = False
        mouse.locked = True    # lock cursor again for gameplay
    else:
        # Pause the game
        application.pause()    # application.paused = True
        pause_menu.enabled = True
        mouse.locked = False   # unlock cursor for UI

# Pause handler to catch 'Escape' key events for pausing/resuming and quitting
pause_handler = Entity(ignore_paused=True)
def pause_handler_input(key):
    if key == 'escape':
        if application.paused:
            # If game is paused, pressing Esc resumes it (same as clicking Resume)
            toggle_pause()
        else:
            if game_running:
                # In game and not paused -> pause the game
                toggle_pause()
            else:
                # At main menu and not in game -> quit the app
                application.quit()
pause_handler.input = pause_handler_input

# Variables for damage cooldown (invulnerability frames)
last_hit_time = 0
invuln_duration = 1.0  # 1 second of invincibility after getting hit

def update():
    """Main game loop: handle movement, collisions, and game logic each frame."""
    global health, score, last_hit_time
    if not game_running:
        return  # Only run game logic if game is active
    if application.paused:
        return  # Skip game updates while paused

    # 1. Handle player falling off the map
    if player and player.y < -10:
        health -= 1
        if health_text:
            health_text.text = f"Health: {health}"
        if health <= 0:
            # No health left, trigger game over
            game_over("Game Over")
            return
        # Respawn player at start and give temporary invulnerability
        player.position = spawn_point
        player.rotation = Vec3(0, 0, 0)
        player.y = spawn_point.y  # ensure above ground
        last_hit_time = time.time()  # reset invulnerability timer
        print("Player fell. Respawned at start. Health now", health)

    # 2. Move and animate hazards (boulder and Chain Chomp)
    if len(hazards) > 0:
        boulder = hazards[0]
        # Boulder rolls from right to left and resets
        boulder.x -= 3 * time.dt
        boulder.rotation_z += 360 * time.dt * 0.5  # rotate for rolling effect
        if boulder.x < -5:
            boulder.x = 5  # loop back to start position
    if len(hazards) > 1:
        chomp = hazards[1]
        # Chain Chomp oscillates in place (simulating a tethered movement)
        chomp.rotation_y = math.sin(time.time() * 2) * 30

    # 3. Animate the power star (spin and bobbing motion)
    if star_entity:
        star_entity.rotation_y += 90 * time.dt
        star_entity.y = 1.5 + math.sin(time.time() * 2) * 0.2

    # 4. Check for player collisions with hazards (boulders or chomp)
    if player:
        current_time = time.time()
        if current_time - last_hit_time > invuln_duration:
            # Only check for damage if invincibility period passed
            for hazard in hazards:
                if hazard and hazard.collider:
                    hit_info = player.intersects(hazard)
                    if hit_info.hit or distance(player, hazard) < (hazard.scale_x + 0.5):
                        # Player is in contact with hazard
                        health -= 1
                        if health_text:
                            health_text.text = f"Health: {health}"
                        last_hit_time = current_time  # start invincibility cooldown
                        print("Player hit by hazard. Health now", health)
                        if health <= 0:
                            game_over("Game Over")
                            return
                        # Briefly flash the player red to indicate damage
                        player.blink(color.red)
                        break  # ensure only one hit is processed this frame

    # 5. Check for star collection
    if star_entity and player:
        if distance(player, star_entity) < 1:
            # Player collected the star
            score += 1
            if score_text:
                score_text.text = f"Stars: {score}"
            destroy(star_entity)    # remove the star from the scene
            star_entity.disable()   # ensure it's truly gone
            print(f"Collected the Power Star! Score is now {score}.")
            # Trigger win state
            game_over("You got the Star!")

# Start the app
app.run()
from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math, time

# Initialize the Ursina app and window
app = Ursina()
window.title = "Ursina Mario-style Game"
window.borderless = False  # Windowed mode for easier compatibility

# Game state variables
game_running = False
player = None
health = 0
score = 0
spawn_point = Vec3(0, 1, 0)  # Player spawn position (x, y, z)

# Main Menu UI setup
menu_ui = Entity(parent=camera.ui)
title_text = Text("Super Ursina 64", parent=menu_ui, origin=(0,0), y=0.3, scale=2)
start_button = Button(text="Start Game", parent=menu_ui, color=color.azure, scale=(0.2, 0.075), y=0, x=0)
quit_button = Button(text="Quit", parent=menu_ui, color=color.azure, scale=(0.2, 0.075), y=-0.1, x=0)

# Pause Menu UI setup (initially hidden)
pause_menu = Entity(parent=camera.ui, enabled=False, ignore_paused=True)
pause_text = Text("PAUSED", parent=pause_menu, origin=(0,0), scale=2, y=0.1)
resume_button = Button(text="Resume", parent=pause_menu, color=color.orange, scale=(0.18, 0.07), y=0, x=0)
menu_button = Button(text="Main Menu", parent=pause_menu, color=color.orange, scale=(0.18, 0.07), y=-0.1, x=0)
# Ensure pause menu elements respond while game is paused
for ui_element in pause_menu.children:
    ui_element.ignore_paused = True

# HUD elements (will be created when game starts)
health_text = None
score_text = None

# Lists for game entities to manage cleanup
game_entities = []
hazards = []
star_entity = None

def start_game():
    """Start the game: initialize level, player, hazards, and HUD."""
    global game_running, player, health, score, health_text, score_text, game_entities, hazards, star_entity
    # Hide main menu
    menu_ui.enabled = False
    game_running = True
    # Reset game state
    health = 3
    score = 0
    hazards = []
    game_entities = []
    star_entity = None
    # Create environment (ground and sky)
    ground = Entity(model='plane', texture='grass', collider='box', scale=50, color=color.green)
    game_entities.append(ground)
    Sky()  # nice sky background
    # Create player (FirstPersonController for movement)
    player = FirstPersonController(model='cube', y=spawn_point.y, origin_y=-0.5, collider='box', speed=5)
    player.position = spawn_point
    player.cursor.visible = False   # hide crosshair for aesthetics
    player.gravity = 1             # normal gravity
    # Create hazards (a rolling boulder and a Chain Chomp-like enemy)
    boulder = Entity(model='sphere', color=color.gray, collider='sphere', scale=1, position=(5, 0.5, 0))
    chain_chomp = Entity(model='sphere', color=color.black, collider='sphere', scale=1.5, position=(0, 0.75, 4))
    hazards.extend([boulder, chain_chomp])
    game_entities.extend([player, boulder, chain_chomp])
    # Create a collectible power star
    star_entity = Entity(model='sphere', color=color.yellow, scale=0.5, position=(0, 1.5, 8))
    game_entities.append(star_entity)
    # Create HUD texts for health and score
    health_text = Text(f"Health: {health}", parent=camera.ui, origin=(-0.5, 0.5), scale=1.5, position=(-0.4, 0.45))
    score_text = Text(f"Stars: {score}", parent=camera.ui, origin=(0.5, 0.5), scale=1.5, position=(0.4, 0.45))
    # Lock mouse for first-person control
    mouse.locked = True
    # Ensure game is unpaused and pause menu is hidden at start
    application.paused = False
    pause_menu.enabled = False
    print("Game started: Health =", health, "Score =", score)

def cleanup_game():
    """Destroy all game entities and HUD elements (for resetting or exiting the game)."""
    global player, health_text, score_text, game_entities, hazards, star_entity
    for ent in game_entities:
        if ent:
            destroy(ent)
    game_entities.clear()
    hazards.clear()
    star_entity = None
    if health_text:
        destroy(health_text)
    if score_text:
        destroy(score_text)
    player = None

def game_over(message="Game Over"):
    """Handle end-of-game events (either losing all health or winning by collecting star)."""
    global game_running
    game_running = False
    application.paused = False    # ensure not paused
    mouse.locked = False         # free mouse for menu or exit
    # Display end-of-game message
    end_color = color.red if "Over" in message else color.yellow
    end_text = Text(message, parent=camera.ui, origin=(0,0), scale=2, color=end_color)
    print(message)
    # Schedule return to main menu after a short delay
    invoke(go_to_menu, delay=2)
    invoke(destroy, end_text, delay=2)  # remove message after showing

def go_to_menu():
    """Return to the main menu, resetting the game state."""
    global game_running
    cleanup_game()
    menu_ui.enabled = True
    pause_menu.enabled = False
    application.paused = False
    mouse.locked = False
    game_running = False
    print("Returned to main menu. Game reset.")

# Button event bindings
start_button.on_click = start_game
quit_button.on_click = application.quit
resume_button.on_click = lambda: toggle_pause()
menu_button.on_click = lambda: (application.resume(), go_to_menu())

def toggle_pause():
    """Toggle game pause state and show/hide pause menu."""
    if not game_running:
        return
    if application.paused:
        # Resume the game
        pause_menu.enabled = False
        application.resume()   # application.paused = False
        mouse.locked = True    # lock cursor again for gameplay
    else:
        # Pause the game
        application.pause()    # application.paused = True
        pause_menu.enabled = True
        mouse.locked = False   # unlock cursor for UI

# Pause handler to catch 'Escape' key events for pausing/resuming and quitting
pause_handler = Entity(ignore_paused=True)
def pause_handler_input(key):
    if key == 'escape':
        if application.paused:
            # If game is paused, pressing Esc resumes it (same as clicking Resume)
            toggle_pause()
        else:
            if game_running:
                # In game and not paused -> pause the game
                toggle_pause()
            else:
                # At main menu and not in game -> quit the app
                application.quit()
pause_handler.input = pause_handler_input

# Variables for damage cooldown (invulnerability frames)
last_hit_time = 0
invuln_duration = 1.0  # 1 second of invincibility after getting hit

def update():
    """Main game loop: handle movement, collisions, and game logic each frame."""
    global health, score, last_hit_time
    if not game_running:
        return  # Only run game logic if game is active
    if application.paused:
        return  # Skip game updates while paused

    # 1. Handle player falling off the map
    if player and player.y < -10:
        health -= 1
        if health_text:
            health_text.text = f"Health: {health}"
        if health <= 0:
            # No health left, trigger game over
            game_over("Game Over")
            return
        # Respawn player at start and give temporary invulnerability
        player.position = spawn_point
        player.rotation = Vec3(0, 0, 0)
        player.y = spawn_point.y  # ensure above ground
        last_hit_time = time.time()  # reset invulnerability timer
        print("Player fell. Respawned at start. Health now", health)

    # 2. Move and animate hazards (boulder and Chain Chomp)
    if len(hazards) > 0:
        boulder = hazards[0]
        # Boulder rolls from right to left and resets
        boulder.x -= 3 * time.dt
        boulder.rotation_z += 360 * time.dt * 0.5  # rotate for rolling effect
        if boulder.x < -5:
            boulder.x = 5  # loop back to start position
    if len(hazards) > 1:
        chomp = hazards[1]
        # Chain Chomp oscillates in place (simulating a tethered movement)
        chomp.rotation_y = math.sin(time.time() * 2) * 30

    # 3. Animate the power star (spin and bobbing motion)
    if star_entity:
        star_entity.rotation_y += 90 * time.dt
        star_entity.y = 1.5 + math.sin(time.time() * 2) * 0.2

    # 4. Check for player collisions with hazards (boulders or chomp)
    if player:
        current_time = time.time()
        if current_time - last_hit_time > invuln_duration:
            # Only check for damage if invincibility period passed
            for hazard in hazards:
                if hazard and hazard.collider:
                    hit_info = player.intersects(hazard)
                    if hit_info.hit or distance(player, hazard) < (hazard.scale_x + 0.5):
                        # Player is in contact with hazard
                        health -= 1
                        if health_text:
                            health_text.text = f"Health: {health}"
                        last_hit_time = current_time  # start invincibility cooldown
                        print("Player hit by hazard. Health now", health)
                        if health <= 0:
                            game_over("Game Over")
                            return
                        # Briefly flash the player red to indicate damage
                        player.blink(color.red)
                        break  # ensure only one hit is processed this frame

    # 5. Check for star collection
    if star_entity and player:
        if distance(player, star_entity) < 1:
            # Player collected the star
            score += 1
            if score_text:
                score_text.text = f"Stars: {score}"
            destroy(star_entity)    # remove the star from the scene
            star_entity.disable()   # ensure it's truly gone
            print(f"Collected the Power Star! Score is now {score}.")
            # Trigger win state
            game_over("You got the Star!")

# Start the app
app.run()
