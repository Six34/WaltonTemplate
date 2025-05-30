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
    'climb': [(2, 262, 25, 27), (29, 262, 25, 27)], 
    'hurt': (2, 258, 33, 32),
})

animations = {
    'walk': Animation(sprites.animation_sprites('walk'), duration=0.5, repeat=True),
    'slash': Animation(sprites.animation_sprites('slash'), duration=0.5, repeat=False, flip_offset=(20, 0)),
    'climb': Animation(sprites.animation_sprites('climb'), duration=0.4, repeat=True),  
}


class Knight(Entity):
    def __init__(self, rect=Rect(0, 0, 0, 0)):
        super().__init__(rect, sprites=sprites, animations=animations)

        self.grounded = True
        self.falling = False
        self.down_attack = False
        self.laddering = False
        
        self.dead = False
        
        self.max_health = 8
        self.health = self.max_health
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.invulnerable_duration = 1.0

        # Attack hitbox properties
        self.attacking = False
        self.attack_type = None 
        self.attack_hitbox = None
        self.attack_damage = 1
        
        self.original_rect_width = rect.width if rect.width > 0 else 32
        self.ladder_rect_width = 10
        
        # Debug flag - ENSURE THIS IS TRUE
        self.debug_mode = False

        self.set_sprite('idle')

        self.slash_sound = pg_mixer.Sound('ShovelKnight/assets/sounds/knight_slash.ogg')  
        self.jump_sound = pg_mixer.Sound('ShovelKnight/assets/sounds/knight_jump.ogg')
        self.land_sound = pg_mixer.Sound('ShovelKnight/assets/sounds/knight_land.ogg')
        self.slash_sound.set_volume(0.1)
        self.jump_sound.set_volume(0.1)
        self.land_sound.set_volume(0.1)

    def on_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_a:
                self.flip = True
                print(f"Moving left, flip = {self.flip}")  # Add this line
                self.vx = -10
                if self.grounded:
                    self.set_animation('walk')
            if event.key == K_d:
                self.flip = False
                print(f"Moving right, flip = {self.flip}")  # Add this line
                self.vx = 10
                if self.grounded:
                    self.set_animation('walk')
                    
            # Handle ladder movement
            if self.laddering:
                if event.key == K_w:
                    self.vy = -10
                    self.set_animation('climb')
                if event.key == K_s:
                    self.vy = 10
                    self.set_animation('climb')
                if event.key == K_SPACE:
                    self.jump_sound.play()
                    self.vy = -40
                    self.grounded = False
                    self.exit_ladder_mode()  # Use helper method
                    self.animation = None
                    self.set_sprite('jump')
                    if self.debug_mode:
                        print("Jumped off ladder")

            elif event.key == K_SPACE and self.grounded:
                self.jump_sound.play()
                self.vy = -40
                self.grounded = False
                self.animation = None
                self.set_sprite('jump')
                if self.debug_mode:
                    print("Normal jump")
                            
            if event.key == K_s:
                if not self.grounded:
                    self.down_attack = True
                    self.attack_type = 'down_thrust'
                    self.set_sprite('down_thrust')
            if event.key == K_f:
                if self.debug_mode:
                    print("Space pressed - Starting shovel attack")
                    
                if self.attacking:
                    self.attacking = False
                    self.attack_hitbox = None
                    self.attack_type = None
                    
                self.slash_sound.play()
                self.set_animation('slash')
                self.attacking = True
                self.attack_type = 'slash'  
            
                self.attack_timer = 0.5  
            
                self.update_attack_hitbox()
                
        if event.type == KEYUP:
            if event.key in (K_a, K_d):
                self.animation = None
                self.vx = 0
                if self.grounded:
                    self.set_sprite('idle')
            
            # Stop vertical movement when keys are released on ladder
            if self.laddering and event.key in (K_w, K_s):
                self.vy = 0
                self.set_animation('climb')


    def find_nearby_ladder(self, tiles, max_distance=20):  # Reduced from 40 to 20
        for tile in tiles:
            if tile.type == 'ladder':
                # Check horizontal distance to ladder center
                ladder_center_x = tile.rect.centerx
                player_center_x = self.rect.centerx
                horizontal_distance = abs(ladder_center_x - player_center_x)
                
                # Check if player overlaps vertically with ladder
                player_bottom = self.rect.bottom
                player_top = self.rect.top
                ladder_bottom = tile.rect.bottom
                ladder_top = tile.rect.top
                
                # More strict vertical overlap check
                vertical_overlap = (player_bottom >= ladder_top and player_top <= ladder_bottom)
                
                if horizontal_distance <= max_distance and vertical_overlap:
                    return tile
        return None

    def move(self, tiles):
        self.collision = {'left': False, 'right': False,
                    'top': False, 'bottom': False}
    
        # Check for UP key press to grab ladder
        keys = pg.key.get_pressed()
        if keys[K_w] and not self.laddering:
            nearby_ladder = self.find_nearby_ladder(tiles, max_distance=15)
            if nearby_ladder:
                if self.debug_mode:
                    print("Grabbing ladder!")
                # Snap to ladder center and make hitbox smaller
                self.rect.centerx = nearby_ladder.rect.centerx
                self.rect.width = self.ladder_rect_width
                self.laddering = True
                self.grounded = False
                self.vy = 0
                self.set_animation('climb')
        
        # Check if we should exit ladder mode (when not pressing UP/DOWN and moving horizontally)
        if self.laddering and (keys[K_a] or keys[K_d]) and not (keys[K_w] or keys[K_s]):
            current_ladder = None
            for tile in tiles:
                if tile.type == 'ladder' and self.rect.colliderect(tile.rect):
                    current_ladder = tile
                    break
            
            # If we're moving away from the ladder horizontally, exit ladder mode
            if not current_ladder:
                self.exit_ladder_mode()
        
        # Handle horizontal movement
        if self.vx != 0:
            self.rect.x += self.vx*dt
            hit_list = self.collisions(tiles)

            for tile in hit_list:
                if tile.type not in ('ladder', 'win_trigger'):
                    if self.vx > 0:
                        self.rect.right = tile.rect.left
                        self.collision['right'] = True
                    elif self.vx < 0:
                        self.rect.left = tile.rect.right
                        self.collision['left'] = True
                    
                    if self.debug_mode:
                        print(f"Horizontal collision with {tile.type}")
                elif tile.type == 'win_trigger' and self.debug_mode:
                    print(f"Win trigger detected at {tile.rect}")

        # Handle vertical movement
        if self.laddering:
            # On ladder: no gravity, just move based on input
            self.rect.y += self.vy*dt
            
            self.center_on_ladder(tiles)
            
            # Check if we've left the ladder bounds
            current_ladder = None
            for tile in tiles:
                if tile.type == 'ladder' and self.rect.colliderect(tile.rect):
                    current_ladder = tile
                    break
            
            if not current_ladder:
                if self.debug_mode:
                    print("Left ladder bounds")
                self.exit_ladder_mode()
                if self.vy < 0:
                    self.grounded = True
                    self.vy = 0
                    self.set_sprite('idle')
                    
        else:
            # Normal movement: apply gravity
            self.rect.y += self.vy*dt
            self.vy += 0.5*g*dt**2
            
            # Check if we should transition to falling state
            if self.vy > 9 and not self.grounded:
                if not self.down_attack:
                    self.animation = None
                    self.set_sprite('fall')

        # Check vertical collisions (only for non-ladder tiles)
        hit_list = self.collisions(tiles)
        
        # Process standard tile collisions
        for tile in hit_list:
            # Don't block movement on win triggers or ladders
            if tile.type != 'ladder' and tile.type != 'win_trigger':
                if self.vy > 0:
                    self.rect.bottom = tile.rect.top
                    self.collision['bottom'] = True
                elif self.vy < 0:
                    self.rect.top = tile.rect.bottom
                    self.collision['top'] = True
            elif tile.type == 'win_trigger' and self.debug_mode:
                print(f"Player rect: {self.rect}, Win trigger: {tile.rect}")
        
        # Handle transition to falling state
        if not self.falling and self.vy > 0 and not self.grounded and not self.laddering:
            if not self.down_attack:
                self.set_sprite('fall')
            self.falling = True
        
        # Stop vertical motion when hitting ground
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
            
            if self.laddering:
                self.exit_ladder_mode()

        if self.collision['top'] == True:
            self.vy = 0
                
    def exit_ladder_mode(self):
        if self.laddering:
            self.laddering = False
            self.rect.width = self.original_rect_width  
            if self.debug_mode:
                print("Exited ladder mode, hitbox restored")

    def check_hazard_collisions(self, spikes):      
        if not self.invulnerable:                   
            spike_hit = self.collisions(spikes)     
            if spike_hit:
                self.take_damage(100)
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
                
    def center_on_ladder(self, tiles):
        if self.laddering:
            current_ladder = None
            for tile in tiles:
                if tile.type == 'ladder' and self.rect.colliderect(tile.rect):
                    current_ladder = tile
                    break
            
            if current_ladder:
                # Center the player's hitbox on the ladder
                self.rect.centerx = current_ladder.rect.centerx
                if self.debug_mode:
                    print(f"Centered on ladder: player centerx={self.rect.centerx}, ladder centerx={current_ladder.rect.centerx}")
                    
    def draw(self, surface, offset=(0, 0)):
        sprite_x = self.rect.x - offset[0]
        sprite_y = self.rect.y - offset[1]

        # If on ladder, adjust sprite position to center it with the narrow hitbox
        if self.laddering:
            # Calculate the difference between original width and ladder width
            width_difference = self.original_rect_width - self.ladder_rect_width
            # Offset the sprite to center it on the narrow hitbox
            sprite_x -= width_difference // 2
        
        # Get the current sprite (already flipped by parent Entity.set_sprite if needed)
        sprite = self.sprite
        if sprite:
            # REMOVED: Don't flip here - parent class already handles it in set_sprite()
            # The Entity.set_sprite() method already applies the flip transformation
            
            # Apply invulnerability flashing effect
            if self.invulnerable:
                # Create flashing effect by modulating alpha
                flash_rate = 10  # flashes per second
                flash_time = self.invulnerable_timer * flash_rate
                if int(flash_time) % 2:  # Flash on/off
                    # Create a copy of the sprite with reduced alpha
                    temp_sprite = sprite.copy()
                    temp_sprite.set_alpha(128)  # Semi-transparent
                    surface.blit(temp_sprite, (sprite_x, sprite_y))
                else:
                    surface.blit(sprite, (sprite_x, sprite_y))
            else:
                surface.blit(sprite, (sprite_x, sprite_y))

        # Debug visualization (attack hitbox)
        if self.attack_hitbox and self.debug_mode:
            debug_hitbox = Rect(
                self.attack_hitbox.x - offset[0],
                self.attack_hitbox.y - offset[1],
                self.attack_hitbox.width,
                self.attack_hitbox.height
            )
            
            pg.draw.rect(surface, (255, 0, 0), debug_hitbox, 2)
            hitbox_fill = debug_hitbox.copy()
            hitbox_surface = pg.Surface((hitbox_fill.width, hitbox_fill.height), pg.SRCALPHA)
            hitbox_surface.fill((255, 0, 0, 64))  
            surface.blit(hitbox_surface, (hitbox_fill.x, hitbox_fill.y))
            
        # Debug visualization (character hitbox)
        if self.debug_mode:
            char_hitbox = Rect(
                self.rect.x - offset[0],
                self.rect.y - offset[1],
                self.rect.width,
                self.rect.height
            )
            hitbox_color = (0, 255, 255) if self.laddering else (0, 255, 0)  
            pg.draw.rect(surface, hitbox_color, char_hitbox, 1)
            
            # Status text with flip state for debugging
            ladder_status = f"On Ladder (W:{self.rect.width})" if self.laddering else f"Normal (W:{self.rect.width})"
            flip_status = f" | Flip: {self.flip}"
            status_text = ladder_status + flip_status
            status_color = (0, 255, 0) if self.laddering else (255, 255, 255)
            status_display = pg.font.SysFont('Arial', 12).render(status_text, True, status_color)
            surface.blit(status_display, (self.rect.x - offset[0], self.rect.y - offset[1] - 20))

    def update_sprite_flip(self):
        """Call this whenever you change the flip state to refresh the sprite"""
        if self.animation:
            self.set_sprite()  
        else:
            self.set_sprite('idle')  