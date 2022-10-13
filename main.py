import pymunk
import pymunk.pygame_util
import pygame
import math
from modules.points import Points

pygame.init()

DISPLAY_SIZE = (1600, 900)
FPS = 75
SCREEN = pygame.display.set_mode(DISPLAY_SIZE)
MAX_DISTANCE_ALLOWED = 60
FORCE_CONST = 20
RADIUS = 15
FONT = pygame.font.SysFont("Times New Roman", 40, bold=True)
START_POS = (400, 500)

BALL_IMG = pygame.image.load("images/golf_ball.png").convert_alpha()
BALL_IMG = pygame.transform.scale(BALL_IMG, (32, 32))
GRASS_IMG = pygame.image.load("images/grass.png").convert_alpha()
GRASS_IMG = pygame.transform.scale(GRASS_IMG, (285, 70))


def draw(space, screen, draw_options, points):
    screen.fill(pygame.color.Color(39, 213, 245))
    space.debug_draw(draw_options)

    # draw grass
    x = -1
    for i in range(6):
        screen.blit(GRASS_IMG, (x, 842))
        x += 284

    # draw power line
    if points:
        point_a = (points[0].x, points[0].y)
        point_b = (points[1].x, points[1].y)
        pygame.draw.line(screen, "black", point_a, point_b, width=4)


def refresh(screen, ball):
    screen.blit(BALL_IMG, (ball.body.position.x - RADIUS, ball.body.position.y - RADIUS))
    pygame.display.update()


def add_object(space, pos):
    body = pymunk.Body()
    body.position = pos
    shape = pymunk.Circle(body, radius=RADIUS)
    shape.mass = 1
    shape.color = (255, 0, 0, 100)
    shape.elasticity = 0.6
    shape.friction = 0.5
    space.add(body, shape)
    return shape


def create_obstacles(space, screen_size):
    rectangle = [
        [(screen_size[0]/2, screen_size[1]-5), (screen_size[0], 80)],
    ]

    for position, size in rectangle:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = position
        shape = pymunk.Poly.create_box(body, size)
        shape.elasticity = 0.6
        shape.friction = 0.2
        space.add(body, shape)


def is_ingame(ball):
    return ball.body.position.y < DISPLAY_SIZE[1]

def module_damping(space, ball):
    print(space.damping)
    if ball.body.velocity.y < 1 and space.damping == 1:
        space.damping = 0.9
    elif ball.body.velocity.y < 1 and space.damping > 0.3:
        space.damping -= 0.03
    elif ball.body.velocity.y < 1 and space.damping <= 0.3:
        pass
    else:
        space.damping = 1


def run(screen, size):
    _run = True
    clock = pygame.time.Clock()
    space = pymunk.Space()
    space.damping = 0.4
    space.gravity = (0, 981)
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    ball = add_object(space, START_POS)
    create_obstacles(space, size)
    start_point = None
    points_to_draw = []
    clicked = False
    moving = False
    shot_counter = 0
    last_pos = None
    while _run:
        module_damping(space, ball)
        if not is_ingame(ball):
            space.remove(ball, ball.body)
            ball = add_object(space, last_pos)

        if abs(ball.body.velocity) < 4 and moving:
            ball.body.body_type = pymunk.Body.STATIC
            ball.body.angle = 0
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

            if abs(ball.body.velocity) < 4:
                if event.type == pygame.MOUSEBUTTONDOWN and not moving:
                    ball.body.body_type = pymunk.Body.DYNAMIC
                    start_point = Points(pygame.mouse.get_pos())
                    clicked = True

                if event.type == pygame.MOUSEBUTTONUP and clicked:
                    shot_counter += 1
                    last_pos = ball.body.position
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

        if shot_counter > 0:
            text = FONT.render("Shot: {}".format(shot_counter), True, "black")
            screen.blit(text, (10, 10))

        refresh(screen, ball)
        space.step(1 / FPS)
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    run(SCREEN, DISPLAY_SIZE)
