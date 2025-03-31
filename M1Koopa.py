from ursina import Ursina, Entity, Button, camera, Func, Text, color, application

# Initialize Ursina app
app = Ursina()

# Menu parent entities
menu_parent = Entity(parent=camera.ui)  # Holds all menu UI elements
main_menu = Entity(parent=menu_parent)
file_select_menu = Entity(parent=menu_parent, enabled=False)

def start_game(file_slot=None):
    """Hide menus and launch the demo scene"""
    menu_parent.enabled = False  # Disable the menu system
    player.enabled = True  # Enable the player entity
    level_entities.enabled = True  # Enable the level entities
    if file_slot:
        print(f"Starting game with File {file_slot}")
    player.position = (0, 1, 0)  # Reset player position above the floor

def show_file_select():
    main_menu.enabled = False
    file_select_menu.enabled = True

def show_main_menu():
    main_menu.enabled = True
    file_select_menu.enabled = False

# Create Main Menu UI
title = Text(text="Beta Mario Demo", parent=main_menu, y=0.4, origin=(0, 0), scale=2)
start_btn = Button(
    text='Start',
    parent=main_menu,
    y=0.1,
    scale=(0.2, 0.05),
    on_click=show_file_select
)
quit_btn = Button(
    text='Quit',
    parent=main_menu,
    y=-0.1,
    scale=(0.2, 0.05),
    on_click=application.quit  # Correct way to quit the application
)

# File Select UI
for i in range(1, 5):  # Create buttons for File 1 to File 4
    btn = Button(
        text=f'File {i}',
        parent=file_select_menu,
        y=0.2 - 0.1 * i,
        scale=(0.2, 0.05),
        on_click=Func(start_game, i)
    )
back_btn = Button(
    text='Back',
    parent=file_select_menu,
    y=-0.3,
    scale=(0.2, 0.05),
    color=color.azure,
    on_click=show_main_menu
)

# Example game entities (disabled until start_game is called)
player = Entity(model='sphere', color=color.red, enabled=False)  # Placeholder player
level_entities = Entity(enabled=False)  # Container for level objects
floor = Entity(
    parent=level_entities,
    model='plane',
    scale=10,
    texture='white_cube',
    color=color.gray
)

if __name__ == '__main__':
    app.run()
