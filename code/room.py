# - libraries -
import pygame
from pytmx.util_pygame import load_pygame  # allows use of tiled tile map files for pygame use
# - general -
from game_data import tile_size, controller_map
from support import resource_path
# - tiles -
from tiles import CollideableTile, HazardTile
# - objects -
from player import Player
from trigger import Trigger
from spawn import Spawn
# - systems -
from camera import Camera


class Room:
    def __init__(self, room_data, screen_surface, screen_rect, controllers, previous_room):
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

        # - get level data -
        tmx_data = load_pygame(resource_path(room_data))  # tile map file
        self.all_sprites = pygame.sprite.Group()  # contains all sprites for ease of updating/scrolling

        # get objects
        self.transitions = self.create_object_group(tmx_data, 'transitions', 'Trigger')
        self.player_spawns = self.create_object_group(tmx_data, 'spawns', 'Spawn')
        self.spawn_triggers = self.create_object_group(tmx_data, 'spawns', 'Trigger')
        # self.player_spawn_triggers = self.create_object_group(tmx_data, 'spawns', 'Trigger')
        self.player = self.create_object_group(tmx_data, '', 'Player')  # must be completed after player_spawns layer

        # get tiles
        self.collideable = self.create_tile_group(tmx_data, 'collideable', 'CollideableTile')
        self.hazards = self.create_tile_group(tmx_data, 'hazards', 'HazardTile')  # TODO hazard, what type?
        self.abs_camera_boundaries = {}
        self.abs_camera_boundaries['x'] = self.create_tile_group(tmx_data, 'abs camera boundaries x', 'CollideableTile')
        self.abs_camera_boundaries['y'] = self.create_tile_group(tmx_data, 'abs camera boundaries y', 'CollideableTile')

        # camera setup
        self.camera = Camera(self.screen_surface, self.screen_rect, self.player.sprite, self.abs_camera_boundaries, controllers)
        self.camera.focus(True)  # focuses camera on target
        scroll_value = self.camera.return_scroll()  # returns scroll, now focused
        self.player.sprite.apply_scroll(scroll_value)  # applies new scroll to player
        self.all_sprites.update(scroll_value)  # applies new scroll to all sprites

# -- set up room methods --

    # creates all the neccessary types of tiles seperately and places them in individual layer groups
    def create_tile_group(self, tmx_file, layer, type):
        sprite_group = pygame.sprite.Group()

        if type == 'CollideableTile':
            # gets layer from tmx and creates StaticTile for every tile in the layer, putting them in both SpriteGroups
            for x, y, surface in tmx_file.get_layer_by_name(layer).tiles():
                tile = CollideableTile((x * tile_size, y * tile_size), tile_size, surface)
                sprite_group.add(tile)
                self.all_sprites.add(tile)
        elif type == 'HazardTile':
            for x, y, surface in tmx_file.get_layer_by_name(layer).tiles():
                tile = HazardTile((x * tile_size, y * tile_size), tile_size, surface, self.player.sprite)
                sprite_group.add(tile)
                self.all_sprites.add(tile)
        else:
            raise Exception(f"Invalid create_tile_group type: '{type}' ")

        return sprite_group

    def create_object_group(self, tmx_file, layer, object):
        sprite_group = pygame.sprite.Group()
        if object == 'Trigger':
            for obj in tmx_file.get_layer_by_name(layer):  # can iterate over for objects
                # checks if object is a trigger (multiple objects could be in the layer
                if obj.type == 'trigger':
                    trigger = Trigger(obj.x, obj.y, obj.width, obj.height, obj.name)
                    sprite_group.add(trigger)
                    self.all_sprites.add(trigger)
        elif object == 'Spawn':
            sprite_group = {}
            for obj in tmx_file.get_layer_by_name(layer):
                # multiple types of object could be in layer, so checking it is correct object type (spawn)
                if obj.type == 'spawn':
                    spawn = Spawn(obj.x, obj.y, obj.name, obj.player_facing)
                    sprite_group[spawn.name] = spawn
                    self.all_sprites.add(spawn)
        elif object == 'Player':
            sprite_group = pygame.sprite.GroupSingle()
            # finds the correct starting position corresponding to the last room/transition
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
        if keys[pygame.K_p] or self.get_controller_input('pause'):
            if not self.pause_pressed:
                self.pause = not self.pause
            self.pause_pressed = True
        # if not pressed
        else:
            self.pause_pressed = False


        # TODO testing, remove
        if (keys[pygame.K_z] and keys[pygame.K_LSHIFT]) or self.get_controller_input('dev off'):
            self.dev_debug = False
        elif keys[pygame.K_z] or self.get_controller_input('dev on'):
            self.dev_debug = True

    # checks controller inputs and returns true or false based on passed check
    def get_controller_input(self, input_check):
        # check if controllers are connected before getting controller input (done every frame preventing error if suddenly disconnected)
        if len(self.controllers) > 0:
            controller = self.controllers[0]
            # TODO testing, remove
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

    # updates the level allowing tile scroll and displaying tiles to screen
    # order is equivalent of layers
    def run(self):
        # #### INPUT > GAME > RENDER ####
        player = self.player.sprite

        # -- INPUT --
        self.get_input()

        # -- UPDATES --
        if not self.pause:
            # checks

            # scroll -- must be first, camera calculates scroll, stores it and returns it for application
            scroll_value = self.camera.return_scroll()
            # resets focus camera, only if it has had a chance to be passed to camera
            self.camera.focus(False)

            # TODO check player respawn should be after player update
            # which object should handle collision? https://gamedev.stackexchange.com/questions/127853/how-to-decide-which-gameobject-should-handle-the-collision
            # checks if player has collided with spawn trigger and updates spawn
            # then checks if the player needs to respawn
            for trigger in self.spawn_triggers:
                if player.hitbox.colliderect(trigger.hitbox):
                    self.player_spawn = self.player_spawns[trigger.name]
                    break
            if player.get_respawn():
                self.camera.focus(True)

            # Updates -- player needs to be before tiles for scroll to function properly
            player.update(self.collideable, scroll_value, self.player_spawn)
            self.all_sprites.update(scroll_value)

        # -- RENDER --
        # Draw
        self.draw_tile_group(self.collideable)
        self.player.sprite.draw()
        self.draw_tile_group(self.hazards)

        # Dev Tools
        if self.dev_debug:
            ####### player hitbox #######
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
