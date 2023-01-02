import pygame


class Trigger(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name):
        super().__init__()
        self.hitbox = pygame.Rect(x, y, width, height)
        self.name = name

    def apply_scroll(self, scroll_value):
        self.hitbox.x -= int(scroll_value[0])
        self.hitbox.y -= int(scroll_value[1])

    def update(self, scroll_value):
        self.apply_scroll(scroll_value)


# stores correspoding in-room spawn as property
class SpawnTrigger(Trigger):
    def __init__(self, x, y, width, height, name, trigger_spawn):
        super().__init__(x, y, width, height, name)
        self.trigger_spawn = trigger_spawn

    def apply_scroll(self, scroll_value):
        self.hitbox.x -= int(scroll_value[0])
        self.hitbox.y -= int(scroll_value[1])
        self.trigger_spawn.update(scroll_value)
