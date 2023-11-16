import pygame
from game_data import tile_size, controller_map
from tiles import StaticTile
from lighting import Light
from support import import_folder


class Player(pygame.sprite.Sprite):
    def __init__(self, room, spawn):
        super().__init__()
        self.room = room
        self.surface = room.screen_surface
        self.controllers = room.controllers

        # -- PLAYER SETUP --
        # player is (tile_size, tile_size * 1.5)

        # - animation, hitboxes and assets --
        # declare what keys require corresponding animations (each key is name of folder in assets)
        self.animations = {"idle_right": [], "idle_left": [], "idle_crouch": []}
        self.animations = self.import_character_animations(self.animations)
        self.frame_index = 0
        self.animation_speed = 5  # time in frames that animation frames change

        # - player state on spawn (image, facing dir, respawn=False) -
        # set up starting player facing direction and starting image
        facing = spawn.player_facing.lower()
        if facing == 'right':
            self.facing_right = 1
        else:
            self.facing_right = -1
        self.image = self.animations['idle_' + facing][self.frame_index]
        self.current_anim = 'idle_' + facing
        self.respawn = False

        # - rect and lights -
        self.rect = pygame.Rect(spawn.x, spawn.y, self.image.get_width(), self.image.get_height())
        self.lights = [Light(self.surface, self.rect.center, (15, 15, 15), False, 40, 30, 0.02),
                       Light(self.surface, self.rect.center, (20, 25, 25), False, 25, 20, 0.02)]
        self.light_background_mask = self.get_background_light_mask_tile(room.background_layers)

        # - hitboxes  -
        self.hitboxes = {
            "normal": pygame.Rect(self.rect.midbottom[0], self.rect.midbottom[1], tile_size * 0.8, tile_size * 1.4),
            "crouch": pygame.Rect(self.rect.midbottom[0], self.rect.midbottom[1], tile_size * 0.8, tile_size * 0.8)}
        self.hitbox = self.hitboxes["normal"]  # used for collisions and can be different to rect and image

        self.interact = False
        self.interact_pressed = False

        # -- PLAYER MOVEMENT --
        self.direction = pygame.math.Vector2(0, 0)  # allows cleaner movement by storing both x and y direction
        # collisions -- provides a buffer allowing late collision
        self.collision_tolerance = tile_size
        self.corner_correction = 8  # tolerance for correcting player on edges of tiles (essentially rounded corners)
        self.vertical_corner_correction_boost = 4

        # - walk -
        self.speed_x = 2.5
        self.right_pressed = False
        self.left_pressed = False

        # - dash -
        self.dashing = False  # NOT REDUNDANT. IS NECCESSARY. Allows resetting timer while dashing. More readable code
        self.dash_speed = 4
        self.dash_pressed = False
        self.dash_max = 12  # max time of dash in frames
        self.dash_timer = self.dash_max  # maxed out to prevent being able to dash on start. Only reset on ground
        self.dash_dir_right = True  # stores the dir for a dash. Prevents changing dir during dash. Only dash cancels
        # - buffer dash -
        self.buffer_dash = False  # is a buffer dash cued up
        self.dashbuff_max = 5  # max time a buffered dash can be cued before it is removed (in frames)
        self.dashbuff_timer = self.dashbuff_max  # times buffered dash from input (maxed to prevent jump cued on start)

        # -- gravity and falling --
        self.on_ground = False
        self.fall_timer = 0  # timer for how long the player has had a positive y vel and not on ground
        # - terminal vel -
        self.norm_terminal_vel = 10
        self.terminal_vel = self.norm_terminal_vel  # max fall speed. if higher than collision tolerance, allows phasing :(
        # - gravity -
        self.gravity = 0.4
        self.fall_gravity = 1

        # -- Jump --
        # HEIGHT OF JUMP THEN MINIMUM JUMP
        self.jumping = False  # true when initial hop has been completed, allowing held jump.false if key up or grounded
        # verifies jump is already in progress (jump_timer is reset every time key down)
        self.jump_speed = 5  # controls initial jump hop and height of hold jump
        self.jump_pressed = False  # if any jump key is pressed
        self.jump_max = 12  # max time a jump can be held
        self.jump_hold_timer = self.jump_max  # amount of time jump has been held. Not related to allowing initial jumps

        # - double jump -
        self.can_double_jump = False
        # - coyote time -
        self.coyote_timer = 0  # times the frames since left the floor
        self.coyote_max = 5  # maximum time for a coyote jump to occur

        # - buffer jump -
        self.jumpbuff_max = 10  # max time a buffered jump can be cued before it is removed (in frames)

        self.jump_timer = self.jumpbuff_max  # Time since last jump input if jump not yet executed. (allows initial jump)
        # Used to time jumps (including buffered jumps and wall jumps) from input
        # if jump timer == 0, means button has just been pressed. Used to ensure button isnt being held
        # if jump timer > 0 and not on_ground, means player is jumping or falling after jump
        # if jump timer == 0 in air, buffer jump has been cued up
        # if jump timer < timer_max, provides a window for input to be processed rather than exactly == 0
        # (starts on max to prevent buffer jump being cued on start)

        # -- Wall slide/jump --
        self.on_wall = False  # if player is currently touching wall
        self.can_wall_jump = True  # whether allowed to wall jump or not
        self.wall_jumping = False  # whether player is in wall jump (should have x wall kick vel applied)
        self.wall_jump_max = 5  # timer for duration of wall jump
        self.on_wall_right = -1  # used to multiply wall x offset to change direction
        self.wall_jump_speed = 7  # wall jump upwards speed
        self.wall_kick_speed = 3  # horizontal velocity gained away from wall when wall jumping
        self.wall_term_vel = 2  # maximum fall (slide) speed when on a wall
        self.extended_wall_jumps = False
        # - sticky wall -
        self.sticky_wall_max = 5
        self.sticky_wall_timer = self.sticky_wall_max
        # - buffer wall jump -
        self.wall_jumpbuff_max = 7  # max time a buffered wall jump can be cued before it is removed (in frames)

        # -- Glide --
        self.gliding = False
        self.glide_pressed = False  # required for resetting glide and preventing holding button
        self.glide_terminal_vel = 2  # terminal vel for gliding. Can't be gravity cause gravity can still accumulate to high terminal vel
        self.glide_timer = 0
        self.glide_max = 120  # max time a glide can be held

        # -- Crouch --
        self.crouching = False
        self.crouch_speed = 1  # speed of walk when crouching

