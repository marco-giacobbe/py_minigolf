import pymunk
import pymunk.pygame_util
# from pymunk.vec2d import Vec2d
import pygame
import math
from modules.points import Points

pygame.init()

DISPLAY_SIZE = width, height = 1000, 700
FPS = 60
SCREEN = pygame.display.set_mode(DISPLAY_SIZE)
MAX_DISTANCE_ALLOWED = 60
FORCE_CONST = 10

BALL_IMG = pygame.image.load("images/golf_ball.png").convert_alpha()
pygame.transform.scale(BALL_IMG, (50, 100))


def draw(space, screen, draw_options, points):
    screen.fill("white")
    space.debug_draw(draw_options)
    if points:
        point_a = (points[0].x, points[0].y)
        point_b = (points[1].x, points[1].y)
        pygame.draw.line(screen, "black", point_a, point_b, width=4)
    pygame.display.update()


def refresh(screen, ball):
    screen.blit(BALL_IMG, ball.body.position)
    pygame.display.update()


def add_object(space, pos):
    body = pymunk.Body()
    body.position = pos
    shape = pymunk.Circle(body, radius=20)
    shape.mass = 1
    shape.color = (255, 0, 0, 100)
    shape.elasticity = 0.5
    shape.friction = 0.5
    space.add(body, shape)
    return shape


def create_obstacles(space, screen_size):
    rectangle = [
        [(screen_size[0]/2, screen_size[1]-5), (screen_size[0], 80)],
        [(screen_size[0]/2, 5), (screen_size[0], 10)],
        [(5, screen_size[1]/2), (10, screen_size[1])],
        [(screen_size[0]-5, screen_size[1]/2), (10, screen_size[1])],
        [(400, 600), (150, 10)]
    ]

    for position, size in rectangle:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = position
        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.5
        shape.friction = 0.2
        space.add(body, shape)


def run(screen, size):
    screen.blit(BALL_IMG, (100, 100))
    _run = True
    clock = pygame.time.Clock()
    space = pymunk.Space()
    space.damping = 0.5
    space.gravity = (0, 981)
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    ball = add_object(space, (400, 500))
    create_obstacles(space, size)
    start_point = None
    points_to_draw = []
    clicked = False
    moving = False
    while _run:
        print(ball.body.velocity)
        if abs(ball.body.velocity) < 4 and moving:
            # ball_position = Points((ball.body.position.x, ball.body.position.y))
            ball.body.angle = 0
            # space.remove(ball)
            # ball = add_object(space, ball_position.to_tuple())
            moving = False
        new_point = Points(pygame.mouse.get_pos())
        if start_point:
            angle = start_point.angle(new_point)

            if start_point.check_distance(new_point, MAX_DISTANCE_ALLOWED):
                x_increment = math.cos(angle)*start_point.distance(new_point)
                y_increment = -math.sin(angle)*start_point.distance(new_point)

            else:
                x_increment = math.cos(angle)*MAX_DISTANCE_ALLOWED
                y_increment = -math.sin(angle)*MAX_DISTANCE_ALLOWED

            ball_position = Points((ball.body.position.x, ball.body.position.y))
            points_to_draw = [ball_position, ball_position + (x_increment, y_increment)]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _run = False
                break
            if not abs(ball.body.velocity):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    start_point = Points(pygame.mouse.get_pos())
                    clicked = True
                if event.type == pygame.MOUSEBUTTONUP and clicked:
                    angle = start_point.angle(new_point)
                    abs_force = points_to_draw[0].distance(points_to_draw[1])
                    x_force = math.cos(angle)*abs_force*FORCE_CONST
                    y_force = math.sin(angle)*abs_force*FORCE_CONST
                    ball.body.apply_impulse_at_local_point(impulse=(-x_force, y_force), point=(0, 0))
                    start_point = None
                    points_to_draw = []
                    clicked = False
                    moving = True

        draw(space, screen, draw_options, points_to_draw)
        refresh(screen, ball)
        space.step(1 / FPS)
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    run(SCREEN, DISPLAY_SIZE)
