# - libraries -
import pygame
from pytmx.util_pygame import load_pygame  # allows use of tiled tile map files for pygame use
# - general -
from game_data import controller_map, fonts
from support import *
# - tiles -
from tiles import CollideableTile, HazardTile
# - objects -
from player import Player
from trigger import Trigger, SpawnTrigger
from spawn import Spawn
# - systems -
from camera import Camera
from text import Font


class Room:
    def __init__(self, dt, fps, room_data, screen_surface, screen_rect, controllers, previous_room):
        # TODO testing, remove
        self.dev_debug = False

        # level setup
        self.screen_surface = screen_surface  # main screen surface
        self.screen_rect = screen_rect
        self.screen_width = screen_surface.get_width()
        self.screen_height = screen_surface.get_height()

        self.controllers = controllers

        self.previous_room = previous_room  # room exited when entering current room
        self.player_spawn = None  # contains the current player spawn, point object (position and name)

        self.pause = False
        self.pause_pressed = False

        #dt = dt  # dt starts as 1 because on the first frame we can assume it is 60fps. dt = 1/60 * 60 = 1

        # - get level data -
        tmx_data = load_pygame(resource_path(room_data))  # tile map file
        self.all_sprites = pygame.sprite.Group()  # contains all sprites for ease of updating/scrolling

        # get objects
        self.transitions = self.create_object_group(tmx_data, 'transitions', 'Trigger')
        self.player_spawns = self.create_object_group(tmx_data, 'spawns', 'Spawn')
        self.spawn_triggers = self.create_object_group(tmx_data, 'spawns', 'SpawnTrigger')
        # self.player_spawn_triggers = self.create_object_group(tmx_data, 'spawns', 'Trigger')
        self.player = self.create_object_group(tmx_data, '', 'Player')  # must be completed after player_spawns layer

        # get tiles
        self.collideable = self.create_tile_group(tmx_data, 'collideable', 'CollideableTile')
        self.tiles_in_screen = []
        self.hazards = self.create_tile_group(tmx_data, 'hazards', 'HazardTile')  # TODO hazard, what type?
        self.abs_camera_boundaries = {
            'x': self.create_tile_group(tmx_data, 'abs camera boundaries x', 'CollideableTile'),
            'y': self.create_tile_group(tmx_data, 'abs camera boundaries y', 'CollideableTile')}

        # camera setup
        self.camera = Camera(self.screen_surface, self.screen_rect, self.player.sprite, self.abs_camera_boundaries, controllers)
        self.camera.focus(True)  # focuses camera on target
        scroll_value = self.camera.get_scroll(dt, fps)  # returns scroll, now focused
        self.player.sprite.apply_scroll(scroll_value)  # applies new scroll to player
        self.all_sprites.update(scroll_value)  # applies new scroll to all sprites

        # text setup
        self.small_font = Font(resource_path(fonts['small_font']), 'white')
        self.large_font = Font(resource_path(fonts['large_font']), 'white')

