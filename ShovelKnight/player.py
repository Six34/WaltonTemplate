from engine import *
from engine.entity import Entity
import engine.game

from config import FPS

sprites = SpriteSheet('ShovelKnight/assets/images/knight.png', {
    'idle': (2, 2, 34, 32),
    'down_thrust': (2, 223, 24, 36),
    'walk': [(2+42*i, 77, 40, 35) for i in range(5)],
    'jump': (2, 114, 31, 34),
    'fall': (2, 150, 33, 34),
    'slash': [(2+56*i, 186, 54, 35) for i in range(5)],
    # 'shine': [(2+36*i, 323, 34, 32) for i in range(3)],
    'hurt': (2, 258, 33, 32),
})

animations = {
    'walk': Animation(sprites.animation_sprites('walk'), duration=0.5, repeat=True),
    'slash': Animation(sprites.animation_sprites('slash'), duration=0.5, repeat=False, flip_offset=(20, 0)),
}


class Knight(Entity):
    def __init__(self, rect=Rect(0, 0, 0, 0)):
        super().__init__(rect, sprites=sprites, animations=animations)

        self.grounded = True
        self.falling = False
        self.down_attack = False
        
        self.dead = False
        
        self.max_health = 1
        self.health = self.max_health
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.invulnerable_duration = 1.0

        self.set_sprite('idle')

        self.slash_sound = pg_mixer.Sound('ShovelKnight/assets/sounds/knight_slash.ogg')
        self.jump_sound = pg_mixer.Sound('ShovelKnight/assets/sounds/knight_jump.ogg')
        self.land_sound = pg_mixer.Sound('ShovelKnight/assets/sounds/knight_land.ogg')

    def on_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_LEFT:
                self.flip = True
                self.vx = -10
                if self.grounded:
                    self.set_animation('walk')
            if event.key == K_RIGHT:
                self.flip = False
                self.vx = 10
                if self.grounded:
                    self.set_animation('walk')
            if event.key == K_UP:
                if self.grounded:
                    self.jump_sound.play()
                    self.vy = -40
                    self.grounded = False
                    self.animation = None
                    self.set_sprite('jump')
            if event.key == K_DOWN:
                if not self.grounded:
                    self.down_attack = True
                    self.set_sprite('down_thrust')
            if event.key == K_SPACE:
                self.slash_sound.play()
                self.set_animation('slash')
        if event.type == KEYUP:
            if event.key in (K_LEFT, K_RIGHT):
                self.animation = None
                self.vx = 0
                if self.grounded:
                    self.set_sprite('idle')

    def move(self, tiles):
        self.collision = {'left': False, 'right': False,
                          'top': False, 'bottom': False}

        if self.vx != 0:
            self.rect.x += self.vx*dt
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

        self.rect.y += self.vy*dt
        self.vy += 0.5*g*dt**2

        if self.vy > 9:
            if self.grounded:
                self.grounded = False
                self.animation = None
                self.set_sprite('fall')

        hit_list = self.collisions(tiles)

        for tile in hit_list:
            if self.vy > 0:
                if tile.type != 'ladder':
                    self.rect.bottom = tile.rect.top
                    self.collision['bottom'] = True
            elif self.vy < 0:
                if tile.type != 'ladder':
                    self.rect.top = tile.rect.bottom
                    self.collision['top'] = True

        if not self.falling and self.vy > 0 and not self.grounded:
            if not self.down_attack:
                self.set_sprite('fall')
            self.falling = True

        if self.collision['bottom'] == True:
            self.vy = 0

            if not self.grounded:
                self.land_sound.play()

                if self.vx != 0:
                    self.set_animation('walk')
                else:
                    self.set_sprite('idle')

            self.grounded = True
            self.falling = False
            self.down_attack = False

        if self.collision['top'] == True:
            self.vy = 0
            
    def check_hazard_collisions(self, spikes):      # checking spikes / other hazards function
        if not self.invulnerable:                   # checks if we can take damage 
            spike_hit = self.collisions(spikes)     
            if spike_hit:
                self.take_damage(1)
                return True
        return False
    
    def check_enemy_collisions(self, enemies):
        if not self.invulnerable:
            if self.down_attack and self.vy > 0:
                for enemy in enemies:
                    if self.rect.colliderect(enemy.rect) and self.rect.bottom < enemy.rect.centery:
                        enemy.take_damage(1)
                        self.vy = -20
                        return False # no damage taking
                    
            enemy_hit = False
            for enemy in enemies:
                if self.rect.colliderect(enemy.rect):
                    enemy_hit = True
                    break
            
            if enemy_hit:
                self.take_damage(1)
                return True
        
        return False
    
    def take_damage(self, damage):
        if not self.invulnerable:
            self.health -= damage
            self.health = max(0, self.health)
            
            self.invulnerable = True
            self.invulnerable_timer = self.invulnerable_duration
            
            self.animation = None
            self.set_sprite('hurt')
            
            # could add a damage sound
            
            knockback_direction = -1 if self.flip else 1 # knocks us back in the opposite direction as the damage we have taken
            self.vx = knockback_direction * 15
            self.vy = -15
            
            if self.health <= 0:
                self.die()
                
    def die(self):
        self.dead = True
        

    def draw_health_bar(self, surface, x, y, width=100, height=10):
        background_rect = Rect(x, y, width, height)
        pg.draw.rect(surface, (128, 128, 128), background_rect)
        
        health_width = int ((self.health / self.max_health) * width)
        health_rect = Rect((x, y, health_width, height))
        
        if self.health > self.max_health * 0.7: # change healthbar color based on current health
            color = (0, 255, 0) 
        elif self.health > self.max_health * 0.3:
            color = (255, 255, 0)
        else:
            color = (255, 0, 0)
            
        pg.draw.rect(surface, color, health_rect)
        
        pg.draw.rect(surface, (0, 0, 0), background_rect, 2)
        
    def update(self, tiles):
        super().update(tiles)
        
        if self.invulnerable:
            self.invulnerable_timer -= 1/FPS
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                self.invulnerable_timer = 0
        