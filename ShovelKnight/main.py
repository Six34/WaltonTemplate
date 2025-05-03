from config import *
from engine import *
import sys

from engine.level import sprites

from camera import Camera

from player import Knight

HALF_WINDOW_SIZE = (WINDOW_SIZE[0] // 2, WINDOW_SIZE[1] // 2)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)


class ShovelKnight(Game):
    def init(self):
        # Initialize game state first
        self.game_state = "running"
        
        # Then reset game to initial state
        self.reset_game()
        
        # Setup fonts
        self.font = pg.font.SysFont('Arial', 36)
        self.small_font = pg.font.SysFont('Arial', 24)
        
        # Setup music
        pg_mixer.music.set_volume(0.05)
        pg_mixer.music.load('ShovelKnight/assets/sounds/music.ogg')
        pg_mixer.music.play(loops=-1)

    def reset_game(self):
        self.level = Level('ShovelKnight/assets/levels/level_1.txt')
        self.add_listener(0)
        
        # Reset camera position explicitly
        self.camera = Camera()
        self.camera.pos = [0, 0]
        
        self.player = None
        self.enemies = []
        
        for entity in self.level.entities:
            if isinstance(entity, Knight):
                self.player = entity
            else: 
                self.enemies.append(entity)
        
        if self.player is None and len(self.level.entities) > 0:
            self.player = self.level.entities[0]
            
        self.game_state = "running"
        print("Game has been reset!")

    def draw(self):
        # Always draw the game background
        self.surface.blit(sprites.sprite(
            'bg', size=HALF_WINDOW_SIZE), (0, 0))

        if self.game_state == "running":
            # Normal game drawing
            view = self.level.map.subsurface(
                tuple(self.camera.pos) + HALF_WINDOW_SIZE)

            self.surface.blit(view, (0, 0))

            for entity in self.level.entities:
                entity.draw(self.surface, offset=(self.camera.pos[0], 0))
                
            if self.player and hasattr(self.player, 'draw_health_bar'):
                self.player.draw_health_bar(self.surface, 10, 10, 100, 16)
        
        elif self.game_state == "game_over":
            # Draw the game over screen
            game_over_text = self.font.render("GAME OVER", True, (255, 0, 0))
            restart_text = self.small_font.render("Press R to restart", True, (0, 0, 0))
            quit_text = self.small_font.render("Press Q to quit", True, (0, 0, 0))
            
            text_rect = game_over_text.get_rect(center=(HALF_WINDOW_SIZE[0] / 2, HALF_WINDOW_SIZE[1] / 2 - 30))
            restart_rect = restart_text.get_rect(center=(HALF_WINDOW_SIZE[0] / 2, HALF_WINDOW_SIZE[1] / 2 + 10))
            quit_rect = quit_text.get_rect(center=(HALF_WINDOW_SIZE[0] / 2, HALF_WINDOW_SIZE[1] / 2 + 40))
            
            self.surface.blit(game_over_text, text_rect)
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
            
        # Handle restart in game over state
        if self.game_state == "game_over" and keys[pg.K_r]:
            print("R key pressed - restarting game")
            self.reset_game()
            return
        
        # Normal game update
        if self.game_state == "running":
            for entity in self.level.entities:
                entity.update(self.level.tiles)
                
            if self.player and hasattr(self.player, 'check_enemy_collisions'):
                self.player.check_enemy_collisions(self.enemies)
                
                for enemy in list(self.enemies):
                    if enemy not in self.level.entities:
                        self.enemies.remove(enemy)
                        
            # Check if the player has died
            if self.player and self.player.dead:
                self.game_state = "game_over"
                print("Game over - Press R to restart or Q to quit")

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