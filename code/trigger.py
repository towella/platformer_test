import pygame
from text import Font
from support import resource_path
from game_data import fonts


class Trigger(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name, parallax):
        super().__init__()
        self.original_pos = (x, y)
        self.hitbox = pygame.Rect(x, y, width, height)
        self.name = name
        self.parallax = parallax

    def apply_scroll(self, scroll_value, use_parallax):
        if use_parallax:
            self.hitbox.x -= int(scroll_value[0] * self.parallax[0])
            self.hitbox.y -= int(scroll_value[1] * self.parallax[1])
        else:
            self.hitbox.x -= int(scroll_value[0])
            self.hitbox.y -= int(scroll_value[1])

    def update(self, scroll_value, use_parallax=False):
        self.apply_scroll(scroll_value, use_parallax)


# stores correspoding in-room spawn as property
class SpawnTrigger(Trigger):
    def __init__(self, x, y, width, height, name, parallax, spawn):
        super().__init__(x, y, width, height, name, parallax)
        self.spawn = spawn

    def get_spawn_pos(self):
        return self.spawn.get_pos()

    def apply_scroll(self, scroll_value, use_parallax=False):
        if use_parallax:
            self.hitbox.x -= int(scroll_value[0] * self.parallax[0])
            self.hitbox.y -= int(scroll_value[1] * self.parallax[1])
        else:
            self.hitbox.x -= int(scroll_value[0])
            self.hitbox.y -= int(scroll_value[1])
        self.spawn.update(scroll_value)


class DoorTrigger(SpawnTrigger):
    def __init__(self, x, y, width, height, name, parallax, spawn, text):
        super().__init__(x, y, width, height, name, parallax, spawn)
        self.text = text
        self.font = Font(resource_path(fonts['small']), 'black')
        self.txtwidth = self.font.width(self.text)

    def draw(self, surface):
        pos = (self.hitbox.midtop[0] - self.txtwidth//2, self.hitbox.midtop[1])  # position text using hitbox
        self.font.render(self.text, surface, pos, 'white')
