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
    'slash': [(2+56*i, 186, 54, 35) for i in range(5)],  # This is actually the shovel attack animation
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
        
        self.max_health = 8
        self.health = self.max_health
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.invulnerable_duration = 1.0

        # Attack hitbox properties
        self.attacking = False
        self.attack_type = None  # Can be 'slash' (shovel attack) or 'down_thrust'
        self.attack_hitbox = None
        self.attack_damage = 1
        
        # Debug flag - ENSURE THIS IS TRUE
        self.debug_mode = True

        self.set_sprite('idle')

        self.slash_sound = pg_mixer.Sound('ShovelKnight/assets/sounds/knight_slash.ogg')  # This is actually the shovel attack sound
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
                    self.attack_type = 'down_thrust'
                    self.set_sprite('down_thrust')
            if event.key == K_SPACE:
                if self.debug_mode:
                    print("Space pressed - Starting shovel attack")
                    
                # Reset any existing attack state to ensure clean start
                if self.attacking:
                    self.attacking = False
                    self.attack_hitbox = None
                    self.attack_type = None
                    
                self.slash_sound.play()
                self.set_animation('slash')
                self.attacking = True
                self.attack_type = 'slash'  # The slash animation is actually the shovel attack
                
                # Reset attack timer for time-based cleanup
                self.attack_timer = 0.5  # Match animation duration
                
                # Create attack hitbox immediately when attacking begins
                self.update_attack_hitbox()
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
        # Debug info about enemies
        if self.debug_mode:
            print(f"Checking enemy collisions, enemies count: {len(enemies)}")
            for i, enemy in enumerate(enemies):
                print(f"Enemy {i}: Position: {enemy.rect.topleft}, Dead: {enemy.dead}")
        
        # Early return if player is dead
        if self.dead:
            return False
            
        player_took_damage = False
        
        # Check for down attack damage
        if self.down_attack and self.vy > 0:
            for enemy in enemies:
                if not getattr(enemy, 'dead', False) and self.rect.colliderect(enemy.rect) and self.rect.bottom < enemy.rect.centery:
                    print(f"Down thrust hit enemy!")
                    enemy.take_damage(self.attack_damage)
                    self.vy = -20
        
        # CRUCIAL: Check for shovel attack damage
        if self.attacking and self.animation:
            if self.debug_mode:
                print(f"Slash animation active: frame {self.animation.frame}")
            
            # Create attack hitbox
            self.update_attack_hitbox()
            
            # Check collision with all enemies
            for enemy in enemies:
                if not getattr(enemy, 'dead', False) and self.attack_hitbox and self.attack_hitbox.colliderect(enemy.rect):
                    print(f"SHOVEL HIT ENEMY!")
                    enemy.take_damage(self.attack_damage)  # Apply damage to the enemy
        
        # Check if player gets hit by enemies
        if not self.invulnerable:
            for enemy in enemies:
                if not getattr(enemy, 'dead', False) and self.rect.colliderect(enemy.rect):
                    self.take_damage(1)
                    player_took_damage = True
                    break
        
        return player_took_damage
    
    def update_attack_hitbox(self):
        """Update the attack hitbox based on player direction and current sprite"""
        # Create hitbox during slash animation, no matter which frame
        if self.attacking and self.attack_type == 'slash':
            # Make hitbox larger for better hit detection
            hitbox_width = 40
            hitbox_height = 30
            
            
            if self.attack_timer > 0:
                if self.flip:  # Facing left
                    hitbox_x = self.rect.left - hitbox_width
                    hitbox_y = self.rect.top + 5
                else:  # Facing right
                    hitbox_x = self.rect.right
                    hitbox_y = self.rect.top + 5
                        
                self.attack_hitbox = Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
                self.attack_timer -= 1/FPS
            else:
                self.attack_hitbox = None

            
            if self.debug_mode:
                print(f"Attack hitbox created: {self.attack_hitbox}")
        elif self.down_attack:
            # Create hitbox for down attack
            hitbox_width = 30
            hitbox_height = 20
            hitbox_x = self.rect.centerx - hitbox_width // 2
            hitbox_y = self.rect.bottom
            
            self.attack_hitbox = Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
            
            if self.debug_mode:
                print(f"Down attack hitbox: {self.attack_hitbox}")
        else:
            self.attack_hitbox = None
    
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
        
        # Store previous animation state to detect when animation completes
        if hasattr(self, 'previous_frame') and self.animation:
            previous_frame = self.previous_frame
        else:
            previous_frame = -1
            
        # Store current frame for next update
        self.previous_frame = self.animation.frame if self.animation else -1
        
        # Check if slash animation is done (reached the last frame)
        if self.attacking and self.animation and self.animation.frame == 'slash':
            # Get total frames in the slash animation
            total_frames = len(sprites.animation_sprites('slash'))
            
            if self.debug_mode:
                print(f"Animation frame: {self.animation.frame}, Total frames: {total_frames}")
                
            # If we're at the last frame or animation changed/disappeared
            if self.animation.frame >= total_frames - 1:
                if self.debug_mode:
                    print("Slash animation complete!")
                self.attacking = False
                self.attack_hitbox = None
                self.attack_type = None
        
        # Update attack hitbox only when actively attacking
        if self.attacking or self.down_attack:
            self.update_attack_hitbox()
        else:
            # Ensure hitbox is removed when not attacking
            self.attack_hitbox = None
        
        if self.invulnerable:
            self.invulnerable_timer -= 1/FPS
            if self.invulnerable_timer <= 0:
                self.invulnerable = False
                self.invulnerable_timer = 0
                
    def draw(self, surface, offset=(0, 0)):
        # For animation/sprite rendering
        super().draw(surface, offset)
        
        # Always draw the attack hitbox when it exists and debug mode is on
        if self.attack_hitbox and self.debug_mode:
            # Make sure to properly offset the hitbox for camera position
            debug_hitbox = Rect(
                self.attack_hitbox.x - offset[0],
                self.attack_hitbox.y - offset[1],
                self.attack_hitbox.width,
                self.attack_hitbox.height
            )
            # Draw a more visible hitbox
            pg.draw.rect(surface, (255, 0, 0), debug_hitbox, 2)
            
            # Adding fill to make it more visible
            hitbox_fill = debug_hitbox.copy()
            hitbox_fill_color = (255, 0, 0, 128)  # Red with transparency
            hitbox_surface = pg.Surface((hitbox_fill.width, hitbox_fill.height), pg.SRCALPHA)
            hitbox_surface.fill((255, 0, 0, 64))  # Semi-transparent red
            surface.blit(hitbox_surface, (hitbox_fill.x, hitbox_fill.y))