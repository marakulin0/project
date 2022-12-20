import pygame
from menu import Menu
from car import Car_road, Car_bio
import controls
screen = pygame.display.set_mode((1024, 768))
clock = pygame.time.Clock()
punkts = [(420, 300, u'Play', (11, 0, 77), (250, 250, 30), 0),
          (420, 400, u'Exit', (11, 0, 77), (250, 250, 30), 1)]
punkts1 = [(100, 100, 0), (600, 100, 1)]
game = Menu(punkts, punkts1)
points1 = 0
points2 = 0
start_collider_road = pygame.rect.Rect(282, 618, 56, 143)
mid_collider_road = pygame.rect.Rect(466, 182, 10, 122)
start_collider_bio = pygame.rect.Rect(872, 521, 128, 13)
mid_collider_bio = pygame.rect.Rect(439, 421, 10, 132)
FPS = 60


def run_road():
    points1 = 0
    points2 = 0
    running = True
    now = [0, 0]
    bg = pygame.image.load('road.png')
    pygame.display.set_caption('Racing')
    car1 = Car_road(screen, 355, 715, 'car_1.png')
    car2 = Car_road(screen, 455, 715, 'car_2.png')
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    start()
        screen.blit(bg, (0, 0))
        car1.draw_car()
        car1.collision_handing(car1.rects)
        car1.move_car1()
        car2.draw_car()
        car2.collision_handing(car2.rects)
        car2.move_car2()
        controls.pause()
        clock.tick(FPS)
        controls.mid_collider_handler(car1, car2, mid_collider_road)
        points1, points2, now[0], now[1] = \
            controls.points_counter(car1, car2,
                                    start_collider_road,
                                    points1, points2, now)
        finish(points1, points2)
        pygame.display.update()


def run_bio():
    points1 = 0
    points2 = 0
    now = [0, 0]
    running = True
    bg = pygame.image.load('bio.png')
    pygame.display.set_caption('Racing')
    car1 = Car_bio(screen, 875, 535, 'car_1.png')
    car2 = Car_bio(screen, 960, 535, 'car_2.png')
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    start()
        screen.blit(bg, (0, 0))
        car1.draw_car()
        car1.move_car1()
        car1.collision_handing(car1.rects)
        car2.collision_handing(car2.rects)
        car2.draw_car()
        car2.move_car2()
        controls.pause()
        clock.tick(FPS)
        controls.mid_collider_handler(car1, car2, mid_collider_bio)
        points1, points2, now[0], now[1] = \
            controls.points_counter(car1, car2,
                                    start_collider_bio,
                                    points1, points2, now)
        finish(points1, points2)
        pygame.display.update()


def finish(points1, points2):
    paused = False
    if points1 == 3 or points2 == 3:
        paused = True
    while paused:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            paused = False
            start()
        if points1 == 3:
            controls.print_text('Player 1 wins', 300, 300,
                                font_colour=(0, 0, 255), font_type='arial',
                                font_size=100)
        if points2 == 3:
            controls.print_text('Player 2 wins', 300, 300,
                                font_colour=(0, 0, 255), font_type='arial',
                                font_size=100)
        points1 = 0
        points2 = 0
        pygame.display.update()


def start():
    pygame.init()
    pygame.mixer.music.load('font_music.MP3')
    pygame.mixer.music.play(-1)
    game.menu()
    game.menu_1()
    if game.menu_1() == 0:
        run_road()
    else:
        run_bio()
    pygame.quit()


start()
pygame.quit()
