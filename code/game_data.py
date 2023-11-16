project_name = "platformer_test"

tile_size = 16
screen_width = tile_size * 30
screen_height = tile_size * 18
scaling_factor = 2  # how much the screen is scaled up before bliting on display

controller_map = {'square': 0, 'X': 1, 'circle': 2, 'triangle': 3, 'L1': 4, 'R1': 5, 'L2': 6, 'R2': 7, 'share': 8,
                  'options': 9, 'left_analog_press': 10, 'right_analog_press': 11, 'PS': 12, 'touchpad': 13,
                  'left_analog_x': 0,  'left_analog_y': 1, 'right_analog_x': 2,  'right_analog_y': 5}

fonts = {'small': '../assets/fonts/small_font.png',
         'large': '../assets/fonts/large_font.png'}

room_path = '../rooms/'