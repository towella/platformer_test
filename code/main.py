# screen resizing tut, dafluffypotato: https://www.youtube.com/watch?v=edJZOQwrMKw

import pygame, sys
from level import Level
from game_data import level_0, controller_map, screen_width, screen_height

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

scaling_factor = 2.7  # how much the screen is scaled up before bliting on display (2.7 good)

# https://www.pygame.org/docs/ref/display.html#pygame.display.set_mode
# https://www.reddit.com/r/pygame/comments/r943bn/game_stuttering/
# vsync only works with scaled flag. Scaled flag will only work in combination with certain other flags.
# although resizeable flag is present, window can not be resized, only fullscreened with vsync still on
# vsync prevents screen tearing (multiple frames displayed at the same time creating a shuddering wave)
window = pygame.display.set_mode((int(screen_width * scaling_factor), int(screen_height * scaling_factor)), pygame.RESIZABLE | pygame.DOUBLEBUF | pygame.SCALED, vsync=True)

# all pixel values in game logic should be based on the screen!!!! NO .display FUNCTIONS!!!!!
screen = pygame.Surface((screen_width, screen_height))  # the display surface, re-scaled and blit to the window
screen_rect = screen.get_rect()  # used for camera scroll boundaries

pygame.display.set_caption('Platformer')

# controller
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
print(len(joysticks))
for joystick in joysticks:
    joystick.init()


def main_menu():
    game()


def game():
    click = False
    pause = False
    level = Level(level_0, screen, screen_rect, joysticks)

    running = True
    while running:

        # x and y mouse pos
        mx, my = pygame.mouse.get_pos()

        # Event Checks (input)
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
                elif event.key == pygame.K_p:
                    pause = not pause
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
                elif event.button == controller_map['options']:
                    pause = not pause

        # Update
        if not pause:
            screen.fill((69, 105, 144))
            level.run()
        window.blit(pygame.transform.scale(screen, window.get_rect().size), (0, 0))

        # update window
        pygame.display.update()
        clock.tick(game_speed)


main_menu()