# -- imports and setup --

    # imports all character animations from folders into dict
    def import_character_animations(self, animations):
        animations_path = '../assets/player/animations/'
        # dictionary keys are the same name as folder
        
        # ONLY IMAGES IN FOLDERS!!!!

        # retrieve assets
        for animation in animations.keys():
            full_path = animations_path + animation  # extends directory pointer with desired animation folder
            animations[animation] = import_folder(full_path, 'list')
        return animations

    # keep just in case required to make hitboxing easier for large scale dev rather than creating rect hitbox manually
    def import_character_hitboxes(self, hitboxes):
        hitboxes_path = '../assets/player/hitboxes/'
        # dictionary keys are the same name as folder
        
        # ONLY IMAGES IN FOLDERS!!!!

        # retrieve assets
        for hitbox in hitboxes.keys():
            full_path = hitboxes_path + hitbox
            hitboxes[hitbox] = import_folder(full_path, 'surface')
        return hitboxes

    def get_background_light_mask_tile(self, background_layers):
        sprite_group = pygame.sprite.GroupSingle()

        # working surface, ends up with all parallax-1 layers compressed onto it and then masked
        combined_layers = pygame.Surface((background_layers[0].sprite.image.get_width(),
                                          background_layers[0].sprite.image.get_height()))
        combined_layers.set_colorkey((0, 0, 0))

        # get parallax-1 background layer tiles
        for layer_tile in background_layers:
            if layer_tile.sprite.parallax == (1, 1):
                combined_layers.blit(layer_tile.sprite.image, (0, 0))

        # create mask with layer tiles cut out (white = on px, leave off px for cutting out light surfs)
        mask = pygame.mask.from_surface(combined_layers)
        mask = mask.to_surface()
        mask.set_colorkey((255, 255, 255))

        # create tile holding mask so shifts with rest of world
        tile = StaticTile((0, 0), (mask.get_width(), mask.get_height()), (1, 1), mask)
        sprite_group.add(tile)

        return sprite_group

