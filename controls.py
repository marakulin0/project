import pygame

screen = pygame.display.set_mode((1024, 768))
pygame.font.init()

MAX_LAPS = 3


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
    return points1, points2, *now


def mid_collider_handler(car1, car2, mid):
    if pygame.rect.Rect.colliderect(car1.rect, mid):
        car1.ready_to_finish = True
    if pygame.rect.Rect.colliderect(car2.rect, mid):
        car2.ready_to_finish = True
