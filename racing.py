import sys
import os
import pygame
from menu import Menu
from car import Car_road, Car_bio
import controls


def resource(filename):
    """Возвращает правильный путь к файлу — и в dev-режиме, и внутри .exe"""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)

screen = pygame.display.set_mode((1024, 768))
clock = pygame.time.Clock()

punkts  = [(420, 300, u'Play', (11, 0, 77), (250, 250, 30), 0),
           (420, 400, u'Exit', (11, 0, 77), (250, 250, 30), 1)]
punkts1 = [(100, 100, 0), (600, 100, 1)]

game = Menu(punkts, punkts1)

start_collider_road = pygame.rect.Rect(282, 618,  56, 143)
mid_collider_road   = pygame.rect.Rect(466, 182,  10, 122)
start_collider_bio  = pygame.rect.Rect(872, 521, 128,  13)
mid_collider_bio    = pygame.rect.Rect(439, 421,  10, 132)

FPS      = 60
MAX_LAPS = 3


def draw_skid(skid_layer, car, color=(25, 25, 25, 150)):
    if car.is_skidding:
        cx, cy = car.rect.center
        pygame.draw.circle(skid_layer, color, (cx, cy), 3)


# Конфигурация трасс: фон, класс машины, точки спавна (x, y, угол),
# коллайдеры старта/середины. Ключи 0/1 совпадают с возвратом game.menu_1().
TRACKS = {
    0: dict(name='road', bg='road.png', car_cls=Car_road,
            spawns=[(404, 625, 270), (404, 677, 270)],
            start=start_collider_road, mid=mid_collider_road),
    1: dict(name='bio', bg='bio.png', car_cls=Car_bio,
            spawns=[(875, 535, 0), (960, 535, 0)],
            start=start_collider_bio, mid=mid_collider_bio),
}


def run_race(cfg):
    points1 = points2 = 0
    now = [0, 0]
    bg = pygame.image.load(resource(cfg['bg']))
    pygame.display.set_caption('Racing')
    (x1, y1, a1), (x2, y2, a2) = cfg['spawns']
    car1 = cfg['car_cls'](screen, x1, y1, resource('car_1.png'), a1)
    car2 = cfg['car_cls'](screen, x2, y2, resource('car_2.png'), a2)
    skid_layer = pygame.Surface((1024, 768), pygame.SRCALPHA)
    start_col, mid_col = cfg['start'], cfg['mid']

    def draw_scene():
        screen.blit(bg, (0, 0))
        screen.blit(skid_layer, (0, 0))
        car1.draw_car()
        car2.draw_car()
        controls.draw_laps(points1, points2)

    controls.countdown(draw_scene)

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                start()
                return

        screen.blit(bg, (0, 0))
        screen.blit(skid_layer, (0, 0))

        car1.move_car1()
        car2.move_car2()

        draw_skid(skid_layer, car1, (25, 20, 20, 150))
        draw_skid(skid_layer, car2, (20, 20, 30, 140))

        car1.draw_car()
        car2.draw_car()

        controls.pause()
        clock.tick(FPS)

        controls.mid_collider_handler(car1, car2, mid_col)
        points1, points2, now[0], now[1] = controls.points_counter(
            car1, car2, start_col, points1, points2, now)

        finish(points1, points2)
        pygame.display.update()


def finish(points1, points2):
    if points1 < MAX_LAPS and points2 < MAX_LAPS:
        return

    winner = 1 if points1 >= MAX_LAPS else 2
    color  = (100, 180, 255) if winner == 1 else (100, 255, 140)
    msg    = f'Игрок {winner} победил!'
    hint   = 'Нажми Enter для перезапуска'

    overlay   = pygame.Surface((1024, 768), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    font_big  = pygame.font.SysFont('arial', 90, bold=True)
    font_hint = pygame.font.SysFont('arial', 32)

    clock_local = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            break

        screen.blit(overlay, (0, 0))

        shadow = font_big.render(msg, True, (0, 0, 0))
        text   = font_big.render(msg, True, color)
        x = 512 - text.get_width() // 2
        screen.blit(shadow, (x + 5, 305))
        screen.blit(text,   (x,     300))

        hint_surf = font_hint.render(hint, True, (180, 180, 180))
        screen.blit(hint_surf, (512 - hint_surf.get_width() // 2, 420))

        pygame.display.update()
        clock_local.tick(60)

    start()


def start():
    pygame.init()
    pygame.mixer.music.load(resource('font_music.MP3'))
    pygame.mixer.music.play(-1)
    game.menu()
    choice = game.menu_1()
    run_race(TRACKS[choice])
    pygame.quit()


if __name__ == '__main__':
    start()
    pygame.quit()