# -- set up room methods --

    # creates all the neccessary types of tiles seperately and places them in individual layer groups
    def create_tile_group(self, tmx_file, layer_name, type):
        sprite_group = pygame.sprite.Group()
        layer = tmx_file.get_layer_by_name(layer_name).tiles()

        if type == 'CollideableTile':
            # gets layer from tmx and creates StaticTile for every tile in the layer, putting them in both SpriteGroups
            for x, y, surface in layer:
                tile = CollideableTile((x * tile_size, y * tile_size), tile_size, surface)
                sprite_group.add(tile)
                self.all_sprites.add(tile)
        elif type == 'HazardTile':
            for x, y, surface in layer:
                tile = HazardTile((x * tile_size, y * tile_size), tile_size, surface, self.player.sprite)
                sprite_group.add(tile)
                self.all_sprites.add(tile)
        else:
            raise Exception(f"Invalid create_tile_group type: '{type}' ")

        return sprite_group

    def create_object_group(self, tmx_file, layer_name, object_class):
        sprite_group = pygame.sprite.Group()
        if layer_name:  # prevents accessing '' layer in case of player
            layer = tmx_file.get_layer_by_name(layer_name)

        if object_class == 'SpawnTrigger':
            for obj in layer:  # can iterate over for objects
                # checks if object is a trigger (multiple object types/classes could be in the layer)
                if obj.type == object_class:
                    spawn_data = tmx_file.get_object_by_id(obj.trigger_spawn)
                    spawn = Spawn(spawn_data.x, spawn_data.y, spawn_data.name, spawn_data.player_facing)
                    trigger = SpawnTrigger(obj.x, obj.y, obj.width, obj.height, obj.name, spawn)
                    sprite_group.add(trigger)
                    self.all_sprites.add(trigger)

        elif object_class == "Trigger":
            for obj in layer:
                if obj.type == object_class:
                    trigger = Trigger(obj.x, obj.y, obj.width, obj.height, obj.name)
                    sprite_group.add(trigger)
                    self.all_sprites.add(trigger)

        elif object_class == 'Spawn':
            sprite_group = {}
            for obj in layer:
                # multiple types of object could be in layer, so checking it is correct object type (spawn)
                if obj.type == object_class:
                    # creates a dictionary containing spawn name: spawn pairs for ease and efficiency of access
                    spawn = Spawn(obj.x, obj.y, obj.name, obj.player_facing)
                    sprite_group[spawn.name] = spawn
                    self.all_sprites.add(spawn)

        elif object_class == 'Player':
            sprite_group = pygame.sprite.GroupSingle()
            # finds the correct starting position corresponding to the last room/transition
            # TODO remove need for self.player_spawns
            spawn = self.player_spawns[self.previous_room]
            player = Player(spawn, self.screen_surface, self.controllers)
            sprite_group.add(player)
            self.player_spawn = spawn  # stores the spawn instance for future respawn
        else:
            raise Exception(f"Invalid create_object_group type: '{type}' ")

        return sprite_group

# -- check methods --

    def get_input(self):
        keys = pygame.key.get_pressed()

        # pause
        # pause pressed prevents holding key and rapidly switching between T and F
        if keys[pygame.K_p] or keys[pygame.K_ESCAPE] or self.get_controller_input('pause'):
            if not self.pause_pressed:
                self.pause = not self.pause
            self.pause_pressed = True
        # if not pressed
        else:
            self.pause_pressed = False

        # TODO testing, remove ###################
        if (keys[pygame.K_z] and keys[pygame.K_LSHIFT]) or self.get_controller_input('dev off'):
            self.dev_debug = False
        elif keys[pygame.K_z] or self.get_controller_input('dev on'):
            self.dev_debug = True

    # checks controller inputs and returns true or false based on passed check
    def get_controller_input(self, input_check):
        # check if controllers are connected before getting controller input (done every frame preventing error if suddenly disconnected)
        if len(self.controllers) > 0:
            controller = self.controllers[0]
            # TODO testing, remove ###################
            if input_check == 'dev on' and controller.get_button(controller_map['share']):
                return True
            elif input_check == 'dev off' and controller.get_button(controller_map['share']) and controller.get_button(controller_map['X']):
                return True

            elif input_check == 'pause' and controller.get_button(controller_map['options']):
                return True
        return False

    # checks if player has collided with a room_transition trigger
    def room_transitions(self):
        player = self.player.sprite
        # loop through all the game objects for the level transition trigger rectangles
        for trigger in self.transitions:
            # if player has hit a transition, return the transition (new room's) name to the main game loop for new instance
            # otherwise return false
            if trigger.hitbox.colliderect(player.hitbox):
                return trigger.name
        return False

# -- visual --

    # draw tiles in tile group but only if in camera view (in tile.draw method)
    def draw_tile_group(self, group):
        for tile in group:
            # render tile
            tile.draw(self.screen_surface, self.screen_rect)
            # TODO testing, remove
            if self.dev_debug:
                pygame.draw.rect(self.screen_surface, 'green', tile.hitbox, 1)