# -- checks --

    def get_input(self, dt, tiles):
        self.direction.x = 0
        keys = pygame.key.get_pressed()

        if keys[pygame.K_e] and not self.interact_pressed:
            self.interact = True
            self.interact_pressed = True
        elif keys[pygame.K_e] and self.interact_pressed:
            self.interact = False
        else:
            self.interact_pressed = False
            self.interact = False

        #### horizontal movement ####
        # -- walk --
        # the not self.'side'_pressed prevents holding a direction and hitting the other at the same time to change direction
        if (keys[pygame.K_d] or self.get_controller_input('right')) and not self.left_pressed and not self.wall_jumping:
            if not self.crouching:
                self.direction.x = self.speed_x
            else:
                self.direction.x = self.crouch_speed
            self.facing_right = 1
            self.right_pressed = True
        else:
            self.right_pressed = False

        if (keys[pygame.K_a] or self.get_controller_input('left')) and not self.right_pressed and not self.wall_jumping:
            if not self.crouching:
                self.direction.x = -self.speed_x
            else:
                self.direction.x = -self.crouch_speed
            self.facing_right = -1
            self.left_pressed = True
        else:
            self.left_pressed = False

        # -- dash --
        # if wanting to dash and not holding the button
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or self.get_controller_input('dash')) and not self.dash_pressed:
            # if only just started dashing, dashing is true and dash direction is set. Prevents changing dash dir during dash
            if not self.dashing:
                self.dashing = True
                # dash direction right is used to multiply dash direction to indicate direction rather than just displacement
                self.dash_dir_right = self.facing_right
                # TODO fix
                # if player is on wall, dash direction is opposite to facing to dash away from wall
                if self.on_wall:
                    self.dash_dir_right = -self.dash_dir_right
            self.dashbuff_timer = 0  # set to 0 ready for next buffdash
            self.dash_pressed = True
        # neccessary to prevent repeated dashes on button hold
        elif not keys[pygame.K_LSHIFT] and not keys[pygame.K_RSHIFT] and not self.get_controller_input('dash'):
            self.dash_pressed = False

        self.dash(dt)

        #### vertical movement ####
        # -- jump --
        # input
        if keys[pygame.K_w] or keys[pygame.K_SPACE] or self.get_controller_input('jump'):
            # if jump wasnt previously pressed, allow jump (also dependent on other variable in function)
            # set jump_pressed to true
            # prevents continuous held jumps
            if not self.jump_pressed:
                self.jump_timer = 0  # set to 0 ready for next buffjump, used to prove not holding button
                self.jump_hold_timer = 0
            self.jump_pressed = True
        # jump keys up
        else:
            self.jumping = False
            self.jump_hold_timer = self.jump_max
            self.jump_pressed = False

        self.jump(dt)

        # -- glide --
        # if button pressed and last frame not pressed, allow glide (prevents holding glide through jumps) can hold
        # through buffer jumps for speedrunning
        if keys[pygame.K_s] or self.get_controller_input('glide') and not self.on_ground:
            if not self.glide_pressed:
                self.gliding = True
            self.glide_pressed = True
        # ends glide/crouch if button is up (crouch exception case is handled in self.crouch())
        else:
            # if glide was pressed and now unpressed and was gliding but now is not, max out glide until glide is reset,
            # prevents multiple not-max glides in one air time but allows holding, letting go and re-pressing in air.
            if self.glide_pressed and self.gliding:
                self.glide_timer = self.glide_max
            # ends/prevents glide when key up.
            self.gliding = False
            self.glide_pressed = False
            # terminal vel auto reset in update

        self.glide(dt)

        # -- crouch --
        # if wanting to crouch AND on the ground (so as to avoid glide)
        if (keys[pygame.K_s] or self.get_controller_input('crouch')) and self.on_ground:
            self.crouching = True
        else:
            self.crouching = False

        self.crouch(tiles)

        # TODO testing, remove #############
        if keys[pygame.K_r] or self.get_controller_input('dev'):
            self.invoke_respawn()

    # checks controller inputs and returns true or false based on passed check
    # pygame controller docs: https://www.pygame.org/docs/ref/joystick.html
    def get_controller_input(self, input_check):
        # self.controller.get_hat(0) returns tuple (x, y) for d-pad where 0, 0 is centered, -1 = left or down, 1 = right or up
        # the 0 refers to the dpad on the controller

        # check if controllers are connected before getting controller input (done every frame preventing error if suddenly disconnected)
        if len(self.controllers) > 0:
            controller = self.controllers[0]
            if input_check == 'jump' and controller.get_button(controller_map['X']):
                return True
            elif input_check == 'right':
                if controller.get_hat(0)[0] == 1 or (0.2 < controller.get_axis(controller_map['left_analog_x']) <= 1):
                    return True
            elif input_check == 'left':
                if controller.get_hat(0)[0] == -1 or (-0.2 > controller.get_axis(controller_map['left_analog_x']) >= -1):
                    return True
                '''elif input_check == 'up':
                    if controller.get_hat(0)[1] == 1 or (-0.2 > controller.get_axis(controller_map['left_analog_y']) >= -1):
                        return True
                elif input_check == 'down':
                    if controller.get_hat(0)[1] == -1 or (0.2 < controller.get_axis(controller_map['left_analog_y']) <= 1):
                        return True'''
            elif input_check == 'dash' and controller.get_button(controller_map['R2']) > 0.8:
                return True
            elif input_check == 'glide' and (controller.get_button(controller_map['L1'])):
                return True
            elif input_check == 'crouch' and (controller.get_hat(0)[1] == -1 or controller.get_button(controller_map['L1'])):  # TODO crouch controls
                return True
                # TODO testing, remove ################
            elif input_check == 'dev' and controller.get_button(controller_map['right_analog_press']):
                return True
        return False

    # - respawn -

    def invoke_respawn(self):
        self.respawn = True

    def get_respawn(self):
        return self.respawn

    def player_respawn(self, spawn):
        self.rect.x, self.rect.y = spawn.x, spawn.y  # set position to respawn point
        self.sync_hitbox()
        if spawn.player_facing == 'right':
            self.facing_right = 1
        else:
            self.facing_right = -1
        self.direction = pygame.math.Vector2(0, 0)  # reset movement
        self.dashing = False  # end any dashes on respawn
        self.dash_timer = self.dash_max  # prevent dash immediately on reset
        self.gliding = False  # end any gliding on respawn
        self.crouching = False  # end any crouching on respawn
        self.jumping = False  # end any jumps on respawn
        self.respawn = False

