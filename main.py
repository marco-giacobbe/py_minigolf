import pymunk
import pymunk.pygame_util
import pygame
import math

from modules.points import Points
from modules.constants import *
from modules.ball import Ball


pygame.init()

SCREEN = pygame.display.set_mode(DISPLAY_SIZE)
COUNTER_FONT = pygame.font.Font(FONT_DIR + "8bit.ttf", 30)
HOLE_FONT = [
    pygame.font.Font(FONT_DIR + "8bit_arcade_out.ttf", 120),
    pygame.font.Font(FONT_DIR + "8bit_arcade_in.ttf", 120)
]
CONTINUE_FONT = pygame.font.Font(FONT_DIR + "8bit.ttf", 20)

FRAME_COUNTER = 0
LEVEL = -1


def get_frame(spritesheet, frame):
    image = pygame.Surface((32, 32)).convert_alpha()
    image.set_colorkey("black")
    image.blit(spritesheet, (0, 0), (frame*32, 0, 32, 32))
    return image


def draw(space, screen, draw_options, points):
    screen.fill(pygame.color.Color(39, 213, 245))
    space.debug_draw(draw_options)

    # draw power line
    if points:
        point_a = (points[0].x, points[0].y)
        point_b = (points[1].x, points[1].y)
        pygame.draw.line(screen, "red", point_a, point_b, width=6)


def create_obstacles(space):
    shapes = []
    for rectangle in OBSTACLES_XY[LEVEL]:
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (0, 0)
        shape = pymunk.Poly(body, rectangle)
        shape.friction = 0.2
        shape.elasticity = 0.6
        shape.color = (30, 157, 45, 1)
        if rectangle[0][1] == rectangle[2][1]:
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
    return [Ball(BALL_XY[LEVEL], space), create_obstacles(space), create_hole(space)]


def remove_level(space, obj):
    space.remove(obj[0].shape, obj[0].body)
    for _obj in obj[1]:
        space.remove(_obj, _obj.body)
    space.remove(obj[2], obj[2].body)


def parable(x):
    y = (x**2)/1800
    return round(y, 3)


def module_damping(space, ball):
    global FRAME_COUNTER
    if abs(ball.body.velocity) > 100 or abs(ball.body.velocity) < 1:
        space.damping = SLIDE_DAMPING
        FRAME_COUNTER = 0
    else:
        if FRAME_COUNTER < MAX_FRAME_DAMPING:
            space.damping = SLIDE_DAMPING - parable(FRAME_COUNTER)
            FRAME_COUNTER += 0.5


def create_collision_handler(space):
    ball_collision = space.add_collision_handler(COLL_TYPE_BALL, COLL_TYPE_HOLE)
    object_collision = space.add_collision_handler(COLL_TYPE_BALL, COLL_TYPE_OBS)
    return [ball_collision, object_collision]


def slide_collision(arbiter, space, data):
    data["ball"].collision = True
    if data["ball"].moving:
        module_damping(space, data["ball"])
        data["ball"].check_stop()
    return True


def end_sliding(arbiter, space, data):
    space.damping = AIR_DAMPING
    return True


def run(screen):
    global LEVEL
    clock = pygame.time.Clock()
    space = pymunk.Space()
    space.gravity = (0, GRAVITY)
    draw_options = pymunk.pygame_util.DrawOptions(screen)
    start_point = None
    points_to_draw = []
    clicked = False
    shot_counter = 0
    new_level = True
    obj = [None]
    new_point = None
    while True:
        draw(space, screen, draw_options, points_to_draw)
        if new_level:
            LEVEL += 1
            if LEVEL == MAX_LEVEL:
                return 0
            new_level = False
            if obj[0]:
                remove_level(space, obj)
            obj = create_level(space)
            coll_handler = create_collision_handler(space)
            coll_handler[0].begin = obj[0].in_hole
            coll_handler[1].pre_solve = slide_collision
            coll_handler[1].separate = end_sliding
            coll_handler[1].data["ball"] = obj[0]

        if not obj[0].hole:
            obj[0].in_game()
            new_point = Points(pygame.mouse.get_pos())

            if start_point:
                print(start_point)
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

            if abs(obj[0].body.velocity) < 10 and not obj[0].hole:
                if event.type == pygame.MOUSEBUTTONDOWN and not obj[0].moving:
                    start_point = Points(pygame.mouse.get_pos())
                    clicked = True

                if event.type == pygame.MOUSEBUTTONUP and clicked:
                    shot_counter += 1
                    angle = start_point.angle(new_point)
                    force = points_to_draw[0].distance(points_to_draw[1])
                    obj[0].apply_force(force, angle)
                    start_point = None
                    points_to_draw = []
                    clicked = False
                    obj[0].moving = True

            if obj[0].hole and event.type == pygame.MOUSEBUTTONDOWN:
                new_level = True
                shot_counter = 0

        if shot_counter > 0 and not obj[0].hole:
            text = COUNTER_FONT.render("SHOT: {}".format(shot_counter), True, "black")
            screen.blit(text, (10, 10))

        if obj[0].hole:
            obj[0].moving = False
            hole_text = HOLE_FONT[1].render("HOLE IN {}".format(shot_counter), True, "yellow")
            hole_text.blit(HOLE_FONT[0].render("HOLE IN {}".format(shot_counter), True, "green"), (0, 0))
            hole_text_rect = hole_text.get_rect(center=(DISPLAY_SIZE[0]/2, DISPLAY_SIZE[1]/2))
            continue_text = CONTINUE_FONT.render("Click to continue...", True, "black")
            continue_text_rect = continue_text.get_rect(center=(DISPLAY_SIZE[0]/2, DISPLAY_SIZE[1]/2 + 70))
            screen.blit(hole_text, hole_text_rect)
            screen.blit(continue_text, continue_text_rect)

        obj[0].update(screen)
        pygame.display.update()
        space.step(1 / FPS)
        clock.tick(FPS)


if __name__ == "__main__":
    if not run(SCREEN):
        pygame.quit()
