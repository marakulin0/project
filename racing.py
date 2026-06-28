import sys
import os
from math import sin, cos, radians
import pygame
from menu import Menu
from car import Car_road, Car_bio, resolve_car_collision, Input
import controls
import online


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


def _draw_results(results):
    """Один кадр экрана результатов (без flip). results: winner, laps[2],
    best[2] (кадры|None), total (кадры)."""
    winner = results['winner']
    wcolor = P1_COLOR if winner == 1 else P2_COLOR
    laps, best, total = results['laps'], results['best'], results['total']

    overlay = pygame.Surface((1024, 768), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))
    _centered(pygame.font.SysFont('arial', 78, bold=True),
              f'ИГРОК {winner} ПОБЕДИЛ!', 140, wcolor, shadow=True)

    f_head = pygame.font.SysFont('arial', 32, bold=True)
    f_row  = pygame.font.SysFont('arial', 26)
    for cx, pid, col in ((330, 1, P1_COLOR), (694, 2, P2_COLOR)):
        head = f_head.render(f'Игрок {pid}', True, col)
        screen.blit(head, (cx - head.get_width() // 2, 300))
        rows = [f'Круги: {min(laps[pid - 1], MAX_LAPS)}/{MAX_LAPS}',
                f'Лучший круг: {controls._fmt_time(best[pid - 1])}']
        for i, r in enumerate(rows):
            s = f_row.render(r, True, (230, 230, 235))
            screen.blit(s, (cx - s.get_width() // 2, 352 + i * 36))

    _centered(pygame.font.SysFont('arial', 30, bold=True),
              f'Общее время: {controls._fmt_time(total)}', 452, (255, 225, 120))
    _centered(pygame.font.SysFont('arial', 26),
              'Enter — играть заново', 560, (185, 185, 190))


def finish(results):
    clock_local = pygame.time.Clock()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        if pygame.key.get_pressed()[pygame.K_RETURN]:
            break
        _draw_results(results)
        pygame.display.update()
        clock_local.tick(60)
    start()


# --------------------------- онлайн (LAN PvP) ---------------------------

def _blit_cd_number(label, color, alpha=255):
    font = pygame.font.SysFont('arial', 150 if label == 'GO!' else 200, bold=True)
    surf = font.render(label, True, color)
    surf.set_alpha(alpha)
    sh = font.render(label, True, (0, 0, 0))
    sh.set_alpha(alpha // 2)
    cx = 512 - surf.get_width() // 2
    cy = 384 - surf.get_height() // 2
    screen.blit(sh, (cx + 6, cy + 6))
    screen.blit(surf, (cx, cy))


def _build_state(phase, cd, track, c1, c2, p1, p2, best, lap_start, frame, winner):
    """Авторитетное состояние гонки (хост -> клиент), JSON-сериализуемое."""
    return {
        'ph': phase, 'cd': cd, 'track': track,
        'cars': [[round(c1.x, 1), round(c1.y, 1), round(c1.angle, 1),
                  round(c1.nitro, 3), c1.boosting],
                 [round(c2.x, 1), round(c2.y, 1), round(c2.angle, 1),
                  round(c2.nitro, 3), c2.boosting]],
        'laps': [p1, p2], 'best': best,
        'cur': [frame - lap_start[0], frame - lap_start[1]],
        'spd': [round(abs(c1.speed), 3), round(abs(c2.speed), 3)],
        'win': winner, 'total': frame,
    }


def _apply_state(cars, st):
    """Клиент: расставляет машины и HUD-поля по присланному состоянию."""
    for car, cs in zip(cars, st['cars']):
        x, y, ang, nit, boost = cs
        car.x, car.y, car.angle = x, y, ang
        car.nitro, car.boosting = nit, boost
        car.image_to_draw = pygame.transform.rotate(car.base_image, -ang)
        car.rect = car.image_to_draw.get_rect(center=(round(x), round(y)))
    cars[0].speed = st['spd'][0]
    cars[1].speed = st['spd'][1]


def _net_lost():
    clk = pygame.time.Clock()
    f_big = pygame.font.SysFont('arial', 54, bold=True)
    f_sub = pygame.font.SysFont('arial', 26)
    for _ in range(150):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                quit()
            if e.type == pygame.KEYDOWN:
                return start()
        screen.fill((12, 12, 16))
        _centered(f_big, 'Соединение потеряно', 300, (235, 90, 80), shadow=True)
        _centered(f_sub, 'Любая клавиша — в меню', 380, (185, 185, 190))
        pygame.display.update()
        clk.tick(60)
    start()


def run_online(cfg, role, ch):
    if role == 'host':
        _run_host(cfg, ch)
    else:
        _run_client(ch)


def _run_host(cfg, ch):
    """Хост-авторитет: считает обе машины, рассылает состояние, играет за P1."""
    track = 0 if cfg['name'] == 'road' else 1
    bg = pygame.image.load(resource(cfg['bg']))
    pygame.display.set_caption('Racing — Host (Игрок 1)')
    (x1, y1, a1), (x2, y2, a2) = cfg['spawns']
    car1 = cfg['car_cls'](screen, x1, y1, resource('car_1.png'), a1)
    car2 = cfg['car_cls'](screen, x2, y2, resource('car_2.png'), a2)
    skid = pygame.Surface((1024, 768), pygame.SRCALPHA)
    start_col, mid_col = cfg['start'], cfg['mid']
    p1 = p2 = 0
    now = [0, 0]
    frame = 0
    lap_start = [0, 0]
    best = [None, None]

    # обратный отсчёт: хост рисует локально и рассылает cd-состояние
    cd_clock = pygame.time.Clock()
    for label, color in (('3', (220, 60, 60)), ('2', (220, 160, 40)),
                         ('1', (240, 220, 40)), ('GO!', (60, 220, 80))):
        for f in range(60):
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    ch.close()
                    pygame.quit()
                    quit()
            screen.blit(bg, (0, 0))
            car1.draw_car()
            car2.draw_car()
            controls.draw_laps(0, 0)
            controls.draw_nitro(car1, car2)
            controls.draw_speed(car1, car2)
            controls.draw_timers(0, None, 0, None)
            _blit_cd_number(label, color, min(255, f * 9))
            pygame.display.update()
            ch.send(_build_state('cd', label, track, car1, car2, 0, 0,
                                 [None, None], [0, 0], 0, 0))
            if not ch.alive:
                return _net_lost()
            cd_clock.tick(60)

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                ch.close()
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                ch.close()
                return start()
        frame += 1

        k = pygame.key.get_pressed()
        in1 = Input(k[pygame.K_w], k[pygame.K_s], k[pygame.K_a], k[pygame.K_d],
                    k[pygame.K_LSHIFT])
        msg = ch.latest()
        in2 = (Input(msg.get('g', False), msg.get('b', False), msg.get('l', False),
                     msg.get('r', False), msg.get('n', False)) if msg
               else Input(False, False, False, False, False))

        screen.blit(bg, (0, 0))
        screen.blit(skid, (0, 0))
        car1.update(in1)
        car2.update(in2)
        resolve_car_collision(car1, car2)
        draw_skid(skid, car1, (25, 20, 20, 150))
        draw_skid(skid, car2, (20, 20, 30, 140))
        draw_boost(car1)
        draw_boost(car2)
        car1.draw_car()
        car2.draw_car()
        clock.tick(FPS)

        controls.mid_collider_handler(car1, car2, mid_col)
        prev1, prev2 = p1, p2
        p1, p2, now[0], now[1] = controls.points_counter(car1, car2, start_col, p1, p2, now)
        if p1 > prev1:
            _, best[0], lap_start[0] = controls.record_lap(frame, lap_start[0], best[0])
        if p2 > prev2:
            _, best[1], lap_start[1] = controls.record_lap(frame, lap_start[1], best[1])
        controls.draw_timers(frame - lap_start[0], best[0], frame - lap_start[1], best[1])

        winner = 1 if p1 >= MAX_LAPS else (2 if p2 >= MAX_LAPS else 0)
        ch.send(_build_state('race', '', track, car1, car2, p1, p2, best, lap_start, frame, winner))
        if not ch.alive:
            return _net_lost()
        pygame.display.update()

        if winner:
            res = {'winner': winner, 'laps': [p1, p2],
                   'best': [best[0], best[1]], 'total': frame}
            fin_clock = pygame.time.Clock()
            while True:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        ch.close()
                        pygame.quit()
                        quit()
                if pygame.key.get_pressed()[pygame.K_RETURN]:
                    break
                _draw_results(res)
                pygame.display.update()
                ch.send(_build_state('fin', '', track, car1, car2, p1, p2,
                                     best, lap_start, frame, winner))
                fin_clock.tick(60)
            ch.close()
            return start()


def _run_client(ch):
    """Клиент: шлёт свой ввод (P2), отрисовывает состояние от хоста."""
    pygame.display.set_caption('Racing — Client (Игрок 2)')
    cfg = bg = cars = None
    wait_font = pygame.font.SysFont('arial', 40, bold=True)
    clk = pygame.time.Clock()

    while cars is None:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                ch.close()
                pygame.quit()
                quit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                ch.close()
                return start()
        st = ch.latest()
        if st and 'track' in st:
            cfg = TRACKS[st['track']]
            bg = pygame.image.load(resource(cfg['bg']))
            (x1, y1, a1), (x2, y2, a2) = cfg['spawns']
            cars = [cfg['car_cls'](screen, x1, y1, resource('car_1.png'), a1),
                    cfg['car_cls'](screen, x2, y2, resource('car_2.png'), a2)]
            break
        screen.fill((10, 10, 15))
        _centered(wait_font, 'Ожидание данных от хоста...', 330, (240, 230, 90))
        pygame.display.update()
        if not ch.alive:
            return _net_lost()
        clk.tick(60)

    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                ch.close()
                pygame.quit()
                quit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                ch.close()
                return start()
        k = pygame.key.get_pressed()
        ch.send({'g': bool(k[pygame.K_w] or k[pygame.K_UP]),
                 'b': bool(k[pygame.K_s] or k[pygame.K_DOWN]),
                 'l': bool(k[pygame.K_a] or k[pygame.K_LEFT]),
                 'r': bool(k[pygame.K_d] or k[pygame.K_RIGHT]),
                 'n': bool(k[pygame.K_LSHIFT] or k[pygame.K_RSHIFT])})
        if not ch.alive:
            return _net_lost()
        st = ch.latest()
        if not st:
            clk.tick(60)
            continue

        _apply_state(cars, st)
        screen.blit(bg, (0, 0))
        draw_boost(cars[0])
        draw_boost(cars[1])
        cars[0].draw_car()
        cars[1].draw_car()
        controls.draw_laps(st['laps'][0], st['laps'][1])
        controls.draw_nitro(cars[0], cars[1])
        controls.draw_speed(cars[0], cars[1])
        controls.draw_timers(st['cur'][0], st['best'][0], st['cur'][1], st['best'][1])

        if st.get('ph') == 'cd':
            cd = st.get('cd', '3')
            _blit_cd_number(cd, (60, 220, 80) if cd == 'GO!' else (240, 230, 90))
        elif st.get('ph') == 'fin':
            _draw_results({'winner': st['win'], 'laps': st['laps'],
                           'best': st['best'], 'total': st['total']})
            if pygame.key.get_pressed()[pygame.K_RETURN]:
                ch.close()
                return start()
        pygame.display.update()
        clk.tick(FPS)


def start():
    pygame.init()
    pygame.mixer.music.load(resource('font_music.MP3'))
    pygame.mixer.music.play(-1)
    game.menu()
    mode = online.mode_menu()
    if mode == 'local':
        run_race(TRACKS[game.menu_1()])
    elif mode == 'host':
        ch = online.host_lobby()
        if ch is None:
            return start()
        run_online(TRACKS[game.menu_1()], 'host', ch)
    elif mode == 'join':
        ip = online.ip_entry()
        if ip is None:
            return start()
        ch = online.client_lobby(ip)
        if ch is None:
            return start()
        run_online(None, 'client', ch)
    pygame.quit()


if __name__ == '__main__':
    start()
    pygame.quit()
