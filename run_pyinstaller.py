import PyInstaller.__main__

PyInstaller.__main__.run([
    'code/main.py',
    'code/camera.py',
    'code/game_data.py',
    'code/player.py',
    'code/room.py',
    'code/spawn.py',
    'code/support.py',
    'code/tiles.py',
    'code/trigger.py',
    'code/pytmx/pytmx.py',
    'code/pytmx/util_pygame.py',
    '--onefile',
    '--noconsole',
    '--debug=imports'
    #'--add-binary=rooms:rooms'
    #'--add-data='
])