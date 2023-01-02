# pyinstaller code/main.py code/camera.py code/game_data.py code/player.py code/room.py code/spawn.py code/support.py code/tiles.py code/trigger.py --onefile --noconsole


# screen resizing tut, dafluffypotato: https://www.youtube.com/watch?v=edJZOQwrMKw

import pygame, sys, time
from room import Room
from text import Font
from game_data import *

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

pygame.display.set_caption('Platformer')

# controller
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
print(f"joy {len(joysticks)}")
for joystick in joysticks:
    joystick.init()

# font
font = Font(fonts['small_font'], 'white')


def main_menu():
    game()


def game():
    click = False
    previous_time = time.time()
    previous_room = 'room_0'
    room = Room(rooms[previous_room], screen, screen_rect, joysticks, previous_room)

    running = True
    while running:
        # delta time
        dt = time.time() - previous_time
        previous_time = time.time()
        print(dt)

        # x and y mouse pos
        mx, my = pygame.mouse.get_pos()

        # Event Checks -- Input --
        click = False
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
                elif event.key == pygame.K_COMMA or event.key == pygame.K_ESCAPE:
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

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == controller_map['left_analog_press']:
                    running = False
                    pygame.quit()
                    sys.exit()

        # -- Update --
        screen.fill((15, 0, 34))
        room.update(dt)  # runs level processes
        # if player has hit a room transition in the room, change the active room
        room_transition = room.room_transitions()
        if room_transition:
            room = Room(rooms[room_transition], screen, screen_rect, joysticks, previous_room)
            previous_room = room_transition  # updates previous room

        font.render(f'FPS: {str(clock.get_fps())}', screen, (0, 0))

        window.blit(pygame.transform.scale(screen, window.get_rect().size), (0, 0))  # scale screen to window

        # -- Render --
        pygame.display.update()
        clock.tick(game_speed)


main_menu()
