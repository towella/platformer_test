import pygame


# in-room spawns are stored as property of SpawnTrigger class for simplicity of access
class Spawn(pygame.sprite.Sprite):
    def __init__(self, x, y, name, player_facing):
        super().__init__()
        self.x = x
        self.y = y
        self.name = name
        self.player_facing = player_facing

    def apply_scroll(self, scroll_value):
        self.x -= int(scroll_value[0])
        self.y -= int(scroll_value[1])

    def update(self, scroll_value):
        self.apply_scroll(scroll_value)