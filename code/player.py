import pygame
from game_data import tile_size, controller_map


class Player(pygame.sprite.Sprite):
    def __init__(self, pos, surface, controllers):
        super().__init__()
        self.surface = surface
        self.controllers = controllers

        # -- player setup --
        self.image = pygame.Surface((tile_size, tile_size * 1.5))
        self.image.fill((255, 88, 98))
        self.rect = self.image.get_rect(topleft=(pos[0], pos[1]))  # used for movement and keeping track of image
        self.hitbox = self.image.get_rect(topleft=(pos[0], pos[1]))  # used for collisions

        # -- player movement --
        self.direction = pygame.math.Vector2(0, 0)  # allows cleaner movement by storing both x and y direction
        # collisions -- provides a buffer allowing late collision (must be higher than max velocity to prevent phasing)
        self.collision_tolerance = 20
        self.on_wall = False

        # - walk -
        self.speed_x = 2.5
        self.facing_right = 1

        # - dash -
        self.dashing = False  # NOT REDUNDANT. IS NECCESSARY. Allows resetting timer while dashing. Also more readable code
        self.dash_speed = 4
        self.dash_pressed = False  # if the dash key is being pressed
        self.dash_timer = 0
        self.dash_max = 12  # max time of dash in frames
        self.dash_dir_right = True  # stores the dir for a dash. Prevents changing dir during dash. Only dash cancels
        # - buffer dash -
        self.buffer_dash = False  # is a buffer dash cued up
        self.dashbuff_max = 5  # max time a buffered dash can be cued before it is removed (in frames)
        self.dashbuff_timer = self.dashbuff_max  # times a buffered dash (starts on max to prevent jump being cued on start)

        # -- gravity and falling --
        self.on_ground = False
        self.fall_timer = 0  # timer for how long the player has had a positive y vel and not on ground
        # - terminal vel -
        self.norm_terminal_vel = 10  # normal terminal vel
        self.terminal_vel = self.norm_terminal_vel  # maximum fall speed. if higher than self.collision_tolerance, will allow phasing :(
        # - gravity -
        self.gravity = 0.4
        self.fall_gravity = 1

        # -- Jump --
        # HEIGHT OF JUMP THEN MINIMUM JUMP
        self.jumping = False  # indicates want to jump. Stays true until hits ground after jump or button up
        self.jump_speed = 5  # controls intial jump hop and height of hold jump
        self.jump_pressed = False  # if any jump key is pressed (if player is still trying to jump as well)
        self.held_jump_timer = 0  # used to time the duration of a held jump MUST BE SEPARATE FROM JUMP TIMER
        # jump timer: times from input and is never reset unless input is detected
        # held jump timer: is reset every time grounded and is maxed when held jump has expired
        self.jump_max = 12  # max time a jump can be held

        # - coyote time -
        self.coyote_timer = 0  # times the frames since left the floor
        self.coyote_max = 5  # maximum time for a coyote jump to occur
        # - buffer jump -
        self.buffer_jump = False  # is a buffer jump cued up
        self.jumpbuff_max = 15  # max time a buffered jump can be cued before it is removed (in frames)

        self.jump_timer = self.jumpbuff_max  # Used to time jumps (including buffered jumps and wall jumps) from input
        # if jump timer == 0, means button has just been pressed. Used to ensure button isnt being held
        # (starts on max to prevent buffer jump being cued on start)

        # -- Wall slide/jump --
        self.wall_jump_speed = 7  # wall jump upwards speed
        self.wall_kick_speed = 15  # horizontal velocity gained away from wall when wall jumping
        self.wall_term_vel = 2  # maxiumum fall (slide) speed when on a wall

        # -- Glide --
        self.gliding = False
        self.glide_pressed = False  # required for resetting glide and preventing holding button
        self.glide_terminal_vel = 2  # terminal vel for gliding. Can't be gravity cause gravity can still accumulate to high terminal vel
        self.glide_timer = 0
        self.glide_max = 120  # max time a glide can be held

    def get_input(self):
        self.direction.x = 0
        keys = pygame.key.get_pressed()

        # self.controller.get_hat(0) returns tuple (x, y) for d-pad where 0, 0 is centered, -1 = left or down, 1 = right or up
        # the 0 refers to the dpad on the controller

        #### horizontal movement ####
        # -- walk --
        if keys[pygame.K_d]:
            self.direction.x = self.speed_x
            self.facing_right = 1
        if keys[pygame.K_a]:
            self.direction.x = -self.speed_x
            self.facing_right = -1

        # -- dash --
        # if wanting to dash and not holding the button
        if keys[pygame.K_PERIOD] and not self.dash_pressed:
            # if only just started dashing, dashing is true and dash direction is set. Prevents changing dash dir during dash
            if not self.dashing:
                self.dashing = True
                self.dash_dir_right = self.facing_right
            self.dashbuff_timer = 0  # set to 0 ready for next buffdash
            self.dash_pressed = True
        elif not keys[pygame.K_PERIOD]:
            self.dash_pressed = False

        self.dash()

        '''elif self.dash_timer > self.dash_max:
            self.dash_timer = 0
            self.dashing = False
        if not keys[pygame.K_PERIOD]:
            self.dash_pressed = False
            self.dash_timer = 0
            self.dashing = False'''

        #### vertical movement ####
        # -- jump --
        # input
        if keys[pygame.K_w] or keys[pygame.K_SPACE]:
            # if jump wasnt previously pressed, allow jump (also dependent on other variable in function)
            # set jump_pressed to true
            # prevents continuous held jumps
            if not self.jump_pressed:
                self.jumping = True
                self.jump_timer = 0  # set to 0 ready for next buffjump, used to prove not holding button
            self.jump_pressed = True

        # Checks jump key up
        elif not keys[pygame.K_w] and not keys[pygame.K_SPACE]:
            # if jump previously pressed, kill jump (doesnt matter if jumping or not
            if self.jump_pressed:
                self.held_jump_timer = self.jump_max  # prevents upkey then downkey, re-allowing held jump
                self.jumping = False
            self.jump_pressed = False

        self.jump()

        # -- glide/crouch --
        # if button pressed and last frame not pressed, allow glide (prevents holding glide through jumps) can hold
        # through buffer jumps for speedrunning
        if keys[pygame.K_s]:
            if not self.glide_pressed:
                self.gliding = True
            self.glide_pressed = True
            # TODO crouch here

        # ends glide if button up
        elif not keys[pygame.K_s]:
            # if glide was pressed and now unpressed and was gliding but now is not, max out glide until glide is reset,
            # prevents multiple not-max glides in one air time but allows holding, letting go and re-pressing in air.
            if self.glide_pressed and self.gliding:
                self.glide_timer = self.glide_max
            # ends/prevents glide when key up.
            self.gliding = False
            self.glide_pressed = False
            self.terminal_vel = self.norm_terminal_vel

        self.glide()

    def collision_x(self, tiles):
        self.on_wall = False
        #self.terminal_vel = self.norm_terminal_vel  # TODO currently breaks glide, may not be neccessary, how is term vel reset?

        for tile in tiles:
            if tile.hitbox.colliderect(self.hitbox):
                # abs ensures only the desired side registers collision
                # not having collisions dependant on status allows hitboxes to change size
                if abs(tile.hitbox.right - self.hitbox.left) < self.collision_tolerance: #and 'left' in self.status_facing:
                    self.hitbox.left = tile.hitbox.right
                elif abs(tile.hitbox.left - self.hitbox.right) < self.collision_tolerance: #and 'right' in self.status_facing:
                    self.hitbox.right = tile.hitbox.left

                # - wall cling -
                self.on_wall = True
                self.terminal_vel = self.wall_term_vel
                break

        # resyncs up rect to the hitbox
        self.rect.midtop = self.hitbox.midtop

    def collision_y(self, tiles):
        self.on_ground = False

        for tile in tiles:
            #print(f'{self.hitbox.bottom}, {tile.hitbox.top}')
            if tile.hitbox.colliderect(self.hitbox):
                # abs ensures only the desired side registers collision
                if abs(tile.hitbox.top - self.hitbox.bottom) < self.collision_tolerance:
                    self.on_ground = True
                    self.hitbox.bottom = tile.hitbox.top
                    break
                elif abs(tile.hitbox.bottom - self.hitbox.top) < self.collision_tolerance:
                    self.hitbox.top = tile.hitbox.bottom
                    # if collide with bottom of tile, fall immediately
                    self.direction.y = 0
                break

        # resyncs up rect to the hitbox
        self.rect.midtop = self.hitbox.midtop

    # contains gravity + it's exceptions(gravity code from clearcode platformer tut), terminal velocity, fall timer
    # and application of y direction
    def apply_y_direction(self):
        # -- gravity --
        # if dashing, set direction.y to 0 to allow float
        if self.dashing: #TODO and not self.on_ground:
            self.direction.y = 0
        # when on the ground set direction.y to 1. Prevents gravity accumulation. Allows accurate on_ground detection
        # must be greater than 1 so player falls into below tile's hitbox every frame and is brought back up
        elif self.on_ground:
            self.direction.y = 1
        # if not dashing or on the ground apply gravity normally
        else:
            # if falling, apply more gravity than if moving up
            if self.direction.y > 0:
                self.direction.y += self.fall_gravity
            else:
                self.direction.y += self.gravity

        # -- terminal velocity --
        if self.direction.y > self.terminal_vel:
            self.direction.y = self.terminal_vel

        # -- fall timer --
        # if falling in the air, increment timer else its 0
        if self.direction.y > 0 and not self.on_ground:
            self.fall_timer += 1
        else:
            self.fall_timer = 0

        # -- apply y direction and sync --
        self.rect.y += int(self.direction.y)
        self.sync_hitbox()

    def dash(self):
        # - reset -
        # reset dash, on ground OR if on the wall and dash completed (not dashing) - allows dash to finish before clinging
        # reset despite button pressed or not (not dependant on button, can only dash with button not pressed)
        if self.on_ground or (self.on_wall and not self.dashing):
            self.dash_timer = 0
        # - setup buffer dash -
        # self.dashing is set to false when buffdash is cued. Sets to true on ground so that it can start a normal dash,
        # which resets buffer dashing variables ready for next one
        if self.on_ground and self.dashbuff_timer < self.dashbuff_max:
            self.dashing = True
        # - start normal dash or continue dash -
        # if dashing and dash duration not exceeded OR buffered dash, allow dash
        if self.dashing and self.dash_timer < self.dash_max:
            # - norm dash -
            # add velocity based on facing direction determined at start of dash
            # self.dash_dir_right multiplies by 1 or -1 to change direction of dash speed distance
            self.direction.x += self.dash_speed * self.dash_dir_right
            # dash timer increment
            self.dash_timer += 1

            # - buffer -
            # reset buffer jump with no jump cued
            self.buffer_dash = False
            self.dashbuff_timer = self.dashbuff_max
        # - kill -
        # if not dashing or timer exceeded, end dash but don't reset timer (prevents multiple dashes in the air)
        else:
            self.dashing = False

        # -- buffer dash timer --
        # cue up dash if dash button pressed (if dash is already allowed it will be maxed out in the dash code)
        # OR having already cued, continue timing
        if (self.dashbuff_timer == 0) or self.buffer_dash:
            self.dashbuff_timer += 1
            self.buffer_dash = True

    # physics maths from clearcode platformer tut
    def jump(self):
        # -- coyote time --
        if self.on_ground:
            self.coyote_timer = 0  # resets timer on the ground
        else:
            self.coyote_timer += 1  # increments when not on the ground

        # -- normal jump --
        # - reset jump -
        # reset jump if on ground and has jumped (jump_timer NOT jumping, jumping prevents any jumps cause still on ground when checked)
        # (BAD) Also prevents resetting jump after hitting the jump button casue still on ground, effectively preventing any jumps
        if self.on_ground and self.held_jump_timer > 0:
            self.held_jump_timer = 0
            # if a buffer jump is cued. self.jumping should still be true in case buffjump passes
            if not self.buffer_jump:
                self.jumping = False
        # - execute initial hop (norm, buffer and coyote) -
        # if on the ground and want to jump (not because of a buffer cued)
        # OR on the ground buffer jump hasnt expired),
        # OR coyote time hasnt expired and want to jump
        # ,allow jump
        elif (self.on_ground and self.jumping and not self.buffer_jump) or \
                (self.on_ground and self.jump_timer < self.jumpbuff_max) or \
                (self.jumping and self.coyote_timer < self.coyote_max):
            # - norm jump -
            self.on_ground = False  # TODO <-- need to be here?
            self.direction.y = -self.jump_speed

            # - coyote -
            self.coyote_timer = self.coyote_max

            # - buffer jump -
            # maxes out jump if key is up when jump starts, preventing holding the jump
            # for buffer jumps to prevent ability to extend jump in air after key up then down
            if self.jump_pressed:
                self.held_jump_timer += 1
            else:
                self.held_jump_timer = self.jump_max
            # reset buffer jump with no jump cued
            self.buffer_jump = False
            self.jump_timer = self.jumpbuff_max  # prevents repeated unwanted buffer jumps.
        # - wall jump - TODO extension
        elif self.on_wall and self.jumping and self.jump_timer == 0:
            self.direction.y = -self.wall_jump_speed
            self.direction.x += self.wall_kick_speed * -self.facing_right  # sideways kick off thrust opposite of facing dir
        # - extend jump (variable height) -
        # if already jumping and not exceeding max jump, want to jump still
        elif 0 < self.held_jump_timer < self.jump_max and self.jump_pressed:
            self.held_jump_timer += 1
            self.direction.y = -self.jump_speed

        # -- buffer jump timer --
        # not having successfully jumped because not on ground, cue up jump OR having already cued, continue timing
        if (not self.on_ground and self.jump_timer == 0) or self.buffer_jump:
            self.jump_timer += 1
            self.buffer_jump = True

        '''# -- buffer jump --
        # else if in air but not holding button and a buffer jump isnt already cued, buffer jump for landing
        if not self.jump_pressed and not self.buffer_jump:
            self.buffer_jump = True
            self.jump_pressed = True
            
        # if buffered jump lasts too long, remove buffered jump
        elif self.jumpbuff_timer >= self.jumpbuff_max:
            self.jumpbuff_timer = 0
            self.buffer_jump = False'''

    def glide(self):
        # resets glide if grounded. Prevents multiple full length glides in one flight
        # Can reset even if button is held.
        if self.on_ground:
            self.glide_timer = 0
            self.gliding = False
        # if glide hasn't exceeded max time and falling and allowed to glide (also not on ground from if statement),
        # continue to glide
        elif self.glide_timer < self.glide_max and self.direction.y > 0 and self.gliding:
            self.glide_timer += 1
            self.terminal_vel = self.glide_terminal_vel
        # ends self.gliding if glide has ended (terminal vel auto reset in update)
        elif self.glide_timer >= self.glide_max or not self.gliding:
            self.gliding = False

    # syncs the player hitbox with the player rect for proper collisions. For use after movement of player rect.
    def sync_hitbox(self):
        self.hitbox.midtop = self.rect.midtop

    def apply_scroll(self, scroll_value):
        self.rect.x -= int(scroll_value[1])
        self.rect.y -= int(scroll_value[0])
        self.sync_hitbox()

    def update(self, tiles, scroll_value):
        self.terminal_vel = self.norm_terminal_vel  # resets terminal vel for next frame. Allows wall cling and glide to
        # reset without interfering with each other.

        # -- input --
        self.get_input()

        # -- collision and movement --
        # applies direction to player then resyncs hitbox (included in most movement/collision functions)
        # HITBOX MUST BE SYNCED AFTER EVERY MOVE OF PLAYER RECT
        # x and y collisions are separated to make diagonal collisions easier and simpler to handle
        # - x -
        self.rect.x += int(self.direction.x)
        self.sync_hitbox()
        self.collision_x(tiles)

        # - y -
        # applies direction to player then resyncs hitbox
        self.apply_y_direction()  # gravity
        self.collision_y(tiles)

        # scroll shouldn't have collision applied, it is separate movement
        self.apply_scroll(scroll_value)

    def draw(self):
        self.surface.blit(self.image, self.rect)

