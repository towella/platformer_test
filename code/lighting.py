import pygame, math
from random import randint
from support import circle_surf, pos_for_center, raycast, get_rect_corners, get_angle, get_distance


class Light():
    def __init__(self, surface, pos, colour, raycasted, max_radius, min_radius=0, glow_speed=0):
        self.surface = surface
        self.pos = pos
        self.raycasted = raycasted
        # amplitude is difference between max and min / 2, (to account for + and -). This creates correct range for sin
        self.amplitude = (max_radius - min_radius)/2
        self.max_radius = max_radius
        self.min_radius = min_radius
        self.radius = max_radius
        self.colour = colour
        self.time = randint(1, 500)
        self.glow_speed = glow_speed
        self.image = circle_surf(self.radius, self.colour)

    # TODO change angles to RADIANS for precsision
    def raycasted_light(self, pos, tiles):
        angles = []
        points = []
        polygon_points = {}
        # get surface
        light_surf = pygame.Surface((self.radius*2, self.radius*2))
        light_surf.set_colorkey((0, 0, 0))

        # get tile corner angles from pos for raycasting (sorted by angle ascending in a list)
        for tile in tiles:
            for point in get_rect_corners(tile.hitbox):
                if self.radius - get_distance(self.pos, point) >= 0:
                    points.append(point)

        for point in points:
            angle = get_angle(self.pos, point)

            polygon_points[angle + 1] = raycast(angle + 1, pos, self.radius, tiles)
            polygon_points[angle] = point
            polygon_points[angle - 1] = raycast(angle - 1, pos, self.radius, tiles)

            angles.append(angle)
            angles.append(angle + 1)
            angles.append(angle - 1)
                #point[0] -= pos[0] - self.radius  # makes point relative to the screen origin rather than pos origin
                #point[1] -= pos[1] - self.radius
                #points.append(point)

        for point in points:
            pygame.draw.circle(self.surface, 'red', point, 1)

        angles.sort()
        points = []

        for angle in angles:
            points.append(polygon_points[angle])

        print(points)

        if len(points) > 2:
            pygame.draw.polygon(light_surf, self.colour, points, 0)

        return light_surf

    def update(self, dt, pos, tiles=pygame.sprite.Group()):
        # amplitude * sin(time * speed) + max_radius - amplitude
        # adding difference between max_radius and amplitude brings sin values (based on amplitude)
        # into correct range between max and min.
        self.radius = self.amplitude * math.sin(self.time * self.glow_speed) + self.max_radius - self.amplitude
        self.pos = pos

        if not self.raycasted:
            self.image = circle_surf(abs(self.radius), self.colour)
        else:
            self.image = self.raycasted_light(pos, tiles)

        self.time += round(1 * dt)

    def draw(self):
        self.surface.blit(self.image, pos_for_center(self.image, self.pos), special_flags=pygame.BLEND_RGB_ADD)