# -- menus --

    def pause_menu(self):
        pause_surf = pygame.Surface((self.screen_surface.get_width(), self.screen_surface.get_height()))
        pause_surf.fill((40, 40, 40))
        self.screen_surface.blit(pause_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        width = self.large_font.width('PAUSED')
        self.large_font.render('PAUSED', self.screen_surface, (center_object_x(width, self.screen_surface), 20))

# -- getters and setters --

    def get_camera_zoom(self):
        return self.camera.get_zoom()

# -------------------------------------------------------------------------------- #

    # updates the level allowing tile scroll and displaying tiles to screen
    # order is equivalent of layers
    def update(self, dt, fps):
        # #### INPUT > GAME(checks THEN UPDATE) > RENDER ####
        # checks deal with previous frames interactions. Update creates interactions for this frame which is then diplayed
        player = self.player.sprite

        # -- INPUT --
        self.get_input()

        # -- CHECKS (For the previous frame) --

        # pauses the game if window is minimized
        if not pygame.display.get_active():
            self.pause = True

        if not self.pause:

            # scroll -- must be first, camera calculates scroll, stores it and returns it for application
            scroll_value = self.camera.get_scroll(dt, fps)
            self.camera.focus(False)

            # which object should handle collision? https://gamedev.stackexchange.com/questions/127853/how-to-decide-which-gameobject-should-handle-the-collision

            # checks if player has collided with spawn trigger and updates spawn
            for spawn_trigger in self.spawn_triggers:
                if player.hitbox.colliderect(spawn_trigger.hitbox):
                    self.player_spawn = spawn_trigger.trigger_spawn
                    #self.player_spawn = self.player_spawns[trigger.name]
                    break

            # checks if the player needs to respawn and therefore needs to focus on the player
            if player.get_respawn():
                self.camera.focus(True)

        # -- UPDATES -- player needs to be before tiles for scroll to function properly
            player.update(dt, self.collideable, scroll_value, self.player_spawn)
            self.all_sprites.update(scroll_value)

        # -- RENDER --
        # Draw
        self.player.sprite.draw()
        self.draw_tile_group(self.collideable)
        self.draw_tile_group(self.hazards)

        # must be after other renders to ensure menu is drawn last
        if self.pause:
            self.pause_menu()

        # Dev Tools
        if self.dev_debug:
            ####### player hitbox #######
            pygame.draw.rect(self.screen_surface, 'grey', self.player.sprite.crouch_hitbox, 1)
            pygame.draw.rect(self.screen_surface, 'grey', self.player.sprite.norm_hitbox, 1)
            pygame.draw.rect(self.screen_surface, 'yellow', self.player.sprite.hitbox, 1)
            ####### center of screen for testing ######
            pygame.draw.line(self.screen_surface, (34, 22, 43), (self.screen_surface.get_width() // 2, 0), (self.screen_surface.get_width() // 2, self.screen_surface.get_height()), width=1)
            pygame.draw.line(self.screen_surface, (34, 22, 43), (0, self.screen_surface.get_height() // 2), (self.screen_surface.get_width(), self.screen_surface.get_height() // 2), width=1)
            ####### for seeing camera target point #######
            pygame.draw.circle(self.screen_surface, 'blue', self.camera.target, 2)
            for trigger in self.transitions:
                pygame.draw.rect(self.screen_surface, 'purple', trigger.hitbox, 1)
            for trigger in self.spawn_triggers:
                pygame.draw.rect(self.screen_surface, 'purple', trigger.hitbox, 1)
            for hazard in self.hazards:
                pygame.draw.rect(self.screen_surface, 'red', hazard.hitbox, 1)
            for spawn in self.player_spawns:
                pygame.draw.circle(self.screen_surface, 'purple', (self.player_spawns[spawn].x, self.player_spawns[spawn].y), 2)
            pygame.draw.circle(self.screen_surface, 'yellow', (self.player_spawn.x, self.player_spawn.y), 2)
