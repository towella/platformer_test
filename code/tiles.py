import pygame
from support import import_folder


# base tile class with block fill image and normal surface support (also used for images, i.e, one big tile)
class StaticTile(pygame.sprite.Sprite):
    def __init__(self, pos, size, parallax, surface=None):
        super().__init__()
        self.original_pos = pos
        if surface:
            self.image = surface
        else:
            self.image = pygame.Surface((size[0], size[1]))  # creates tile
            self.image.fill('grey')  # makes tile grey
        self.rect = self.image.get_rect(topleft=pos)  # postions the rect and image and used to check on screen
        self.parallax = parallax  # set to 1 if no parallax required
        self.screen_width = pygame.display.Info().current_w
        self.screen_height = pygame.display.Info().current_h

    # allows all tiles to scroll at a set speed creating camera illusion
    def apply_scroll(self, scroll_value):
        self.rect.x -= int(scroll_value[0] * self.parallax[0])
        self.rect.y -= int(scroll_value[1] * self.parallax[1])

    # scroll is separate to update, giving control to children of Tile class to override update
    def update(self, scroll_value):
        self.apply_scroll(scroll_value)

    def draw(self, screen, screen_rect):
        # if the tile is within the screen, render tile
        if self.rect.colliderect(screen_rect):
            screen.blit(self.image, self.rect)


# terrain tile type, inherits from main tile and can be assigned an image
class CollideableTile(StaticTile):
    def __init__(self, pos, size, parallax, surface):
        super().__init__(pos, size, parallax)  # passing in variables to parent class
        self.image = surface  # image is passed tile surface
        self.hitbox = self.image.get_rect()
        self.hitbox_offset = (0, 0)
        self.pos = [pos[0], pos[1]]  # allows for float coordinates for parallax moving

    # allows all tiles to scroll at a set speed creating camera illusion
    def apply_scroll(self, scroll_value):
        # apply scroll to position
        self.pos[0] -= scroll_value[0] * self.parallax[0]
        self.pos[1] -= scroll_value[1] * self.parallax[1]
        # sync rect with pos
        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]
        # move hitbox, accounting for custom hitbox position
        self.hitbox.x = self.pos[0] + self.hitbox_offset[0]
        self.hitbox.y = self.pos[1] + self.hitbox_offset[1]


class HazardTile(CollideableTile):
    def __init__(self, pos, size, parallax, surface, player, properties=None):
        super().__init__(pos, size, parallax, surface)
        self.player = player
        if properties:
            colliders = properties['colliders']
            for obj in colliders:
                self.hitbox = pygame.Rect(0, 0, obj.width, obj.height)  # custom hitbox from tiled
                self.hitbox_offset = (obj.x, obj.y)  # custom hitbox position

    def update(self, scroll_value):
        if self.hitbox.colliderect(self.player.hitbox):
            self.player.invoke_respawn()
        self.apply_scroll(scroll_value)


# animated tile that can be assigned images from a folder to animate
class AnimatedTile(StaticTile):
    def __init__(self, pos, size, parallax, path):
        super().__init__(pos, size, parallax)
        self.frames = import_folder(path, 'list')
        self.frame_index = 0
        self.image = self.frames[self.frame_index]

    def animate(self):
        self.frame_index += 0.15
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
        self.image = self.frames[int(self.frame_index)]

    def update(self, scroll_value, use_parallax=False):
        self.animate()
        self.apply_scroll(scroll_value, use_parallax)


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