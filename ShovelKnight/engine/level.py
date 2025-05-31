from engine import pg, Surface, SpriteSheet, Rect
import os

from player import Knight
from enemy import Beeto

# Get the directory containing this file
base_path = os.path.dirname(__file__)

# Create paths for both images
plains_path = os.path.join(base_path, '../assets/images/plains.png')
door_path = os.path.join(base_path, '../assets/images/DOOR.png')

# Try to load door image with error handling
try:
    door_image_raw = pg.image.load(door_path)
    print(f"Original door size: {door_image_raw.get_size()}")
except pg.error:
    door_path = os.path.join(base_path, '../DOOR.png')
    try:
        door_image_raw = pg.image.load(door_path)
        print(f"Original door size: {door_image_raw.get_size()}")
    except pg.error:
        print(f"Warning: Could not load door image from {door_path}")
        door_image_raw = pg.Surface((16, 32))
        door_image_raw.fill((139, 69, 19))

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

# Create a proper 16x32 door sprite (1 tile wide, 2 tiles tall)
door_sprite = pg.transform.smoothscale(door_image_raw, (16, 32))
print(f"Door sprite scaled to: {door_sprite.get_size()}")

sprite_mapping = {
    '[': sprites.sprite('g0'),
    '=': sprites.sprite('g1'),
    ']': sprites.sprite('g2'),
    '|': sprites.sprite('g3'),
    '.': sprites.sprite('g6'),
    'M': sprites.sprite('sp'),
    'H': sprites.sprite('ld'),
    'W': door_sprite,
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
        
        try:
            self.level_number = int(data.split('level_')[1].split('.')[0])
        except:
            self.level_number = 1
        
        with open(data) as file:
            # Read all lines and normalize them
            raw_lines = file.read().split('\n')
            
            # Remove trailing empty lines
            while raw_lines and not raw_lines[-1].strip():
                raw_lines.pop()
            
            # If no lines remain, create a minimal level
            if not raw_lines:
                raw_lines = ['P W']
            
            # Find the maximum width across all lines
            max_width = max(len(line) for line in raw_lines) if raw_lines else 1
            
            # Pad all lines to the same width with spaces
            self.array = []
            for line in raw_lines:
                padded_line = line.ljust(max_width)  # Pad with spaces to max_width
                self.array.append(padded_line)
            
            self.w = max_width
            self.h = len(self.array)
            
        print(f"Level dimensions: {self.w}x{self.h}")
        self.map = Surface((self.w*16, self.h*16), pg.SRCALPHA)

        self.build_map()

    def build_map(self):
        for i in range(self.h):
            for j in range(self.w):
                # Safe character access - default to space if index is out of bounds
                if j < len(self.array[i]):
                    k = self.array[i][j]
                else:
                    k = ' '

                if k != ' ':
                    if k not in ('P', 'B'):
                        # Handle door specially - it's 2 tiles tall
                        if k == 'W':
                            # Draw the door starting from current position, extending upward
                            # The door bottom should align with the tile where 'W' is placed
                            door_x = j * 16
                            door_y = i * 16 - 16  # Move up by 16 pixels so door spans this tile and the one above
                            
                            # Make sure we don't draw above the map bounds
                            if door_y >= 0:
                                self.map.blit(sprite_mapping[k], (door_x, door_y))
                            else:
                                # If we can't fit the full door, just draw it starting from the current position
                                self.map.blit(sprite_mapping[k], (door_x, i * 16))
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
                            # Create win trigger for both tiles that the door occupies
                            win_tile_bottom = Tile(Rect(j*16, i*16, 16, 16), _type)
                            self.win_triggers.append(win_tile_bottom)
                            # DON'T add door tiles to self.tiles - they shouldn't show collision debug
                            
                            # Also create trigger for the tile above (if it exists)
                            if i > 0:
                                win_tile_top = Tile(Rect(j*16, (i-1)*16, 16, 16), _type)
                                self.win_triggers.append(win_tile_top)
                                # DON'T add this to self.tiles either
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