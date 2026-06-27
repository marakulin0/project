import sys
import os
from math import sin, cos, radians
import pygame
from menu import Menu
from car import Car_road, Car_bio, resolve_car_collision
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
P1_COLOR = (100, 180, 255)
P2_COLOR = (100, 255, 140)


def draw_skid(skid_layer, car, color=(25, 25, 25, 150)):
    if car.is_skidding:
        cx, cy = car.rect.center
        pygame.draw.circle(skid_layer, color, (cx, cy), 3)


def draw_boost(car):
    """Свечение позади машины, пока активно нитро."""
    if not car.boosting:
        return
    rad = radians(car.angle)
    bx = int(car.x - sin(rad) * 32)   # позади машины (минус направление вперёд)
    by = int(car.y + cos(rad) * 32)
    pygame.draw.circle(screen, (120, 210, 255), (bx, by), 6)
    pygame.draw.circle(screen, (225, 245, 255), (bx, by), 3)


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
    frame = 0                 # кадры гонки (растут только в игровом цикле)
    lap_start = [0, 0]        # кадр начала текущего круга у каждого игрока
    best = [None, None]       # лучший круг в кадрах у каждого игрока
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
        controls.draw_nitro(car1, car2)
        controls.draw_speed(car1, car2)
        controls.draw_timers(frame - lap_start[0], best[0],
                             frame - lap_start[1], best[1])

    controls.countdown(draw_scene)

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                start()
                return

        frame += 1

        screen.blit(bg, (0, 0))
        screen.blit(skid_layer, (0, 0))

        car1.move_car1()
        car2.move_car2()
        resolve_car_collision(car1, car2)

        draw_skid(skid_layer, car1, (25, 20, 20, 150))
        draw_skid(skid_layer, car2, (20, 20, 30, 140))

        draw_boost(car1)
        draw_boost(car2)
        car1.draw_car()
        car2.draw_car()

        controls.pause()
        clock.tick(FPS)

        controls.mid_collider_handler(car1, car2, mid_col)
        prev1, prev2 = points1, points2
        points1, points2, now[0], now[1] = controls.points_counter(
            car1, car2, start_col, points1, points2, now)

        # засчитан круг -> зафиксировать время, обновить лучший, сбросить отсчёт
        if points1 > prev1:
            _, best[0], lap_start[0] = controls.record_lap(frame, lap_start[0], best[0])
        if points2 > prev2:
            _, best[1], lap_start[1] = controls.record_lap(frame, lap_start[1], best[1])

        controls.draw_timers(frame - lap_start[0], best[0],
                             frame - lap_start[1], best[1])

        if points1 >= MAX_LAPS or points2 >= MAX_LAPS:
            finish({'winner': 1 if points1 >= MAX_LAPS else 2,
                    'laps': [points1, points2],
                    'best': [best[0], best[1]],
                    'total': frame})
            return

        pygame.display.update()


def _centered(font, text, y, color, shadow=False):
    surf = font.render(text, True, color)
    x = 512 - surf.get_width() // 2
    if shadow:
        screen.blit(font.render(text, True, (0, 0, 0)), (x + 4, y + 4))
    screen.blit(surf, (x, y))


def finish(results):
    """Экран результатов. results: winner, laps[2], best[2] (кадры|None), total."""
    winner = results['winner']
    wcolor = P1_COLOR if winner == 1 else P2_COLOR
    laps, best, total = results['laps'], results['best'], results['total']

    overlay = pygame.Surface((1024, 768), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    f_title = pygame.font.SysFont('arial', 78, bold=True)
    f_head  = pygame.font.SysFont('arial', 32, bold=True)
    f_row   = pygame.font.SysFont('arial', 26)
    f_total = pygame.font.SysFont('arial', 30, bold=True)
    f_hint  = pygame.font.SysFont('arial', 26)

    clock_local = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        if pygame.key.get_pressed()[pygame.K_RETURN]:
            break

        screen.blit(overlay, (0, 0))
        _centered(f_title, f'ИГРОК {winner} ПОБЕДИЛ!', 140, wcolor, shadow=True)

        for cx, pid, col in ((330, 1, P1_COLOR), (694, 2, P2_COLOR)):
            head = f_head.render(f'Игрок {pid}', True, col)
            screen.blit(head, (cx - head.get_width() // 2, 300))
            rows = [f'Круги: {min(laps[pid - 1], MAX_LAPS)}/{MAX_LAPS}',
                    f'Лучший круг: {controls._fmt_time(best[pid - 1])}']
            for i, r in enumerate(rows):
                s = f_row.render(r, True, (230, 230, 235))
                screen.blit(s, (cx - s.get_width() // 2, 352 + i * 36))

        _centered(f_total, f'Общее время: {controls._fmt_time(total)}', 452, (255, 225, 120))
        _centered(f_hint, 'Enter — играть заново', 560, (185, 185, 190))

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
