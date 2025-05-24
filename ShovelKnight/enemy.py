from engine import *
from engine.entity import Entity

sprites = SpriteSheet('ShovelKnight/assets/images/beeto.png', {
    'idle': (2, 2, 26, 16),
    'walk': [(2+28*i, 2, 26, 16) for i in range(4)],
    'flip': (2, 20, 26, 16),
})

animations = {
    'walk': Animation(sprites.animation_sprites('walk'), 1, repeat=True),
}


class Beeto(Entity):
    def __init__(self, rect=(0, 0, 0, 0)):
        super().__init__(rect, sprites=sprites, animations=animations)
        self.set_sprite('idle')
        self.set_animation('walk')
        self.vx = 5
        
        self.health = 1
        self.dead = False
        self.debug_mode = True

    def move(self, tiles):
        if self.dead:
            return
        
        self.collision = {'left': False, 'right': False,
                          'top': False, 'bottom': False}

        self.rect.x += self.vx * dt

        hit_list = self.collisions(tiles)

        for tile in hit_list:
            if self.vx > 0:
                if tile.type != 'ladder':
                    self.rect.right = tile.rect.left
                    self.collision['right'] = True
            elif self.vx < 0:
                if tile.type != 'ladder':
                    self.rect.left = tile.rect.right
                    self.collision['left'] = True

        if self.collision['right'] or self.collision['left'] or self.rect.x < 0:
            self.vx *= -1
            self.flip = not self.flip
            
        self.rect.y += self.vy * dt
        self.vy += 0.5 * g * dt**2
        
        hit_list = self.collisions(tiles)
        
        for tile in hit_list:
            if self.vy > 0:
                if tile.type != 'ladder':
                    self.rect.bottom = tile.rect.top
                    self.collision['bottom'] = True
                    self.vy = 0
            elif self.vy < 0:
                if tile.type != 'ladder':
                    self.rect.top = tile.rect.bottom
                    self.collision['top'] = True
                    self.vy = 0
                    
    def die(self):
        if self.debug_mode:
            print("Enemy died!")
        self.dead = True
        # Remove enemy from level.entities to properly despawn
        if hasattr(self, 'level') and hasattr(self.level, 'entities'):
            if self in self.level.entities:
                self.level.entities.remove(self)
                
    def take_damage(self, damage):
        if self.dead:
            return
            
        print(f"Enemy taking {damage} damage! Current health: {self.health}")
        self.health -= damage
        if self.health <= 0:
            self.die()
        return True

    def on_event(self, event):
        pass