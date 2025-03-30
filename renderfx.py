import pygame
import numpy as np

# Initialize Pygame with no sound
pygame.mixer.pre_init(44100, -16, 2, 512)  # Set up mixer but will be muted
pygame.mixer.init()
pygame.mixer.quit()  # Disable sound entirely
pygame.init()

# Window settings
WINDOW_SIZE = (800, 600)
PIXEL_SIZE = 64
SCALE = 8  # Scale factor for pixel art
screen = pygame.display.set_mode(WINDOW_SIZE)
pygame.display.set_caption("Super Mario 64 Renderer")
clock = pygame.time.Clock()

class SM64Renderer:
    def __init__(self):
        self.pixel_size = PIXEL_SIZE
        self.surface = pygame.Surface((self.pixel_size, self.pixel_size), pygame.SRCALPHA)  # Enable alpha channel
        self.generate_texture()

    def generate_texture(self):
        # Create pixel array with alpha channel (3D: height, width, RGBA)
        pixels = np.zeros((self.pixel_size, self.pixel_size, 4), dtype=np.uint8)
        
        # N64-style color palette (RGBA)
        colors = {
            'mario_red': [228, 32, 48, 255],
            'overalls_blue': [32, 96, 255, 255],
            'skin': [255, 216, 176, 255],
            'hair': [148, 80, 52, 255],
            'eyes': [32, 32, 32, 255]
        }

        # Draw Mario's body
        self.draw_rect(pixels, 24, 20, 16, 24, colors['mario_red'])
        # Add overalls
        self.draw_rect(pixels, 24, 32, 16, 12, colors['overalls_blue'])
        # Create head
        self.draw_circle(pixels, 32, 16, 8, colors['skin'])
        # Add hat
        self.draw_rect(pixels, 20, 4, 24, 8, colors['hair'])

        # Convert numpy array to Pygame surface (ensure correct RGBA format)
        # Use make_surface instead of blit_array for better compatibility
        self.surface = pygame.surfarray.make_surface(pixels[:, :, :3])  # Use RGB channels
        self.surface = pygame.transform.scale(self.surface, (self.pixel_size, self.pixel_size))  # Ensure size matches
        self.surface.set_alpha(255)  # Set full opacity

    def draw_rect(self, pixels, x, y, w, h, color):
        # Ensure bounds are within the pixel array
        x_end = min(x + w, self.pixel_size)
        y_end = min(y + h, self.pixel_size)
        x_start = max(x, 0)
        y_start = max(y, 0)
        pixels[y_start:y_end, x_start:x_end] = color

    def draw_circle(self, pixels, cx, cy, r, color):
        y, x = np.ogrid[-r:r+1, -r:r+1]
        mask = x*x + y*y <= r*r
        # Ensure circle stays within bounds
        y_start = max(cy - r, 0)
        y_end = min(cy + r + 1, self.pixel_size)
        x_start = max(cx - r, 0)
        x_end = min(cx + r + 1, self.pixel_size)
        pixels[y_start:y_end, x_start:x_end][mask[:y_end-y_start, :x_end-x_start]] = color

    def render(self, screen):
        # Scale up the pixel art and center it
        scaled_surface = pygame.transform.scale(self.surface, (self.pixel_size * SCALE, self.pixel_size * SCALE))
        screen.blit(scaled_surface, ((WINDOW_SIZE[0] - self.pixel_size * SCALE) // 2, 
                                    (WINDOW_SIZE[1] - self.pixel_size * SCALE) // 2))

def main():
    renderer = SM64Renderer()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # Clear screen
        screen.fill((0, 0, 0))  # Black background
        
        # Render Mario
        renderer.render(screen)
        
        # Update display
        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    pygame.quit()

if __name__ == "__main__":
    main()
