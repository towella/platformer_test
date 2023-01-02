# pyinstaller code/main.py code/camera.py code/game_data.py code/player.py code/room.py code/spawn.py code/support.py code/tiles.py code/trigger.py --onefile --noconsole


# screen resizing tut, dafluffypotato: https://www.youtube.com/watch?v=edJZOQwrMKw

import pygame, sys, time
from room import Room
from text import Font
from game_data import *
from support import resource_path

# General setup
pygame.mixer.pre_init(44100, 16, 2, 4096)
pygame.init()
# tells pygame what events to check for
#setallowed
pygame.font.init()
clock = pygame.time.Clock()
game_speed = 60

# window and screen Setup ----- The window is the real pygame window. The screen is the surface that everything is
# placed on and then resized to blit on the window. Allowing larger pixels (art pixel = game pixel)
# https://stackoverflow.com/questions/54040397/pygame-rescale-pixel-size

scaling_factor = 3.4  # how much the screen is scaled up before bliting on display

# https://www.pygame.org/docs/ref/display.html#pygame.display.set_mode
# https://www.reddit.com/r/pygame/comments/r943bn/game_stuttering/
# vsync only works with scaled flag. Scaled flag will only work in combination with certain other flags.
# although resizeable flag is present, window can not be resized, only fullscreened with vsync still on
# vsync prevents screen tearing (multiple frames displayed at the same time creating a shuddering wave)
# screen dimensions are cast to int to prevent float values being passed (-1 is specific to this game getting screen multiple of 16)
window = pygame.display.set_mode((int(screen_width * scaling_factor) - 1, int(screen_height * scaling_factor)), pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.SCALED, vsync=True)

# all pixel values in game logic should be based on the screen!!!! NO .display FUNCTIONS!!!!!
screen = pygame.Surface((screen_width, screen_height))  # the display surface, re-scaled and blit to the window
screen_rect = screen.get_rect()  # used for camera scroll boundaries

# caption and icon
pygame.display.set_caption('Platformer')
pygame.display.set_icon(pygame.image.load(resource_path('../assets/icon/app_icon.png')))

# controller
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
print(f"joy {len(joysticks)}")
for joystick in joysticks:
    joystick.init()

# font
font = Font(fonts['small_font'], 'white')


# creates path to new room based on root room path and desired room
def get_relative_room_path(room):
    return room_path + room + '.tmx'


def main_menu():
    game()


def game():
    click = False

    # dt
    dt = 1  # first frame so no dt yet. Assume running at desired frame rate with dt of 1
    previous_time = time.time()
    fps = clock.get_fps()

    previous_room = 'room_0'
    room = Room(dt, fps, get_relative_room_path(previous_room), screen, screen_rect, joysticks, previous_room)

    running = True
    while running:
        # delta time  https://www.youtube.com/watch?v=OmkAUzvwsDk
        dt = (time.time() - previous_time) * 60  # 60 keeps units such that movement += 1 * dt means add 1px if at 60fps
        previous_time = time.time()
        fps = clock.get_fps()

        # x and y mouse pos
        mx, my = pygame.mouse.get_pos()

        # Event Checks -- Input --
        click = False
        # TODO finalise standard controls for both keyboard and controller
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                # debug keys
                if event.key == pygame.K_SLASH:
                    pass
                elif event.key == pygame.K_PERIOD:
                    pass
                elif event.key == pygame.K_COMMA:
                    running = False
                    pygame.quit()
                    sys.exit()
                # TODO Test only, remove
                elif event.key == pygame.K_x:
                    global game_speed
                    if game_speed == 60:
                        game_speed = 20
                    else:
                        game_speed = 60
                # TODO put into room pause
                elif event.key == pygame.K_f:
                    room.pause = True
                    pygame.display.toggle_fullscreen()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == controller_map['left_analog_press']:
                    running = False
                    pygame.quit()
                    sys.exit()

        # -- Checks --

        # -- Update --
        screen.fill((15, 0, 34))
        room.update(dt, fps)  # runs level processes
        # if player has hit a room transition in the room, change the active room
        room_transition = room.room_transitions()
        if room_transition:
            del room  # make sure the level instance is deleted properly, freeing memory
            room = Room(dt, fps, get_relative_room_path(room_transition), screen, screen_rect, joysticks, previous_room)
            previous_room = room_transition  # updates previous room

        font.render(f'FPS: {str(clock.get_fps())}', screen, (0, 0))

        # - zoom -
        # TODO add way to pass point to zoom into
        # increases scale of screen based on room's camera zoom
        zoom, zoom_offset = room.get_camera_zoom()
        zoom_width = int(window.get_width() * zoom)
        zoom_height = int(window.get_height() * zoom)
        scaled_dimensions = (zoom_width, zoom_height)

        # -- Render --
        # blit screen to window after scaling screen to window dimensions * zoom amount from active room's camera
        window.blit(pygame.transform.scale(screen, scaled_dimensions), (0 - zoom_offset[0], 0 - zoom_offset[1]))
        pygame.display.update()
        clock.tick(game_speed)


main_menu()