# -- movement methods --

    def dash(self, dt):
        # - reset -
        # reset dash, on ground OR if on the wall and dash completed (not dashing) - allows dash to finish before clinging
        # reset despite button pressed or not (not dependant on button, can only dash with button not pressed)
        if self.on_ground or (self.on_wall and not self.dashing):
            self.dash_timer = 0
        # - setup buffer dash - (only when not crouching)
        # self.dashing is set to false when buffdash is cued. Sets to true on ground so that it can start a normal dash,
        # which resets buffer dashing variables ready for next one
        if self.on_ground and self.dashbuff_timer < self.dashbuff_max and not self.crouching:
            self.dashing = True
        # - start normal dash or continue dash - (only when not crouching)
        # (if dashing and dash duration not exceeded OR buffered dash) AND not crouching AND not on wall, allow dash
        if self.dashing and self.dash_timer < self.dash_max and not self.crouching:
            # - norm dash -
            # add velocity based on facing direction determined at start of dash
            # self.dash_dir_right multiplies by 1 or -1 to change direction of dash speed distance
            self.direction.x += self.dash_speed * self.dash_dir_right
            # dash timer increment
            self.dash_timer += round(1 * dt)

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
            self.dashbuff_timer += round(1 * dt)
            self.buffer_dash = True

    # physics maths from clearcode platformer tut (partly)
    def jump(self, dt):
        # -- coyote time --
        if self.on_ground:
            self.coyote_timer = 0  # resets timer on the ground
        else:
            self.coyote_timer += round(1 * dt)  # increments when not on the ground

        # -- sticky wall time --
        if self.on_wall:
            self.sticky_wall_timer = 0  # reset on wall
        else:
            self.sticky_wall_timer += round(1 * dt)  # increments when not on wall

        # - reset -
        if self.on_ground:
            self.jumping = False
        if self.on_ground or self.on_wall:
            self.can_double_jump = True
            self.wall_jumping = False
        if not self.jump_pressed:
            self.can_wall_jump = True

        # - wall jump -
        # before normal jump. Prevents double jump being checked before wall jump (BAD: infinite double jumps up walls)
        # if on wall or within sticky wall lenience window
        # input within jump window
        # not on the ground (so ground jump takes prescendence over wall jump)
        # allowed to wall jump (button has been lifted since last wall jump)
        # wanting jump (jump pressed)
        if self.sticky_wall_timer < self.sticky_wall_max and self.jump_timer < self.wall_jumpbuff_max and not \
                self.on_ground and self.can_wall_jump and self.jump_pressed:
            self.direction.y = -self.wall_jump_speed
            # sideways kick off, thrust opposite facing dir.
            # = rather than += to prevent dash interfering with jump, also cancel dash
            # // dt to counteract later * by dt. prevents dt being applied to instantaneous movement
            self.direction.x = (self.wall_kick_speed // dt) * -self.on_wall_right
            self.dashing = False
            self.wall_jumping = True
            self.can_wall_jump = False
            if self.extended_wall_jumps:
                self.jumping = True  # (wall jump)

        # - execute initial hop and allow jump extension (norm, buffer and coyote) -
        # if grounded and want jump (timer == 0) OR grounded and within buffer jump window (timer < max)
        # OR within coyote time window and want to jump
        # OR double jump
        elif (self.on_ground and self.jump_timer < self.jumpbuff_max) or \
                (self.jump_timer == 0 and self.coyote_timer < self.coyote_max) or \
                (self.jump_timer == 0 and self.can_double_jump):

            # - double jump -
            # if not on the ground and coyote window expired and has been able to jump,
            # must be double jumping, so prevent more double jumps
            if not self.on_ground and self.coyote_timer >= self.coyote_max:
                self.can_double_jump = False
                self.direction.y = 0

            # - coyote -
            self.coyote_timer = self.coyote_max  # prevents another coyote jump in mid air

            # - buffer jump -
            self.jump_hold_timer = 0  # Resets timer so buffjump has same extend window as norm.
            self.jump_timer = self.jumpbuff_max  # prevents repeated unwanted buffer jumps.

            # - norm jump - (start the jump)
            self.on_ground = False  # neccessary to prevent direction being cancelled by gravity on ground code later in loop
            # // dt to counteract later * by dt. prevents dt being applied to instantaneous movement
            self.direction.y = -self.jump_speed // dt
            self.jumping = True  # verifies that a jump is in progress

        # - extend jump (variable height) -
        # if already jumping (has hopped) and not exceeding max jump and want to jump still
        elif self.jumping and self.jump_hold_timer < self.jump_max and self.jump_pressed:
            self.direction.y = -self.jump_speed

        # - continue wall jump velocity -
        if self.wall_jumping and self.jump_timer < self.wall_jump_max:
            self.direction.x = self.wall_kick_speed * -self.on_wall_right
        else:
            self.wall_jumping = False

        self.jump_timer += round(1 * dt)  # increments the timer (time since jump input if jump hasnt been executed yet)
        self.jump_hold_timer += round(1 * dt)  # increments timer (time jump has been held for)

    def crouch(self, tiles):
        if self.crouching:
            # change to crouched hitbox and sync to the same pos as previous hitbox (using rect midbottom)
            self.hitbox = self.hitboxes["crouch"]
            self.sync_hitbox()
        # - exception case (if not crouching but should be forced to cause under platform) -
        else:
            # if normal hitbox top collides with a tile, make crouched
            for tile in tiles:
                if tile.hitbox.colliderect(self.hitboxes["normal"]):
                    if abs(tile.hitbox.bottom - self.hitboxes["normal"].top) < self.collision_tolerance:
                        # change to crouched hitbox and sync to the same pos as previous hitbox (using rect midbottom)
                        self.hitbox = self.hitboxes["crouch"]
                        self.sync_hitbox()
                        self.crouching = True
                        break

    def glide(self, dt):
        # resets glide if grounded. Prevents multiple full length glides in one flight
        # Can reset even if button is held.
        if self.on_ground or self.on_wall:
            self.glide_timer = 0
            self.gliding = False
        # if glide hasn't exceeded max time and falling and allowed to glide and not on wall (also not on ground from if statement),
        # continue to glide
        elif self.glide_timer < self.glide_max and self.direction.y > 0 and self.gliding:
            self.glide_timer += round(1 * dt)
            self.terminal_vel = self.glide_terminal_vel
        # ends self.gliding if glide has ended (terminal vel auto reset in update)
        elif self.glide_timer >= self.glide_max or not self.gliding:
            self.gliding = False

# -- visuals methods --

    def animator(self, dt):
        prev_anim = self.current_anim

        # determine animation corresponding with player state
        if self.crouching:
            self.current_anim = 'idle_crouch'
        elif self.facing_right == 1:
            self.current_anim = 'idle_right'
        elif self.facing_right == -1:
            self.current_anim = 'idle_left'

        # increment index and access required animation from dict
        anim_frames = self.animations[self.current_anim]
        self.frame_index += round(1 * dt)

        # if anim has changed or frame_index > than number of frames in anim, reset frame index
        if prev_anim != self.current_anim or self.frame_index > len(anim_frames) - 1:
            self.frame_index = 0

        # reassign player image
        self.image = anim_frames[int(self.frame_index)]

# -- update methods --

    # checks collision for a given hitbox (the player's) against given tiles on the x
    def collision_x(self, tiles):
        collision_offset = [0, 0]  # position hitbox is to be corrected to after checks
        # if on wall on prev frame, push one pixel towards wall so collision checks == true. Stays sliding on wall
        if self.on_wall:
            self.hitbox.x += self.on_wall_right
        self.on_wall = False  # assume false until proven true

        top = False
        top_margin = False
        bottom = False
        bottom_margin = False

        for tile in tiles:
            if tile.hitbox.colliderect(self.hitbox):
                # - normal collision checks -
                # abs ensures only the desired side registers collision
                # not having collisions dependant on status allows hitboxes to change size
                if abs(tile.hitbox.right - self.hitbox.left) < self.collision_tolerance:
                    collision_offset[0] = tile.hitbox.right - self.hitbox.left
                    self.on_wall_right = -1  # player touching on left
                elif abs(tile.hitbox.left - self.hitbox.right) < self.collision_tolerance:
                    collision_offset[0] = tile.hitbox.left - self.hitbox.right
                    self.on_wall_right = 1  # player touching on right

                # - wall cling - (self.on_wall_right above)
                # if not crouching, allow wall clinging
                if not self.crouching:
                    self.on_wall = True
                    self.terminal_vel = self.wall_term_vel

                #- horizontal corner correction - (for both side collisions)

                # checking allowed to corner correct
                # Use a diagram. Please
                # checks if the relevant horizontal raycasts on the player hitbox are within a tile or not
                # this allows determination as to whether on the end of a column of tiles or not

                # top
                if tile.hitbox.top <= self.hitbox.top <= tile.hitbox.bottom:
                    top = True
                if tile.hitbox.top <= self.hitbox.top + self.corner_correction <= tile.hitbox.bottom:
                    top_margin = True
                # stores tile for later potential corner correction
                if self.hitbox.top < tile.hitbox.bottom < self.hitbox.top + self.corner_correction:
                    collision_offset[1] = tile.hitbox.bottom - self.hitbox.top

                # bottom
                if tile.hitbox.top <= self.hitbox.bottom <= tile.hitbox.bottom:
                    bottom = True
                if tile.hitbox.top <= self.hitbox.bottom - self.corner_correction <= tile.hitbox.bottom:
                    bottom_margin = True
                if self.hitbox.bottom > tile.hitbox.top > self.hitbox.bottom - self.corner_correction:
                    collision_offset[1] = -(self.hitbox.bottom - tile.hitbox.top)

        # -- application of offsets --
        # must occur after checks so that corner correction can check every contacted tile
        # without movement of hitbox half way through checks
        # - collision correction -
        self.hitbox.x += collision_offset[0]
        # - corner correction -
        # adding velocity requirement prevents correction when just walking towards a wall. Only works at a higher
        # velocity like during a dash or if the player is boosted.
        if ((top and not top_margin) or (bottom and not bottom_margin)) and abs(self.direction.x) >= self.dash_speed:
            self.hitbox.y += collision_offset[1]

        self.sync_rect()

    # checks collision for a given hitbox (the player's) against given tiles on the y
    def collision_y(self, tiles):
        collision_offset = [0, 0]
        self.on_ground = False

        left = False
        left_margin = False
        right = False
        right_margin = False

        bonk = False

        for tile in tiles:
            if tile.hitbox.colliderect(self.hitbox):
                # abs ensures only the desired side registers collision
                if abs(tile.hitbox.top - self.hitbox.bottom) < self.collision_tolerance:
                    self.on_ground = True
                    collision_offset[1] = tile.hitbox.top - self.hitbox.bottom
                # collision with bottom of tile
                elif abs(tile.hitbox.bottom - self.hitbox.top) < self.collision_tolerance:
                    collision_offset[1] = tile.hitbox.bottom - self.hitbox.top

                    # - vertical corner correction - (only for top, not bottom collision)
                    # left
                    if tile.hitbox.left <= self.hitbox.left <= tile.hitbox.right:
                        left = True
                    if tile.hitbox.left <= self.hitbox.left + self.corner_correction <= tile.hitbox.right:
                        left_margin = True
                    if self.hitbox.left < tile.hitbox.right < self.hitbox.left + self.corner_correction:
                        collision_offset[0] = tile.hitbox.right - self.hitbox.left

                    # right
                    if tile.hitbox.left <= self.hitbox.right <= tile.hitbox.right:
                        right = True
                    if tile.hitbox.left <= self.hitbox.right - self.corner_correction <= tile.hitbox.right:
                        right_margin = True
                    if self.hitbox.right > tile.hitbox.left > self.hitbox.right - self.corner_correction:
                        collision_offset[0] = -(self.hitbox.right - tile.hitbox.left)

                    bonk = True

        # -- application of offsets --
        # - normal collisions -
        self.hitbox.y += collision_offset[1]
        # - corner correction -
        if (left and not left_margin) or (right and not right_margin):
            self.hitbox.x += collision_offset[0]
            self.hitbox.y -= self.vertical_corner_correction_boost
        # drop by zeroing upwards velocity if corner correction isn't necessary and hit bottom of tile
        elif bonk:
            self.direction.y = 0

        # resyncs up rect to the hitbox
        self.sync_rect()

    # contains gravity + it's exceptions(gravity code from clearcode platformer tut), terminal velocity, fall timer
    # and application of y direction
    def apply_y_direction(self, dt):
        # -- gravity --
        # if dashing, set direction.y to 0 to allow float
        if self.dashing:
            self.direction.y = 0
        # when on the ground set direction.y to 1. Prevents gravity accumulation. Allows accurate on_ground detection
        # must be greater than 1 so player falls into below tile's hitbox every frame and is brought back up
        elif self.on_ground:
            self.direction.y = 1
        # if not dashing or on the ground apply gravity normally
        else:
            # if falling, apply more gravity than if moving up
            if self.direction.y > 0:
                self.direction.y += self.fall_gravity * dt
            else:
                self.direction.y += self.gravity * dt

        # -- terminal velocity --
        # must be constant despite fps (cap on y vel). Therefore applied after dt application
        if self.direction.y > self.terminal_vel:
            self.direction.y = self.terminal_vel

        # -- fall timer --
        # if falling in the air, increment timer else its 0
        if self.direction.y > 0 and not self.on_ground:
            self.fall_timer += round(1 * dt)
        else:
            self.fall_timer = 0

        # -- apply y direction and sync --
        self.rect.y += round(self.direction.y * dt)
        self.sync_hitbox()

    # syncs the player's current and stored hitboxes with the player rect for proper collisions. For use after movement of player rect.
    def sync_hitbox(self):
        self.hitbox.midbottom = self.rect.midbottom
        for hitbox in self.hitboxes:
            self.hitboxes[hitbox].midbottom = self.rect.midbottom

    # syncs the player's rect with the current hitbox for proper movement. For use after movement of main hitbox
    def sync_rect(self):
        self.rect.midbottom = self.hitbox.midbottom

    def apply_scroll(self, scroll_value):
        # must be here for when camera is initally created in room and scroll value is applied to all tiles
        # must be applied to mask as well otherwise it is consistently out by initial scroll value
        self.light_background_mask.sprite.apply_scroll(scroll_value)

        self.rect.x -= int(scroll_value[0])
        self.rect.y -= int(scroll_value[1])
        self.sync_hitbox()

    def update(self, dt, collision_tiles, scroll_value):
        self.terminal_vel = self.norm_terminal_vel  # resets terminal vel for next frame. Allows wall cling and glide to
        # reset without interfering with each other.
        self.hitbox = self.hitboxes["normal"]  # same with hitbox as terminal vel
        self.sync_hitbox()  # just in case

        # -- INPUT --
        self.get_input(dt, collision_tiles)

        # -- CHECKS/UPDATE --

        # - collision and movement -
        # applies direction to player then resyncs hitbox (included in most movement/collision functions)
        # HITBOX MUST BE SYNCED AFTER EVERY MOVE OF PLAYER RECT
        # x and y collisions are separated to make diagonal collisions easier and simpler to handle
        # x
        self.rect.x += round(self.direction.x * dt)
        self.sync_hitbox()
        self.collision_x(collision_tiles)

        # y
        # applies direction to player then resyncs hitbox
        self.apply_y_direction(dt)  # gravity
        self.collision_y(collision_tiles)

        # sticky walls
        # is on the ground or not on the wall, reset sticky timer
        if self.on_ground and not self.on_wall:
            self.sticky_wall_timer = 0
        # if pressing right and colliding on the left, or vise versa, increment sticky
        elif (self.right_pressed and not self.on_wall_right) or (self.left_pressed and self.on_wall_right):
            pass

        # scroll shouldn't have collision applied, it is separate movement
        self.apply_scroll(scroll_value)

        # light (after movement and scroll so pos is accurate)
        for light in self.lights:
            light.update(dt, self.rect.center, collision_tiles)

        # animate after movement checks
        self.animator(dt)

# -- render method --

    def draw(self):
        # draw lights
        for light in self.lights:
            light.draw(self.light_background_mask.sprite)
        # draw player
        self.surface.blit(self.image, self.rect)
