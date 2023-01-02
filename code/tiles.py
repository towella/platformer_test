import pygame
from support import import_folder, scale_hitbox


# base tile class with block fill image
class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, size):
        super().__init__()
        self.image = pygame.Surface((size, size))  # creates square tile
        self.image.fill('grey')  # makes tile grey
        self.rect = self.image.get_rect(topleft=pos)  # postions the rect and image
        self.screen_width = pygame.display.Info().current_w
        self.screen_height = pygame.display.Info().current_h

    # allows all tiles to scroll at a set speed creating camera illusion
    def apply_scroll(self, scroll_value):
        self.rect.x -= int(scroll_value[1])
        self.rect.y -= int(scroll_value[0])

    # scroll is separate to update, giving control to children of Tile class to override update
    def update(self, scroll_value):
        self.apply_scroll(scroll_value)

    def draw(self, display):
        # if the tile is within the screen with a buffer of 100px every direction, render tile
        #if self.rect.right > 100 and self.rect.left < self.screen_width + 100 and self.rect.top > -100 and self.rect.bottom < self.screen_height + 100:
        display.blit(self.image, self.rect)


# terrain tile type, inherits from main tile and can be assigned an image
class StaticTile(Tile):
    def __init__(self, pos, size, surface):
        super().__init__(pos, size)  # passing in variables to parent class
        self.image = surface  # image is passed tile surface
        self.hitbox = self.image.get_rect()

    # allows all tiles to scroll at a set speed creating camera illusion
    def apply_scroll(self, scroll_value):
        self.rect.x -= int(scroll_value[1])
        self.rect.y -= int(scroll_value[0])
        self.hitbox.midbottom = self.rect.midbottom

# animated tile that can be assigned images from a folder to animate
class AnimatedTile(Tile):
    def __init__(self, pos, size, path):
        super().__init__(pos, size)
        self.frames = import_folder(path, 'list')
        self.frame_index = 0
        self.image = self.frames[self.frame_index]

    def animate(self):
        self.frame_index += 0.15
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def update(self, scroll_value):
        self.animate()
        self.apply_scroll(scroll_value)


'''class NPC(Tile):
    def __init__(self, pos, size, path):
        super().__init__(pos, size)
        self.text_box
'''

'''class Crate(StaticTile):
    def __init__(self, pos, size, surface, all_tiles):
        super().__init__(pos, size, surface)
        # TODO implement crate specific hitbox
        self.all_tiles = all_tiles

    def collide(self, sprite):
        collision_tolerance = 20

        if sprite.hitbox.colliderect(self.hitbox):
            # abs ensures only the desired side registers collision
            # not having collisions dependant on status allows hitboxes to change size
            if abs(sprite.hitbox.right - self.hitbox.left) < collision_tolerance: #and 'left' in self.status_facing:
                self.hitbox.left = sprite.hitbox.right
            elif abs(sprite.hitbox.left - self.hitbox.right) < collision_tolerance: #and 'right' in self.status_facing:
                self.hitbox.right = sprite.hitbox.left
        # resyncs up rect to the hitbox
        self.rect.midtop = self.hitbox.midtop'''