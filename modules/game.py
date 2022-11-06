import pygame
import pymunk
import pymunk.pygame_util
import math

from modules.constants import *
from modules.ball import Ball
from modules.points import Points


class Game:
    def __init__(self):
        # pygame and pymunk objects
        self.screen = pygame.display.set_mode(DISPLAY_SIZE)
        self.clock = pygame.time.Clock()
        self.space = pymunk.Space()
        self.space.gravity = (0, GRAVITY)
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.collision_handler = []

        self.level = -1
        self.new_level = True
        self.start_point = None  # where player click to load the shot
        self.new_point = None  # where player release the shot
        self.points_to_draw = []
        self.clicked = False  # flag to check if player is loading the shot
        self.shot_counter = 0  # counter for shot in a single level
        self.total_shot_counter = 0  # counter for all the shot

        # object of game
        self.ball = None
        self.obstacles = None
        self.hole = None

        self.fonts = [
            [
                pygame.font.Font(FONT_DIR + "8bit_arcade_out.ttf", 120),
                pygame.font.Font(FONT_DIR + "8bit_arcade_in.ttf", 120)
            ],
            pygame.font.Font(FONT_DIR + "8bit.ttf", 20),
            pygame.font.Font(FONT_DIR + "8bit.ttf", 30)
        ]

        # counter for patch damping
        self.frame_counter = 0

    def run(self):
        while True:
            if self.new_level:
                self.create_new_level()

            self.draw_game()

            if self.handle_event():
                # player want to quit
                return False

            if not self.ball.hole:
                # calculate release position
                self.new_point = Points(pygame.mouse.get_pos())

                if self.start_point:
                    self.load_shot()

                if self.shot_counter > 0:
                    self.draw_shot()

            else:
                self.ball.moving = False
                self.draw_score()
            self.update_game()

    def handle_event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if abs(self.ball.body.velocity) < 10 and not self.ball.moving and not self.ball.hole:
                # check if ball is hittable
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # player loads the shot
                    self.start_point = Points(pygame.mouse.get_pos())
                    self.clicked = True
                if event.type == pygame.MOUSEBUTTONUP and self.clicked:
                    # ball gets hit
                    self.shot_counter += 1
                    angle = self.start_point.angle(self.new_point)
                    force = self.points_to_draw[0].distance(self.points_to_draw[1])
                    self.ball.apply_force(force, angle)
                    self.points_to_draw = []
                    self.start_point = None
                    self.clicked = False
                    self.ball.moving = True

            if event.type == pygame.MOUSEBUTTONDOWN and self.ball.hole:
                if self.level == MAX_LEVEL:
                    return True
                # ball is in hole and player is ready for the next level
                self.new_level = True
                self.total_shot_counter += self.shot_counter
                self.shot_counter = 0

    def update_game(self):
        pygame.display.update()
        self.space.step(1 / FPS)
        self.clock.tick(FPS)

    def create_new_level(self):
        self.level += 1
        self.new_level = False
        if self.ball:
            self.remove_level()
        self.create_level()
        self.collision_handler = self.create_collision_handler()

    def create_level(self):
        self.ball = Ball(BALL_XY[self.level], self.space)
        self.obstacles = self.create_obstacles()
        self.hole = self.create_hole()

    def remove_level(self):
        self.space.remove(self.ball.shape, self.ball.body)
        for obstacle in self.obstacles:
            self.space.remove(obstacle, obstacle.body)
        self.space.remove(self.hole, self.hole.body)

    def create_obstacles(self):
        shapes = []
        for rectangle in OBSTACLES_XY[self.level]:
            body = pymunk.Body(body_type=pymunk.Body.STATIC)
            body.position = (0, 0)
            shape = pymunk.Poly(body, rectangle)
            shape.friction = 0.2
            shape.elasticity = 0.6
            shape.color = (30, 157, 45, 1)
            if rectangle[0][1] == rectangle[2][1]:
                shape.collision_type = COLL_TYPE_OBS
            self.space.add(body, shape)
            shapes.append(shape)
        return shapes

    def create_hole(self):
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (0, 0)
        shape = pymunk.Poly(body, HOLE_XY[self.level])
        shape.color = (219, 245, 39, 0.8)
        shape.collision_type = COLL_TYPE_HOLE
        self.space.add(body, shape)
        return shape

    def create_collision_handler(self):
        hole_collision = self.space.add_collision_handler(COLL_TYPE_BALL, COLL_TYPE_HOLE)
        hole_collision.begin = self.ball.in_hole
        grass_collision = self.space.add_collision_handler(COLL_TYPE_BALL, COLL_TYPE_OBS)
        grass_collision.pre_solve = self.sliding
        grass_collision.separate = self.end_slide
        return [hole_collision, grass_collision]

    def sliding(self, arbiter, space, data):
        if self.ball.moving:
            self.module_damping()
            self.ball.check_stop()
        return True

    def end_slide(self, arbiter, space, data):
        self.space.damping = AIR_DAMPING
        return True

    def module_damping(self):
        if abs(self.ball.body.velocity) > 100 or abs(self.ball.body.velocity) < 1:
            self.space.damping = SLIDE_DAMPING
            self.frame_counter = 0
        else:
            if self.frame_counter < MAX_FRAME_DAMPING:
                self.space.damping = SLIDE_DAMPING - self.parable()
                self.frame_counter += 0.5

    def parable(self):
        y_value = (self.frame_counter**2)/1800
        return round(y_value, 3)

    def load_shot(self):
        angle = self.start_point.angle(self.new_point)

        if self.start_point.check_distance(self.new_point, MAX_POWERLINE_LEN):
            # if len of shot bar < MAX_POWERLINE_LEN
            x_increment = math.cos(angle)*self.start_point.distance(self.new_point)
            y_increment = -math.sin(angle)*self.start_point.distance(self.new_point)
        else:
            x_increment = math.cos(angle) * MAX_POWERLINE_LEN
            y_increment = -math.sin(angle) * MAX_POWERLINE_LEN

        ball_position = Points((self.ball.body.position.x, self.ball.body.position.y))
        self.points_to_draw = [ball_position, ball_position + (x_increment, y_increment)]

    def draw_game(self):
        self.screen.fill(pygame.color.Color(39, 213, 245))
        self.space.debug_draw(self.draw_options)
        self.ball.update(self.screen)
        if self.points_to_draw:
            point_a = (self.points_to_draw[0].x, self.points_to_draw[0].y)
            point_b = (self.points_to_draw[1].x, self.points_to_draw[1].y)
            pygame.draw.line(self.screen, "red", point_a, point_b, width=6)

    def draw_shot(self):
        text = self.fonts[2].render("SHOT: {}".format(self.shot_counter), True, "black")
        self.screen.blit(text, (10, 10))

    def draw_score(self):
        if self.level != MAX_LEVEL:
            hole_text = self.fonts[0][1].render("HOLE IN {}".format(self.shot_counter), True, "yellow")
            hole_text.blit(self.fonts[0][0].render("HOLE IN {}".format(self.shot_counter), True, "green"), (0, 0))
            hole_text_rect = hole_text.get_rect(center=(DISPLAY_SIZE[0]/2, DISPLAY_SIZE[1]/2))
            continue_text = self.fonts[1].render("Click to continue...", True, "black")
            continue_text_rect = continue_text.get_rect(center=(DISPLAY_SIZE[0]/2, DISPLAY_SIZE[1]/2 + 70))
            self.screen.blit(hole_text, hole_text_rect)
            self.screen.blit(continue_text, continue_text_rect)
        else:
            hole_text = self.fonts[0][1].render("TOTAL SCORE {}".format(self.shot_counter), True, "yellow")
            hole_text.blit(self.fonts[0][0].render("TOTAL SCORE {}".format(self.shot_counter), True, "green"), (0, 0))
            hole_text_rect = hole_text.get_rect(center=(DISPLAY_SIZE[0]/2, DISPLAY_SIZE[1]/2))
            continue_text = self.fonts[1].render("Click to end...", True, "black")
            continue_text_rect = continue_text.get_rect(center=(DISPLAY_SIZE[0]/2, DISPLAY_SIZE[1]/2 + 70))
            self.screen.blit(hole_text, hole_text_rect)
            self.screen.blit(continue_text, continue_text_rect)
