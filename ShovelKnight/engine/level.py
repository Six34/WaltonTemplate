from engine import pg, Surface, SpriteSheet, Rect
import os

from player import Knight
from enemy import Beeto

# Get the directory containing this file
base_path = os.path.dirname(__file__)

# Create paths for both images
plains_path = os.path.join(base_path, '../assets/images/plains.png')
door_path = os.path.join(base_path, '../assets/images/DOOR.png')  # Assuming DOOR.png is in the same directory

# Try to load door image with error handling
try:
    door_image_raw = pg.image.load(door_path)
except pg.error:
    # If DOOR.png is in a different location, try the parent directory
    door_path = os.path.join(base_path, '../DOOR.png')
    try:
        door_image_raw = pg.image.load(door_path)
    except pg.error:
        print(f"Warning: Could not load door image from {door_path}")
        # Create a placeholder surface if door image can't be loaded
        door_image_raw = pg.Surface((16, 16))
        door_image_raw.fill((139, 69, 19))  # Brown color as placeholder

sprites = SpriteSheet(plains_path, {
    'bg': (0, 20, 150, 90),
    'g0': (144, 224, 16, 16),
    'g1': (160, 224, 16, 16),
    'g2': (192, 224, 16, 16),
    'g3': (96, 224, 16, 16),
    'g4': (304, 240, 16, 16),
    'g5': (368, 240, 16, 16),
    'g6': (352, 176, 16, 16),
    'ld': (80, 224, 16, 16),
    'sp': (352, 240, 16, 16),
})

sprite_mapping = {
    '[': sprites.sprite('g0'),
    '=': sprites.sprite('g1'),
    ']': sprites.sprite('g2'),
    '|': sprites.sprite('g3'),
    '.': sprites.sprite('g6'),
    'M': sprites.sprite('sp'),
    'H': sprites.sprite('ld'),
    'W': door_image_raw,  
}


class Tile:
    def __init__(self, rect, type):
        self.rect = rect
        self.type = type


class Level:
    def __init__(self, data):
        self.tiles = []
        self.entities = []
        self.win_triggers = []
        self.spikes = []  
        
        # Extract level number from filename (e.g., level_1.txt → 1)
        try:
            self.level_number = int(data.split('level_')[1].split('.')[0])
        except:
            self.level_number = 1  # Default to level 1 if parsing fails
        
        with open(data) as file:
            self.array = file.read().split('\n')
            self.w = len(self.array[0])
            self.h = len(self.array)
        self.map = Surface((self.w*16, self.h*16), pg.SRCALPHA)

        self.build_map()

    def build_map(self):
        for i in range(self.h):
            for j in range(self.w):
                k = self.array[i][j]

                if k != ' ':
                    if k not in ('P', 'B'):
                        # Special handling for door image scaling
                        if k == 'W':
                            # Scale the door image to fit 16x16 tile if needed
                            scaled_door = pg.transform.scale(door_image_raw, (16, 16))
                            self.map.blit(scaled_door, (j*16, i*16))
                        else:
                            self.map.blit(sprite_mapping[k], (j*16, i*16))

                        if k == 'H':
                            _type = 'ladder'
                            self.tiles.append(Tile(Rect(j*16, i*16, 16, 16), _type))
                        elif k == 'M':
                            _type = 'spike'
                            spike_tile = Tile(Rect(j*16, i*16, 16, 16), _type)
                            self.spikes.append(spike_tile)
                        elif k == 'W':
                            _type = 'win_trigger'
                            win_tile = Tile(Rect(j*16, i*16, 16, 16), _type)
                            self.win_triggers.append(win_tile)
                            self.tiles.append(win_tile)
                        else:
                            _type = 'block'
                            self.tiles.append(Tile(Rect(j*16, i*16, 16, 16), _type))
                    elif k == 'P':
                        self.entities.append(Knight(Rect(j*16, i*16-15, 34, 31)))
                    elif k == 'B':
                        self.entities.append(Beeto(Rect(j*16, i*16+1, 26, 15)))

    def check_win_condition(self, player):
        if not player:
            return False
            
        for trigger in self.win_triggers:
            if player.rect.colliderect(trigger.rect):
                return True
                
        return False