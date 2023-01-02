import pygame, os, sys
from csv import reader
from game_data import tile_size


# allows paths to be used for both normal running in PyCharm and as an .exe
def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        relative_path = relative_path[3:]  # slices path if using executable to absolute path. Otherwise use relative for PyCharm
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# https://riptutorial.com/pygame/example/23788/transparency    info on alpha values in surfaces (opacity and clear pixels)

# imports all the images in a single folder
# based on passed entity whether it resizes and/or returns list or image surface
def import_folder(path, return_type):
    surface_list = []
    allowed_file_types = ['.png', '.jpg', '.jpeg', '.gif']

    for folder_name, sub_folders, img_files in os.walk(path):
        img_files.sort()
        for image in img_files:
            for type in allowed_file_types:
                if type in image.lower():  # prevents invisible non image files causing error while allowing image type to be flexible (e.g. .DS_Store)
                    full_path = path + '/' + image  # accesses image from directory by creating path name
                    image_surface = pygame.image.load(full_path).convert_alpha()  # adds image to surface (convert alpha is best practice)

                    resized_width = image_surface.get_width() * 4  # each art pixel is 4 real pixels. Scales up art to appropriate game size
                    resized_height = image_surface.get_height() * 4
                    image_surface = pygame.transform.scale(image_surface, (resized_width, resized_height))

                    if return_type == 'surface':
                        return image_surface

                    surface_list.append(image_surface)
                    break  # breaks  from checking allowed file types
        # if return_type == 'list'
        return surface_list


# imports level csvs and returns workable list of lists
def import_csv_layout(path):
    terrain_map = []
    with open(path) as map:
        level = reader(map, delimiter=',')
        for row in level:
            terrain_map.append(list(row))
        return terrain_map


# cuts up tile sheets returning list with provided path and the size each tile is in the image.
# tiles must have no spacing and consistent dimensions
def import_cut_graphics(path, art_tile_size):
    surface = pygame.image.load(path).convert_alpha()
    tile_num_x = int(surface.get_size()[0] / art_tile_size)  # works out how many tiles are on the x and y based on passed value
    tile_num_y = int(surface.get_size()[1] / art_tile_size)
    surface = pygame.transform.scale(surface, (tile_size * tile_num_x, tile_size * tile_num_y)) # expands tileset to game resolution based on dimensions in tiles

    cut_tiles = []
    # keeps track of different segments of tilesheet
    for row in range(tile_num_y):
        for col in range(tile_num_x):
            # x and y refer to x and y tile grid on the imported tileset not the game (top left of tile being sliced)
            x = col * tile_size
            y = row * tile_size
            # makes new surface and places segment of sheet (tile) on new surface
            new_surface = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)  # SRCALPHA allows opacity and invis pixels
            # blit args: thing to be placed, position (the top left corner of the surface), rectangle (mask)
            new_surface.blit(surface, (0, 0), pygame.Rect(x, y, tile_size, tile_size))
            #new_surface.set_alpha(100)  <-- changes alpha value for entire surface
            cut_tiles.append(new_surface)

    return cut_tiles


def scale_hitbox(hitbox_image, scaleup):
    hitbox_width = hitbox_image.get_width()
    hitbox_height = hitbox_image.get_height()
    return pygame.transform.scale(hitbox_image, (hitbox_width * scaleup, hitbox_height * scaleup))