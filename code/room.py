# - libraries -
import pygame
from pytmx.util_pygame import load_pygame  # allows use of tiled tile map files for pygame use
# - general -
from game_data import tile_size
# - tiles -
from tiles import StaticTile
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
        tmx_data = load_pygame(room_data)  # tile map file
        self.all_sprites = pygame.sprite.Group()  # contains all sprites for ease of updating/scrolling

        # get tiles
        self.collideable = self.create_tile_group(tmx_data, 'collideable', 'StaticTile')
        self.hazards = self.create_tile_group(tmx_data, 'hazards', 'StaticTile')  # TODO hazard, what type?

        # get objects
        self.transitions = self.create_object_group(tmx_data, 'transitions', 'Trigger')
        self.player_spawns = self.create_object_group(tmx_data, 'spawns', 'Spawn')
        #self.player_spawn_triggers = self.create_object_group(tmx_data, 'spawns', 'Trigger')
        self.player = self.create_object_group(tmx_data, '', 'Player')  # must be completed after player_spawns layer

        # camera setup
        self.camera = Camera(self.screen_surface, self.player.sprite)
        self.focus_camera = True
        scroll_value = self.camera.return_scroll(self.focus_camera)  # brings focus onto the player with scroll immediately
        self.player.sprite.apply_scroll(scroll_value)  # applies new scroll to player
        self.all_sprites.update(scroll_value)  # applies new scroll to all tiles

# -- set up room methods --

    # creates all the neccessary types of tiles seperately and places them in individual layer groups
    def create_tile_group(self, tmx_file, layer, type):
        sprite_group = pygame.sprite.Group()

        if type == 'StaticTile':
            # gets layer from tmx and creates StaticTile for every tile in the layer, putting them in both SpriteGroups
            for x, y, surface in tmx_file.get_layer_by_name(layer).tiles():
                tile = StaticTile((x * tile_size, y * tile_size), tile_size, surface)
                sprite_group.add(tile)
                self.all_sprites.add(tile)
        else:
            raise Exception(f"Invalid create_tile_group type: '{type}' ")

        return sprite_group

    # TODO more efficient?? less repetition in lines
    def create_object_group(self, tmx_file, layer, type):
        if type == 'Trigger':
            sprite_group = pygame.sprite.Group()
            for obj in tmx_file.get_layer_by_name(layer):  # can iterate over for objects
                print(obj.type)
                trigger = Trigger(obj.x, obj.y, obj.width, obj.height, obj.name)
                sprite_group.add(trigger)
                self.all_sprites.add(trigger)
        elif type == 'Spawn':
            sprite_group = pygame.sprite.Group()
            for obj in tmx_file.get_layer_by_name(layer):
                #print(obj.type)
                # multiple types of object could be in layer, so checking it is correct object type (spawn)
                #TODO if obj.type == 'spawn':
                spawn = Spawn(obj.x, obj.y, obj.name)
                sprite_group.add(spawn)
                self.all_sprites.add(spawn)
        elif type == 'Player':
            sprite_group = pygame.sprite.GroupSingle()
            # loops through spawn points to find the correct starting position corresponding to the last room/transition
            for spawn in self.player_spawns:
                if spawn.name == self.previous_room:
                    player = Player((spawn.x, spawn.y), self.screen_surface, self.controllers)
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
        if keys[pygame.K_p]:
            if not self.pause_pressed:
                self.pause = not self.pause
            self.pause_pressed = True
        elif not keys[pygame.K_p]:
            self.pause_pressed = False


        # TODO testing, remove
        if keys[pygame.K_z] and keys[pygame.K_LSHIFT]:
            self.dev_debug = False
        elif keys[pygame.K_z]:
            self.dev_debug = True

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

    def respawn_player(self):
        player = self.player.sprite
        for hazard in self.hazards:
            if hazard.hitbox.colliderect(player.hitbox):
                player.respawn((self.player_spawn.x, self.player_spawn.y))
                self.focus_camera = True

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

        # reset neccessary variables
        self.focus_camera = False

        # -- INPUT --
        self.get_input()

        # -- UPDATES --
        if not self.pause:
            # checks
            # TODO order is screwed
            self.respawn_player()  # check if player has collided with hazard. If so, set player to relevant spawn point

            # scroll -- must be first, camera calculates scroll, stores it and returns it for application
            scroll_value = self.camera.return_scroll(self.focus_camera)

            # Updates -- player needs to be before tiles for scroll to function properly
            self.player.update(self.collideable, scroll_value)
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
            ####### for seeing camera target point #######
            pygame.draw.circle(self.screen_surface, 'blue', self.camera.target, 2)
            for trigger in self.transitions:
                pygame.draw.rect(self.screen_surface, 'purple', trigger.hitbox, 1)
            for hazard in self.hazards:
                pygame.draw.rect(self.screen_surface, 'red', hazard.hitbox, 1)
            for spawn in self.player_spawns:
                pygame.draw.circle(self.screen_surface, 'orange', (spawn.x, spawn.y), 2)
            pygame.draw.circle(self.screen_surface, 'darkorange', (self.player_spawn.x, self.player_spawn.y), 2)
