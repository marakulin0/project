import pygame

screen = pygame.display.set_mode((1024, 768))
pygame.font.init()

MAX_LAPS = 3
SPEED_SCALE = 40   # px/кадр -> условные км/ч на спидометре


def print_text(message, x, y, font_colour=(255, 255, 255),
               font_type='arial', font_size=70):
    font = pygame.font.SysFont(font_type, font_size)
    shadow = font.render(message, True, (0, 0, 0))
    screen.blit(shadow, (x + 2, y + 2))
    text = font.render(message, True, font_colour)
    screen.blit(text, (x, y))


def draw_laps(p1, p2):
    font = pygame.font.SysFont('arial', 20, bold=True)

    # Игрок 1 — верхний левый угол
    label = font.render('P1', True, (220, 220, 220))
    screen.blit(label, (10, 10))
    for i in range(MAX_LAPS):
        color = (80, 210, 80) if i < p1 else (50, 50, 50)
        pygame.draw.circle(screen, color, (55 + i * 26, 20), 9)
        pygame.draw.circle(screen, (180, 180, 180), (55 + i * 26, 20), 9, 1)

    # Игрок 2 — верхний правый угол
    label2 = font.render('P2', True, (220, 220, 220))
    screen.blit(label2, (875, 10))
    for i in range(MAX_LAPS):
        color = (80, 140, 255) if i < p2 else (50, 50, 50)
        pygame.draw.circle(screen, color, (930 + i * 26, 20), 9)
        pygame.draw.circle(screen, (180, 180, 180), (930 + i * 26, 20), 9, 1)


def _nitro_bar(x, y, value, boosting):
    w, h = 130, 14
    pygame.draw.rect(screen, (28, 28, 38), (x, y, w, h), border_radius=3)
    fill = int((w - 4) * value)
    if value < 0.2:
        col = (230, 70, 60)
    elif boosting:
        col = (130, 235, 255)
    else:
        col = (60, 170, 230)
    if fill > 0:
        pygame.draw.rect(screen, col, (x + 2, y + 2, fill, h - 4), border_radius=2)
    pygame.draw.rect(screen, (160, 160, 175), (x, y, w, h), 1, border_radius=3)


def draw_nitro(car1, car2):
    font = pygame.font.SysFont('arial', 12, bold=True)
    screen.blit(font.render('NITRO', True, (200, 200, 210)), (10, 32))
    _nitro_bar(10, 46, car1.nitro, car1.boosting)
    lbl = font.render('NITRO', True, (200, 200, 210))
    screen.blit(lbl, (1014 - lbl.get_width(), 32))
    _nitro_bar(1014 - 130, 46, car2.nitro, car2.boosting)


def draw_speed(car1, car2):
    font = pygame.font.SysFont('arial', 20, bold=True)
    for car, right_edge, left_align in ((car1, None, True), (car2, 1014, False)):
        text = f'{int(abs(car.speed) * SPEED_SCALE)} км/ч'
        col = (130, 235, 255) if car.boosting else (235, 235, 240)
        surf = font.render(text, True, col)
        x = 10 if left_align else right_edge - surf.get_width()
        screen.blit(font.render(text, True, (0, 0, 0)), (x + 1, 65))
        screen.blit(surf, (x, 64))


def _fmt_time(frames):
    """Кадры -> строка времени: '12.4' или '1:05.3'. None -> '--.-'."""
    if frames is None:
        return '--.-'
    sec = frames / 60.0
    m, s = divmod(sec, 60)
    return f'{int(m)}:{s:04.1f}' if m >= 1 else f'{s:.1f}'


def record_lap(frame, lap_start, best):
    """Засчитан круг: возвращает (время_круга, новый_лучший, новый_lap_start)."""
    lap = frame - lap_start
    new_best = lap if best is None else min(best, lap)
    return lap, new_best, frame


def draw_timers(cur1, best1, cur2, best2):
    font = pygame.font.SysFont('arial', 15, bold=True)
    for cur, best, left in ((cur1, best1, True), (cur2, best2, False)):
        lines = [f'КРУГ {_fmt_time(cur)}', f'ЛУЧШИЙ {_fmt_time(best)}']
        for i, line in enumerate(lines):
            surf = font.render(line, True, (235, 235, 240))
            x = 10 if left else 1014 - surf.get_width()
            y = 90 + i * 17
            screen.blit(font.render(line, True, (0, 0, 0)), (x + 1, y + 1))
            screen.blit(surf, (x, y))


def countdown(draw_scene):
    """draw_scene() — колбэк, рисующий фон, машины и HUD под цифрой отсчёта."""
    font_big = pygame.font.SysFont('arial', 200, bold=True)
    font_go  = pygame.font.SysFont('arial', 150, bold=True)
    clock = pygame.time.Clock()

    items = [
        ('3',   (220,  60,  60)),
        ('2',   (220, 160,  40)),
        ('1',   (240, 220,  40)),
        ('GO!', ( 60, 220,  80)),
    ]

    for label, color in items:
        font = font_go if label == 'GO!' else font_big
        for frame in range(60):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()

            alpha = min(255, frame * 9)
            text_surf = font.render(label, True, color)
            text_surf.set_alpha(alpha)
            shadow_surf = font.render(label, True, (0, 0, 0))
            shadow_surf.set_alpha(alpha // 2)

            draw_scene()
            cx = 512 - text_surf.get_width() // 2
            cy = 384 - text_surf.get_height() // 2
            screen.blit(shadow_surf, (cx + 6, cy + 6))
            screen.blit(text_surf, (cx, cy))
            pygame.display.update()
            clock.tick(60)


def pause():
    pressed = pygame.key.get_pressed()
    if not pressed[pygame.K_SPACE]:
        return
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        print_text('Пауза  —  Enter для продолжения', 140, 320,
                   font_colour=(240, 220, 60), font_size=48)
        pygame.display.update()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            break


def points_counter(car1, car2, finish, points1, points2, before):
    rect1 = car1.rect
    rect2 = car2.rect
    now = [1, 1]
    if not before[0]:
        if pygame.rect.Rect.colliderect(rect1, finish) and car1.ready_to_finish:
            points1 += 1
            now[0] = 1
            car1.ready_to_finish = False
        else:
            now[0] = 0
    else:
        if not pygame.rect.Rect.colliderect(rect1, finish):
            now[0] = 0
    if not before[1]:
        if pygame.rect.Rect.colliderect(rect2, finish) and car2.ready_to_finish:
            points2 += 1
            now[1] = 1
            car2.ready_to_finish = False
        else:
            now[1] = 0
    else:
        if not pygame.rect.Rect.colliderect(rect2, finish):
            now[1] = 0
    draw_laps(points1, points2)
    draw_nitro(car1, car2)
    draw_speed(car1, car2)
    return points1, points2, *now


def mid_collider_handler(car1, car2, mid):
    if pygame.rect.Rect.colliderect(car1.rect, mid):
        car1.ready_to_finish = True
    if pygame.rect.Rect.colliderect(car2.rect, mid):
        car2.ready_to_finish = True
