import pymunk
import pymunk.pygame_util
import pygame
import math
from modules.points import Points
from modules.constants import *

# import time


pygame.init()

SCREEN = pygame.display.set_mode(DISPLAY_SIZE)
COUNTER_FONT = pygame.font.Font(FONT_DIR + "8bit.ttf", 30)
HOLE_FONT = [
    pygame.font.Font(FONT_DIR + "8bit_arcade_out.ttf", 120),
    pygame.font.Font(FONT_DIR + "8bit_arcade_in.ttf", 120)
]
CONTINUE_FONT = pygame.font.Font(FONT_DIR + "8bit.ttf", 20)
BALL_IMG = pygame.image.load(IMG_DIR+"golf_ball.png").convert_alpha()
GRASS_IMG = pygame.image.load(IMG_DIR+"grass.png").convert_alpha()

FRAME_COUNTER = 0
LEVEL = -1

COLL_TYPE_BALL = 1
COLL_TYPE_HOLE = 2
COLL_TYPE_OBS = 3


def get_frame(spritesheet, frame):
    image = pygame.Surface((32, 32)).convert_alpha()
    image.set_colorkey("black")
    image.blit(spritesheet, (0, 0), (frame*32, 0, 32, 32), )
    return image


def draw(space, screen, draw_options, points):
    screen.fill(pygame.color.Color(39, 213, 245))
    space.debug_draw(draw_options)

    # draw grass
    x = -1
    for i in range(1):
        # screen.blit(GRASS_IMG, (x, 820))
        x += 284

    # draw power line
    if points:
        point_a = (points[0].x, points[0].y)
        point_b = (points[1].x, points[1].y)
        pygame.draw.line(screen, "red", point_a, point_b, width=6)


