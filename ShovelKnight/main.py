from config import *
from engine import *
import sys
import os
from pygame import Rect

from engine.level import sprites

from camera import Camera

from player import Knight

HALF_WINDOW_SIZE = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GOLD = (255, 215, 0)


class ShovelKnight(Game):
    def init(self):
        
        self.game_state = "running"
        self.current_level = 1
        self.max_level = self.find_max_level()
        
        self.reset_game()
        
        # Setup fonts
        self.font = pg.font.SysFont('Arial', 36)
        self.small_font = pg.font.SysFont('Arial', 24)
        
        # Setup music
        pg_mixer.music.set_volume(0.05)
        pg_mixer.music.load('ShovelKnight/assets/sounds/music.ogg')
        pg_mixer.music.play(loops=-1)
        
        # Load sound effects
        self.victory_sound = pg_mixer.Sound('ShovelKnight/assets/sounds/knight_land.ogg')  # Use existing sound for victory
        self.next_level_sound = pg_mixer.Sound('ShovelKnight/assets/sounds/knight_jump.ogg')  # Use existing sound for level transition

    def find_max_level(self): # Finding what the highest level there is by going in the files
        max_level = 1
        levels_dir = 'ShovelKnight/assets/levels'
        
        if os.path.exists(levels_dir):
            for filename in os.listdir(levels_dir):
                if filename.startswith('level_') and filename.endswith('.txt'):
                    try:
                        level_num = int(filename.split('level_')[1].split('.')[0])
                        max_level = max(max_level, level_num)
                    except:
                        pass
        
        print(f"Found {max_level} levels")
        return max_level

    def reset_game(self, level_num=None):
        """Reset game to initial state, optionally at a specific level"""
        if level_num is None:
            level_num = self.current_level
        else:
            self.current_level = level_num
            
        level_file = f'ShovelKnight/assets/levels/level_{level_num}.txt'
        
        # Check if level file exists
        if not os.path.exists(level_file):
            print(f"Level file {level_file} not found!")
            if level_num > 1:
                # Try loading the first level instead
                self.current_level = 1
                return self.reset_game(1)
            else:
                # levels do not exist, quit
                print("No level files found! Game cannot start.")
                pg.quit()
                sys.exit()
        
        self.level = Level(level_file)
        self.add_listener(0)
        
        self.camera = Camera()
        self.camera.pos = [0, 0]
        
        self.player = None
        self.enemies = []
        
        for entity in self.level.entities:
            if isinstance(entity, Knight):
                self.player = entity
            else: 
                self.enemies.append(entity)
                entity.level = self.level
        
        if self.player is None and len(self.level.entities) > 0:
            self.player = self.level.entities[0]
            
        self.game_state = "running"
        print(f"Game has been reset to level {self.current_level}!")

    def next_level(self):
        self.current_level += 1
        
        # Check if we've completed all levels
        if self.current_level > self.max_level:
            self.game_state = "victory"
            self.victory_sound.play()
            print("All levels completed! Victory!")
        else:
            self.next_level_sound.play()
            self.reset_game(self.current_level)
            print(f"Advancing to level {self.current_level}")

    def draw(self):
        # Always draw the game background
        self.surface.blit(sprites.sprite(
            'bg', size=HALF_WINDOW_SIZE), (0, 0))

        if self.game_state == "running":
            view = self.level.map.subsurface(
                tuple(self.camera.pos) + HALF_WINDOW_SIZE)

            self.surface.blit(view, (0, 0))

            for entity in self.level.entities:
                entity.draw(self.surface, offset=(self.camera.pos[0], 0))
                
            if self.player and hasattr(self.player, 'draw_health_bar'):
                self.player.draw_health_bar(self.surface, 10, 10, 100, 16)
                
            # Draw level number
            level_text = self.small_font.render(f"Level: {self.current_level}", True, BLACK)
            self.surface.blit(level_text, (10, 30))
            
            # DEBUG: Draw win triggers for debugging
            for win_trigger in self.level.win_triggers:
                debug_rect = Rect(
                    win_trigger.rect.x - self.camera.pos[0],
                    win_trigger.rect.y,  
                    win_trigger.rect.width,
                    win_trigger.rect.height
                )
                pg.draw.rect(self.surface, GREEN, debug_rect, 2)
            
        elif self.game_state == "game_over":
            # Draw the game over screen
            game_over_text = self.font.render("GAME OVER", True, RED)
            restart_text = self.small_font.render("Press R to restart", True, BLACK)
            quit_text = self.small_font.render("Press Q to quit", True, BLACK)
            
            text_rect = game_over_text.get_rect(center=(HALF_WINDOW_SIZE[0] / 2, HALF_WINDOW_SIZE[1] / 2 - 30))
            restart_rect = restart_text.get_rect(center=(HALF_WINDOW_SIZE[0] / 2, HALF_WINDOW_SIZE[1] / 2 + 10))
            quit_rect = quit_text.get_rect(center=(HALF_WINDOW_SIZE[0] / 2, HALF_WINDOW_SIZE[1] / 2 + 40))
            
            self.surface.blit(game_over_text, text_rect)
            self.surface.blit(restart_text, restart_rect)
            self.surface.blit(quit_text, quit_rect)
            
        elif self.game_state == "victory":
            # Draw victory screen
            victory_text = self.font.render("VICTORY!", True, GOLD)
            level_complete_text = self.small_font.render(f"All {self.max_level} levels completed!", True, GREEN)
            restart_text = self.small_font.render("Press R to restart from level 1", True, WHITE)
            quit_text = self.small_font.render("Press Q to quit", True, WHITE)
            
            text_rect = victory_text.get_rect(center=(HALF_WINDOW_SIZE[0] / 2, HALF_WINDOW_SIZE[1] / 2 - 40))
            level_rect = level_complete_text.get_rect(center=(HALF_WINDOW_SIZE[0] / 2, HALF_WINDOW_SIZE[1] / 2))
            restart_rect = restart_text.get_rect(center=(HALF_WINDOW_SIZE[0] / 2, HALF_WINDOW_SIZE[1] / 2 + 30))
            quit_rect = quit_text.get_rect(center=(HALF_WINDOW_SIZE[0] / 2, HALF_WINDOW_SIZE[1] / 2 + 60))
            
            self.surface.blit(victory_text, text_rect)
            self.surface.blit(level_complete_text, level_rect)
            self.surface.blit(restart_text, restart_rect)
            self.surface.blit(quit_text, quit_rect)

        self.screen.blit(pg_transform.scale(self.surface, WINDOW_SIZE), (0, 0))

    def update(self):
        # Check for restart and quit keys
        keys = pg.key.get_pressed()
        
        # Handle quitting regardless of game state
        if keys[pg.K_q] or keys[pg.K_ESCAPE]:
            print("Quit key pressed - exiting game")
            pg.quit()
            sys.exit()
            
        # Handle restart in game over or victory state
        if (self.game_state == "game_over" or self.game_state == "victory") and keys[pg.K_r]:
            print("R key pressed - restarting game from level 1")
            self.current_level = 1
            self.reset_game(1)
            return
        
        if self.game_state == "running":
            # Update all entities first
            for entity in self.level.entities:
                entity.update(self.level.tiles)
                
            # Now handle player-enemy interactions
            if self.player and hasattr(self.player, 'check_enemy_collisions'):
                # Pass the current list of enemies
                current_enemies = [e for e in self.level.entities if e != self.player]
                self.player.check_enemy_collisions(current_enemies)
                self.player.check_hazard_collisions(self.level.spikes)
                
                # Update our enemies list
                self.enemies = current_enemies
                
            if self.player and self.level.check_win_condition(self.player):
                print("WIN condition met! Player touched win trigger.")
                self.next_level()
                return  
                        
            # Check if the player has died
            if self.player and self.player.dead:
                self.game_state = "game_over"
                print("Game over - Press R to restart or Q to quit")

            # Update camera
            if self.level.entities:
                self.camera.move(self.level.entities[0])
            
    def on_event(self, event):
        # Handle quit event
        if event.type == pg.QUIT:
            print("Quit event detected!")
            pg.quit()
            sys.exit()
        
        # Process other events only in running state
        if self.game_state == "running":
            for entity in self.level.entities:
                if hasattr(entity, 'on_event'):
                    entity.on_event(event)


# Create and run the game
game = ShovelKnight(TITLE, WINDOW_SIZE, fps=FPS)
game.run()