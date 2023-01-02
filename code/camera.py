import pygame

class Camera():
    def __init__(self, surface, player):
        self.player = player  # the target of the camera
        self.target = [self.player.rect.centerx, self.player.rect.centery]  # target position
        self.scroll_value = [0, 0]  # the scroll, shifts the world to create camera effect

        # lerp = linear interpolation. Speed the camera takes to center on the player as it moves, (camera smoothing)
        # -- normal lerp --
        self.norm_lerp = 15  # (20) normal camera interpolation speed
        # -- fall --
        self.fall_lerp_max = 8  # (8) maximum sensitivity the camera can track the player w/ while falling
        self.fall_lerp_increment = 0.5  # used to increment the falling lerp gradually to it's max for smoothness
        self.fall_min_time = 60  # number of frames w/ y vel > 0 before falling logic is applied
        # -- lerp active values --
        self.lerp_x = self.norm_lerp  # controls scroll interpolation amount x (sensitivity of camera to movement of target)
        self.lerp_y = self.norm_lerp  # controls scroll interpolation amount y (sensitivity of camera to movement of target)

        # -- offsets --
        self.facing_offset = 25  # offset from the player on the horizontal when not falling and change facing dir (40)
        self.walking_offset = 35  # offset from the player on the horizontal when walking (not falling and move hori)

        self.fall_offset = 0  # added to when falling, allows gradual movement of target
        self.fall_offset_max = 100  # max offset from player on vertical when falling
        self.fall_offset_increment = 6  # increment target is moved by

        self.look_up_down = 100

        # -- screen dimensions --
        self.screen_width = surface.get_width()
        self.screen_height = surface.get_height()
        self.screen_center_x = surface.get_width() // 2
        self.screen_center_y = surface.get_height() // 2

        # -- boundary collision --
        self.collision_tolerance = 60  # tolerance for camera boundaries  (60)

    def get_input(self):
        keys = pygame.key.get_pressed()

        # -- camera look up and down--
        if self.player.on_ground:
            if keys[pygame.K_DOWN]:
                self.target[1] += self.look_up_down
            elif keys[pygame.K_UP]:
                self.target[1] -= self.look_up_down

# -- camera --

    def update_target(self):
        # target[0] = x, target[1] = y
        self.target = [self.player.rect.centerx, self.player.rect.centery]  # sets target to player pos for modification

        self.get_input()

        # -- player horizontal directional offset --
        '''# walking
        if self.player.direction.x != 0:
            # right
            if self.player.direction.x > 0:
                self.target[0] += self.walking_offset
            # left
            else:
                self.target[0] -= self.walking_offset'''

        # facing (multiply distance by direction)
        self.target[0] += self.facing_offset * self.player.facing_right

        # -- falling vertical offset --
        # if player IS falling have vertical offset and no horizontal offset
        if self.player.fall_timer > self.fall_min_time:
            # TODO super bodgy code
            self.fall_offset += self.fall_offset_increment
            # caps the fall_offset at the max
            if self.fall_offset > self.fall_offset_max:
                self.fall_offset = self.fall_offset_max
            # applies fall_offset
            self.target[1] += self.fall_offset
        else:
            self.fall_offset = 0

    # scrolls the world when the player hits certain points on the screen
    # dynamic camera tut, dafluffypotato:  https://www.youtube.com/watch?v=5q7tmIlXROg
    def return_scroll(self, focus_target=False):
        self.update_target()

        # if camera is to follow normally, do normal stuff, otherwise, focus camera directly on target
        if not focus_target:
            # -- decreases LERP_y gradually when falling and resets when hit ground --
            if self.player.direction.y > 0 and not self.player.on_ground:
                self.lerp_y -= self.fall_lerp_increment
                if self.lerp_y < self.fall_lerp_max:
                    self.lerp_y = self.fall_lerp_max
            else:
                self.lerp_y = self.norm_lerp
            #print('lerp_x', self.lerp_x)
            #print('lerp_y', self.lerp_y)

            # scroll_value[0] = y, scroll_value[1] = x

            # scroll value cancels player movement with scrolling everything, including player (centerx - scroll_value)
            # subtracts screen width//2 to place player in the center of the screen rather than left edge

            # the division adds a fraction of the difference between the camera (scroll) and the player to the scroll,
            # making the camera follow with lag and also settle gently as the  fraction gets smaller the closer the camera
            # is to the player

            # self.scroll_value[1] += (player.rect.centerx - self.scroll_value[1] - screen_width//2)/20   for platformer
            # += was an issue causing odd motion (use for screen shake??)
            # TODO smoother approach and settle when player is stopped?? Closer to target??
            self.scroll_value[0] = (self.target[1] - self.scroll_value[0] - self.screen_center_y) / self.lerp_y
            self.scroll_value[1] = (self.target[0] - self.scroll_value[1] - self.screen_center_x) / self.lerp_x
        else:
            # focus camera on target.
            self.scroll_value = [-(self.screen_center_y - self.player.rect.centery),
                                 -(self.screen_center_x - self.player.rect.centerx)]

        return self.scroll_value

        # enables scroll camera boundaries
        '''screen_right = self.screen_rect.right
        screen_left = 0
        screen_top = 0
        screen_bottom = self.screen_rect.bottom  # may not appear to work as a result of the screen rect being set to fullscreen making screen bigger
        for tile in self.camera_boundaries_x:
            # neccessary to use a variable to be able to manipulate value
            tile_right = tile.rect.right
            tile_left = tile.rect.left
            # if the tile's right is on the right side within a certain area of the screen and we're scrolling left
            # (chained expression for efficiency)
            if collision_tolerance > tile.rect.right >= screen_left and self.scroll_value[1] < 0:
                # stop scroll
                self.scroll_value[1] = 0
                # while the tile's right is on screen
                while tile_right > screen_left:
                    # moving the camera to snap to tile grid by rounding the scroll value to a multiple of a tile
                    # (moving the camera until the tile is offscreen by exactly one pixel)
                    self.scroll_value[1] += 1
                    tile_right -= 1  # (positive scroll moves everything negatively) simulates the tile moving away
                    # without actually updating the tile pos, enables checking if the scroll is enough
                # after moving the camera we dont need to cycle through the rest of the tiles
                break
            elif (screen_right - collision_tolerance) < tile.rect.left <= screen_right and self.scroll_value[1] > 0:
                self.scroll_value[1] = 0
                while tile_left < screen_right:
                    self.scroll_value[1] -= 1
                    tile_left += 1
                break

        for tile in self.camera_boundaries_y:
            tile_bottom = tile.rect.bottom
            tile_top = tile.rect.top
            if collision_tolerance > tile.rect.bottom >= screen_top and self.scroll_value[0] < 0:
                self.scroll_value[0] = 0
                while tile_bottom > screen_top:
                    self.scroll_value[0] += 1
                    tile_bottom -= 1
                break
            elif (screen_bottom - collision_tolerance) < tile.rect.top <= screen_bottom and self.scroll_value[0] > 0:
                self.scroll_value[0] = 0
                while tile_top < screen_bottom:
                    self.scroll_value[0] -= 1
                    tile_top += 1
                break'''

# -- HUD --

    def hud_handler(self):
        pass