def refresh(screen, ball):
    global BALL_IMG
    angle = (ball.body.angle*57.2958) % 360
    ball_frame = get_frame(BALL_IMG, angle//20)
    screen.blit(ball_frame, (ball.body.position.x - BALL_RADIUS, ball.body.position.y - BALL_RADIUS))
    pygame.display.update()


def create_ball(space, pos):
    body = pymunk.Body()
    body.position = pos
    shape = pymunk.Circle(body, radius=BALL_RADIUS)
    shape.mass = 1
    shape.color = (255, 0, 0, 100)
    shape.elasticity = 0.6
    shape.friction = 0.5
    shape.collision_type = COLL_TYPE_BALL
    space.add(body, shape)
    return shape


def create_obstacles(space):
    shapes = []
    for rectangle in OBSTACLES_XY[LEVEL]:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (0, 0)
        shape = pymunk.Poly(body, rectangle)
        shape.friction = 0.2
        shape.elasticity = 0.6
        shape.collision_type = COLL_TYPE_OBS
        space.add(body, shape)
        shapes.append(shape)
    return shapes


def create_hole(space):
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = (0, 0)
    shape = pymunk.Poly(body, HOLE_XY[LEVEL])
    shape.color = (219, 245, 39, 0.8)
    shape.collision_type = COLL_TYPE_HOLE
    space.add(body, shape)
    return shape


def create_level(space):
    return [create_ball(space, BALL_XY[LEVEL]), create_obstacles(space), create_hole(space)]


def remove_level(space, obj):
    space.remove(obj[0], obj[0].body)
    for _obj in obj[1]:
        space.remove(_obj, _obj.body)
    space.remove(obj[2], obj[2].body)


def is_ingame(ball):
    return ball.body.position.y < DISPLAY_SIZE[1]


def in_hole(ball):
    hole = Points(((HOLE_XY[LEVEL][0][0] + HOLE_XY[LEVEL][2][0])/2, HOLE_XY[LEVEL][1][1]))
    return hole.check_distance(Points(ball.body.position), MAX_INHOLE_DISTANCE)


def in_hole_screen(screen, n_shot):
    text = HOLE_FONT[1].render("HOLE IN {} SHOT".format(n_shot), True, "black")
    text.blit(HOLE_FONT[0].render("HOLE IN {} SHOT".format(n_shot), True, "red"), (0, 0))
    screen.blit(text, (DISPLAY_SIZE[0]/2, DISPLAY_SIZE[1]/2))


def parable(x):
    y = (x**2)/1800
    return round(y, 3)


def module_damping(space, ball, moving):
    global FRAME_COUNTER
    if moving:
        if abs(ball.body.velocity) > 40:
            space.damping = 0.5
        else:
            if FRAME_COUNTER < MAX_FRAME_DAMPING:
                space.damping = 0.5 - parable(FRAME_COUNTER)
                FRAME_COUNTER += 0.5
    else:
        space.damping = 0.5


def create_collision_handler(space):
    return [
        space.add_collision_handler(COLL_TYPE_BALL, COLL_TYPE_HOLE),
        space.add_collision_handler(COLL_TYPE_BALL, COLL_TYPE_OBS)
    ]


def run(screen, size):  # , size):
    global LEVEL
    clock = pygame.time.Clock()
    space = pymunk.Space()
    space.gravity = (0, GRAVITY)
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    start_point = None
    points_to_draw = []
    clicked = False
    moving = False
    shot_counter = 0
    last_pos = None
    hole = False
    new_level = True
    obj = [None]
    obj[0] = None
    coll_handler = []
    while True:
        if new_level:
            LEVEL += 1
            if LEVEL == MAX_LEVEL:
                return 0
            new_level = False
            if obj[0]:
                remove_level(space, obj)
            obj = create_level(space)
            coll_handler = create_collision_handler(space)
        if not hole:
            module_damping(space, obj[0], moving)
            if in_hole(obj[0]):
                hole = True

            # check_hole_collision(coll_handler[0])
            # check_obs_collision(coll_handler[1])

            if not is_ingame(obj[0]):
                space.remove(obj[0], obj[0].body)
                obj[0] = create_ball(space, last_pos)

            if abs(obj[0].body.velocity) < 4 and moving:
                obj[0].body.body_type = pymunk.Body.STATIC
                obj[0].body.angle = 0
                obj[0].body.body_type = pymunk.Body.DYNAMIC
                moving = False
            new_point = Points(pygame.mouse.get_pos())

            if start_point:
                angle = start_point.angle(new_point)

                if start_point.check_distance(new_point, MAX_POWERLINE_LEN):
                    x_increment = math.cos(angle)*start_point.distance(new_point)
                    y_increment = -math.sin(angle)*start_point.distance(new_point)

                else:
                    x_increment = math.cos(angle) * MAX_POWERLINE_LEN
                    y_increment = -math.sin(angle) * MAX_POWERLINE_LEN

                ball_position = Points((obj[0].body.position.x, obj[0].body.position.y))
                points_to_draw = [ball_position, ball_position + (x_increment, y_increment)]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 0

            if abs(obj[0].body.velocity) < 4 and not hole:
                if event.type == pygame.MOUSEBUTTONDOWN and not moving:
                    start_point = Points(pygame.mouse.get_pos())
                    clicked = True

                if event.type == pygame.MOUSEBUTTONUP and clicked:
                    shot_counter += 1
                    last_pos = obj[0].body.position
                    angle = start_point.angle(new_point)
                    abs_force = points_to_draw[0].distance(points_to_draw[1])
                    x_force = math.cos(angle)*abs_force*FORCE_MULTIPLIER
                    y_force = math.sin(angle)*abs_force*FORCE_MULTIPLIER
                    obj[0].body.apply_impulse_at_local_point(impulse=(-x_force, y_force), point=(0, 0))
                    start_point = None
                    points_to_draw = []
                    clicked = False
                    moving = True

            if hole and event.type == pygame.MOUSEBUTTONDOWN:
                hole = False
                new_level = True
                shot_counter = 0

        draw(space, screen, draw_options, points_to_draw)

        if shot_counter > 0 and not hole:
            text = COUNTER_FONT.render("SHOT: {}".format(shot_counter), True, "black")
            screen.blit(text, (10, 10))

        if hole:
            print("asshole")
            moving = False
            hole_text = HOLE_FONT[1].render("HOLE IN {}".format(shot_counter), True, "yellow")
            hole_text.blit(HOLE_FONT[0].render("HOLE IN {}".format(shot_counter), True, "green"), (0, 0))
            hole_text_rect = hole_text.get_rect(center=(DISPLAY_SIZE[0]/2, DISPLAY_SIZE[1]/2))
            continue_text = CONTINUE_FONT.render("Click to continue...", True, "black")
            continue_text_rect = continue_text.get_rect(center=(DISPLAY_SIZE[0]/2, DISPLAY_SIZE[1]/2 + 70))
            screen.blit(hole_text, hole_text_rect)
            screen.blit(continue_text, continue_text_rect)

        refresh(screen, obj[0])
        space.step(1 / FPS)
        clock.tick(FPS)


if __name__ == "__main__":
    if not run(SCREEN, DISPLAY_SIZE):
        pygame.quit()
