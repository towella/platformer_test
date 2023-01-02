import pygame
from pytmx.util_pygame import load_pygame  # allows use of tiled tile map files for pygame use

from game_data import tile_size
from tiles import StaticTile
from player import Player
from camera import Camera
from support import import_csv_layout, import_cut_graphics


class Level:
    def __init__(self, level_data, screen_surface, screen_rect, controllers):
        # TODO testing, remove
        self.dev_debug = False

        # level setup
        self.screen_surface = screen_surface  # main screen surface
        self.screen_rect = screen_rect
        self.screen_width = screen_surface.get_width()
        self.screen_height = screen_surface.get_height()
        self.controllers = controllers

        # takes in csvs into dictionary with same key (layer) names
        self.layer_data = {}
        for csv in level_data:
            self.layer_data[csv] = import_csv_layout(level_data[csv])
        # creates list of tile textures
        # TODO fix directory and file selection when art is done
        #self.tile_textures = import_cut_graphics(f'../graphics/tiles/tilesets/tileset.png', 16)

        # turns csv into coresponding tiles in a sprite group
        self.all_tiles = pygame.sprite.Group()  # contains all tiles for ease of scrolling

        # tiles
        self.collideable = self.create_tile_group(self.layer_data['collideable'], 'static')  # contains all collideable tiles
        # other
        self.hazards = self.create_tile_group(self.layer_data['hazards'], 'hazard')
        self.player = self.create_tile_group(self.layer_data['player'], 'player')

        # camera setup
        self.camera = Camera(self.screen_surface, self.player.sprite)
        scroll_value = self.camera.focus_target()  # brings focus onto the player with scroll immediately
        self.player.sprite.apply_scroll(scroll_value)  # applies new scroll to player
        self.all_tiles.update(scroll_value)  # applies new scroll to all tiles

    # sets up tile sprite group based on level data
    '''def setup_level(self, layout):
        self.tiles = pygame.sprite.Group()
        self.player = pygame.sprite.GroupSingle()

        for row_index, row in enumerate(layout):  # enumerate gives the index and information (!so cool!)
            for column_index, cell in enumerate(row):
                x = column_index * tile_size  # sets x coordinate
                y = row_index * tile_size  # sets y coordinate

                # checks for tile
                if cell == 'X':
                    tile = Tile((x, y), tile_size)
                    self.tiles.add(tile)
                # checks for player
                elif cell == 'P':
                    player_sprite = Player((x, y), self.screen_surface)
                    self.player.add(player_sprite)'''

    # creates all the neccessary types of tiles seperately and places them in individual layer groups
    def create_tile_group(self, layout, type):
        sprite_group = pygame.sprite.Group()
        # layers must have the same name as directories and file names

        for row_index, row in enumerate(layout):  # enumerate gives index and row list
            for column_index, val in enumerate(row):
                # if the tile isn't empty space
                #print(val)
                if val != '-1':
                    #print('here')
                    x = column_index * tile_size
                    y = row_index * tile_size

                    # static
                    if type == 'static':
                        #tile_surface = self.tile_textures[int(val)]  # the index of the surface is the same as the csv

                        # TODO temporary, see above comment ^
                        tile_surface = pygame.Surface((tile_size, tile_size))
                        tile_surface.fill((213, 202, 202))

                        # values as a result of the way the tilesheet is sliced and placed in the list
                        # essentially automatically coresponds number with tile type without copious if statements
                        sprite = StaticTile((x, y), tile_size, tile_surface)
                        sprite_group.add(sprite)
                        self.all_tiles.add(sprite)

                        '''elif type == 'hazard':
                            tile_surface = pygame.Surface((tile_size, tile_size))
                            tile_surface.fill('red')
                            
                            sprite = StaticTile((x, y), tile_size, tile_surface)
                            sprite_group.add(sprite)
                            self.all_tiles.add(sprite)'''

                    elif type == 'player':
                        player_sprite = Player((x, y), self.screen_surface, self.controllers)
                        return pygame.sprite.GroupSingle(player_sprite)
        return sprite_group

    # draw tiles in tile group but only if in camera view
    def draw_tile_group(self, group):
        for tile in group:
            # render tile
            self.screen_surface.blit(tile.image, tile.rect)
            # TODO testing, remove
            if self.dev_debug:
                pygame.draw.rect(self.screen_surface, 'red', tile.hitbox, 2)

    def get_input(self):
        keys = pygame.key.get_pressed()

        # TODO testing, remove
        if keys[pygame.K_z] and keys[pygame.K_LSHIFT]:
            self.dev_debug = False
        elif keys[pygame.K_z]:
            self.dev_debug = True

    # updates the level allowing tile scroll and displaying tiles to screen
    # order is equivalent of layers
    def run(self):
        # scroll -- must be first, camera calculates scroll, stores it and returns it for application
        scroll_value = self.camera.return_scroll()

        self.get_input()  # TODO is this the right spot??

        # Updates -- player needs to be before tiles for scroll to function properly
        self.player.update(self.collideable, scroll_value)
        self.all_tiles.update(scroll_value)

        # Draw
        self.draw_tile_group(self.collideable)
        self.player.sprite.draw()

        if self.dev_debug:
            ####### player hitbox #######
            pygame.draw.rect(self.screen_surface, 'red', self.player.sprite.hitbox, 2)
            ####### center of screen for testing ######
            pygame.draw.line(self.screen_surface, (34, 22, 43), (self.screen_surface.get_width() // 2, 0), (self.screen_surface.get_width() // 2, self.screen_surface.get_height()), width=1)
            ####### for seeing camera target point #######
            pygame.draw.circle(self.screen_surface, (73, 220, 177), self.camera.target, 2)



# TODO make tiles more efficent
# TODO animated tile class
# TODO implement delta time movement?? See how it goes