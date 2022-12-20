import pygame


screen = pygame.display.set_mode((1024, 768))
pygame.font.init()


def print_text(message, x, y, font_colour=(0, 0, 255),
               font_type='arial', font_size=70):
    font_type = pygame.font.SysFont(font_type, font_size)
    text = font_type.render(message, True, font_colour)
    screen.blit(text, (x, y))


def pause():
    paused = False
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_SPACE]:
        paused = True
    while paused:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
        print_text('Paused. Press enter to continue', 120, 300)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RETURN]:
            paused = False
        pygame.display.update()


def points_counter(car1, car2, finish, points1, points2, before):
    rect1 = car1.rect
    rect2 = car2.rect
    now = [1, 1]
    if not before[0]:
        if pygame.rect.Rect.colliderect(rect1, finish) and\
             car1.ready_to_finish:
            points1 += 1
            now[0] = 1
            car1.ready_to_finish = False
        else:
            now[0] = 0
    else:
        if not pygame.rect.Rect.colliderect(rect1, finish):
            now[0] = 0
    if not before[1]:
        if pygame.rect.Rect.colliderect(rect2, finish) and\
             car2.ready_to_finish:
            points2 += 1
            now[1] = 1
            car2.ready_to_finish = False
        else:
            now[1] = 0
    else:
        if not pygame.rect.Rect.colliderect(rect2, finish):
            now[1] = 0
    print_text('Кругов:'+str(points1), 10, 10)
    print_text('Кругов:'+str(points2), 800, 10)
    return points1, points2, *now


def mid_collider_handler(car1, car2, mid):
    rect1 = car1.rect
    rect2 = car2.rect
    if pygame.rect.Rect.colliderect(rect1, mid):
        car1.ready_to_finish = True
    if pygame.rect.Rect.colliderect(rect2, mid):
        car2.ready_to_finish = True
