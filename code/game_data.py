tile_size = 16  # 40 or 64 or 80 at 64 tilesize with 16 resolution, 4 real px per art px
screen_width = tile_size * 29
screen_height = tile_size * 18

controller_map = {'square': 0, 'X': 1, 'circle': 2, 'triangle': 3, 'L1': 4, 'R1': 5, 'L2': 6, 'R2': 7, 'share': 8,
                  'options': 9, 'left_analog_press': 10, 'right_analog_press': 11, 'PS': 12, 'touchpad': 13,
                  'left_analog_x': 0,  'left_analog_y': 1}

rooms = {'room_0': '../rooms/test_csvs.tmx',
         'room_1': '../rooms/level_1.tmx'}
