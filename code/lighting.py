import pygame, math
from random import randint
from support import circle_surf, pos_for_center


class Light():
    def __init__(self, pos, colour, max_radius, min_radius=0, glow_speed=0):
        self.pos = pos
        # amplitude is difference between max and min / 2, (to account for + and -). This creates correct range for sin
        self.amplitude = (max_radius - min_radius)/2
        self.max_radius = max_radius
        self.min_radius = min_radius
        self.radius = max_radius
        self.colour = colour
        self.time = randint(1, 500)
        self.glow_speed = glow_speed
        self.image = circle_surf(self.radius, self.colour)

    def update(self):
        # amplitude * sin(time * speed) + max_radius - amplitude
        # adding difference between max_radius and amplitude brings sin values (based on amplitude)
        # into correct range between max and min.
        self.radius = self.amplitude * math.sin(self.time * self.glow_speed) + self.max_radius - self.amplitude
        self.image = circle_surf(abs(self.radius), self.colour)
        self.time += 1

    def draw(self, surface, pos):
        surface.blit(self.image, pos_for_center(self.image, pos), special_flags=pygame.BLEND_RGB_ADD)

