import pygame
import pymunk
import math

from modules.constants import *

SLEEP = False


class Ball:
    def __init__(self, xy, space):
        self.body = pymunk.Body()
        self.body.position = xy
        self.shape = pymunk.Circle(self.body, radius=BALL_RADIUS)
        self.shape.elasticity = 0.6
        self.shape.friction = 0.5
        self.shape.mass = 1
        self.shape.collision_type = COLL_TYPE_BALL
        self.shape.color = (255, 255, 255, 100)
        self.hole = False
        self.moving = True
        self.last_position = xy
        space.add(self.body, self.shape)

    def update(self, screen):
        pygame.draw.circle(screen, "white", self.body.position, BALL_RADIUS)
        if not self.moving:
            self.body.body_type = pymunk.Body.STATIC
            self.body.body_type = pymunk.Body.DYNAMIC
            self.body.angle = 0
            self.shape.collision_type = COLL_TYPE_BALL

    def in_hole(self, arbiter, space, data):
        self.hole = True
        return True

    def check_stop(self):
        if abs(self.body.velocity) < 20 and self.moving:
            self.shape.collision_type = 0
            self.moving = False
            self.last_position = self.body.position

    def in_game(self):
        if self.body.position.y > DISPLAY_SIZE[1]:
            self.body.position = self.last_position
            self.body.body_type = pymunk.Body.STATIC
            self.body.body_type = pymunk.Body.DYNAMIC

    def apply_force(self, absolute_force, angle):
        x_force = math.cos(angle)*absolute_force*FORCE_MULTIPLIER
        y_force = math.sin(angle)*absolute_force*FORCE_MULTIPLIER
        self.body.apply_impulse_at_local_point(impulse=(-x_force, y_force), point=(0, 0))
