import pygame
from math import sin, cos, pi

DRIFT = 0.76        # инерция: чем выше, тем больше скольжение
TURN_RATE = 0.038   # базовая чувствительность поворота


class Car_road():

    def __init__(self, screen, x0, y0, filename):
        self.screen = screen
        car_image_load = pygame.image.load(filename)
        car_image_scaled = pygame.transform.scale(car_image_load, (32, 70))
        self.image = pygame.transform.rotate(car_image_scaled, 90.0)
        self.image_to_draw = self.image
        self.rect = self.image.get_rect()
        self.rect.x = x0
        self.rect.y = y0
        self.speed = 0
        self.vx = 0.0       # фактическая скорость по X (с инерцией)
        self.vy = 0.0       # фактическая скорость по Y (с инерцией)
        self.acceleration = -0.015
        self.max_speed = 0.42
        self.angle = 0
        self.ready_to_finish = False

    def draw_car(self):
        self.screen.blit(self.image_to_draw, self.rect)

    @property
    def is_skidding(self):
        return abs(self.speed) > 0.18

    def _move(self, keys, fwd, back, left, right):
        if keys[fwd]:
            self.speed += self.acceleration
        elif keys[back]:
            self.speed -= self.acceleration

        # Ограничение максимальной скорости
        if self.speed < -self.max_speed:
            self.speed = -self.max_speed
        if self.speed > self.max_speed:
            self.speed = self.max_speed

        # Угловая скорость зависит от скорости: стоя поворот невозможен,
        # на высокой скорости — уменьшенный grip (машина хуже слушается)
        speed_abs = abs(self.speed)
        speed_factor = min(1.0, speed_abs / 0.06)
        grip = max(0.5, 1.0 - (speed_abs - 0.22) * 1.4) if speed_abs > 0.22 else 1.0
        tr = TURN_RATE * speed_factor * grip

        if keys[left]:
            self.angle += tr
        if keys[right]:
            self.angle -= tr

        # Торможение за счёт трения
        if not (keys[fwd] or keys[back]):
            self.speed *= 0.93

        # Инерция: плавно сближаем скорость с текущим направлением взгляда
        tx = self.speed * cos(self.angle)
        ty = -self.speed * sin(self.angle)
        self.vx = self.vx * DRIFT + tx * (1 - DRIFT)
        self.vy = self.vy * DRIFT + ty * (1 - DRIFT)

        self.image_to_draw = pygame.transform.rotate(self.image, self.angle / pi * 180)
        self.rect = self.image_to_draw.get_rect(center=self.rect.center)
        self.rect.x += self.vx
        self.rect.y += self.vy

    def move_car1(self):
        self._move(pygame.key.get_pressed(),
                   pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d)

    def move_car2(self):
        self._move(pygame.key.get_pressed(),
                   pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)

    rects = [pygame.rect.Rect(0, 0, 9, 768),
             pygame.rect.Rect(10, 0, 1014, 9),
             pygame.rect.Rect(1015, 10, 9, 758),
             pygame.rect.Rect(10, 757, 1004, 9),
             pygame.rect.Rect(787, 276, 131, 79),
             pygame.rect.Rect(465, 10, 18, 163),
             pygame.rect.Rect(339, 446, 677, 18),
             pygame.rect.Rect(160, 144, 173, 18),
             pygame.rect.Rect(637, 144, 250, 18),
             pygame.rect.Rect(160, 159, 18, 459),
             pygame.rect.Rect(178, 306, 461, 18),
             pygame.rect.Rect(178, 600, 675, 18),
             pygame.rect.Rect(636, 145, 18, 162)]

    def collision_handing(self, rects):
        for i in rects:
            if pygame.rect.Rect.colliderect(self.rect, i):
                if cos(self.angle) < -0.01:
                    deltax = self.rect.right - i.left - cos(self.angle) * abs(self.speed)
                elif cos(self.angle) > 0.01:
                    deltax = i.right - self.rect.left + cos(self.angle) * abs(self.speed)
                else:
                    deltax = 2 * abs(self.speed)
                if sin(self.angle) < 0:
                    deltay = i.bottom - self.rect.top + sin(self.angle) * self.speed
                else:
                    deltay = self.rect.bottom - sin(self.angle) * self.speed - i.top
                if deltax < 2 * abs(self.speed):
                    if sin(self.angle) > 0:
                        self.angle = pi / 2
                    elif sin(self.angle) < 0:
                        self.angle = -pi / 2
                    else:
                        self.speed = 0
                    self.speed *= 0.2
                    self.vx *= 0.2
                    self.vy *= 0.2
                if deltay < 2 * abs(self.speed):
                    if cos(self.angle) > 0:
                        self.angle = 0
                    elif cos(self.angle) < 0:
                        self.angle = pi
                    else:
                        self.speed = 0
                    self.speed *= 0.2
                    self.vx *= 0.2
                    self.vy *= 0.2


class Car_bio():

    def __init__(self, screen, x0, y0, filename):
        self.screen = screen
        car_image_load = pygame.image.load(filename)
        self.image = pygame.transform.scale(car_image_load, (32, 70))
        self.image_to_draw = self.image
        self.rect = self.image.get_rect()
        self.rect.x = x0
        self.rect.y = y0
        self.speed = 0
        self.vx = 0.0
        self.vy = 0.0
        self.acceleration = -0.01
        self.max_speed = 0.34
        self.angle = 0
        self.ready_to_finish = False

    def draw_car(self):
        self.screen.blit(self.image_to_draw, self.rect)

    @property
    def is_skidding(self):
        return abs(self.speed) > 0.13

    def _move(self, keys, fwd, back, left, right):
        if keys[fwd]:
            self.speed += self.acceleration
        elif keys[back]:
            self.speed -= self.acceleration

        if self.speed < -self.max_speed:
            self.speed = -self.max_speed
        if self.speed > self.max_speed:
            self.speed = self.max_speed

        speed_abs = abs(self.speed)
        speed_factor = min(1.0, speed_abs / 0.05)
        grip = max(0.5, 1.0 - (speed_abs - 0.18) * 1.4) if speed_abs > 0.18 else 1.0
        tr = TURN_RATE * speed_factor * grip

        if keys[left]:
            self.angle += tr
        if keys[right]:
            self.angle -= tr

        if not (keys[fwd] or keys[back]):
            self.speed *= 0.93

        # Car_bio использует другую ось координат
        tx = self.speed * sin(self.angle)
        ty = self.speed * cos(self.angle)
        self.vx = self.vx * DRIFT + tx * (1 - DRIFT)
        self.vy = self.vy * DRIFT + ty * (1 - DRIFT)

        self.image_to_draw = pygame.transform.rotate(self.image, self.angle / pi * 180)
        self.rect = self.image_to_draw.get_rect(center=self.rect.center)
        self.rect.x += self.vx
        self.rect.y += self.vy

    def move_car1(self):
        self._move(pygame.key.get_pressed(),
                   pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d)

    def move_car2(self):
        self._move(pygame.key.get_pressed(),
                   pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)

    rects = [pygame.rect.Rect(0, 0, 12, 768),
             pygame.rect.Rect(10, 0, 1014, 12),
             pygame.rect.Rect(1015, 13, 12, 758),
             pygame.rect.Rect(13, 757, 1004, 12)]

    def collision_handing(self, rects):
        for i in rects:
            if pygame.rect.Rect.colliderect(self.rect, i):
                if cos(self.angle) < -0.01:
                    deltax = self.rect.right - i.left - cos(self.angle) * abs(self.speed)
                elif cos(self.angle) > 0.01:
                    deltax = i.right - self.rect.left + cos(self.angle) * abs(self.speed)
                else:
                    deltax = 2 * abs(self.speed)
                if sin(self.angle) < 0:
                    deltay = i.bottom - self.rect.top + sin(self.angle) * self.speed
                else:
                    deltay = self.rect.bottom - sin(self.angle) * self.speed - i.top
                if deltax < 2 * abs(self.speed):
                    if sin(self.angle) > 0:
                        self.angle = pi / 2
                    elif sin(self.angle) < 0:
                        self.angle = -pi / 2
                    else:
                        self.speed = 0
                    self.speed *= 0.2
                    self.vx *= 0.2
                    self.vy *= 0.2
                if deltay < 2 * abs(self.speed):
                    if cos(self.angle) > 0:
                        self.angle = 0
                    elif cos(self.angle) < 0:
                        self.angle = pi
                    else:
                        self.speed = 0
                    self.speed *= 0.1
                    self.vx *= 0.1
                    self.vy *= 0.1
