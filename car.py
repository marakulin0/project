"""Физика машин — аркадная модель top-down гонок.

Ключевые принципы (в отличие от старой версии):
  * координаты хранятся как float (self.x/self.y), rect синхронизируется
    каждый кадр — нет дёрганья от целочисленного округления;
  * скорость измеряется в пикселях за кадр (реальный масштаб, а не ~0.4 px);
  * руль чувствителен сразу, доводчик чувствительности только на самой
    малой скорости (нельзя крутиться на месте);
  * столкновения разрешаются по осям (X, затем Y) через отдельный квадратный
    хитбокс — машина скользит вдоль стены, а не снапится к 0/90/180°.
"""

import pygame
from collections import namedtuple
from math import sin, cos, radians

# Единый формат ввода для машины. Физика принимает Input, а не читает
# клавиатуру сама — это позволяет одному коду работать локально, на хосте
# и на клиенте (фаза 7, сеть). Поле boost задействуется на фазе нитро.
Input = namedtuple('Input', ['gas', 'brake', 'left', 'right', 'boost'],
                   defaults=[False])


def _clamp(value, low, high):
    return low if value < low else high if value > high else value


class BaseCar():

    # --- настройки, переопределяются в подклассах ---
    ACCEL = 0.16          # разгон, px/кадр²
    BRAKE = 0.34          # торможение при движении вперёд
    REVERSE_ACCEL = 0.11  # набор задней скорости
    MAX_SPEED = 4.6       # максимальная скорость вперёд, px/кадр
    MAX_REVERSE = 2.0     # максимальная задняя скорость
    ROLL = 0.975          # трение качения на накате
    TURN_SPEED = 3.4      # град/кадр на полной скорости
    TURN_FULL_AT = 2.2    # скорость, при которой руль работает на 100%
    WALL_BOUNCE = 0.30    # доля скорости, сохраняемая после удара о стену
    HITBOX = 26           # сторона квадратного хитбокса для стен
    SKID_SPEED = 2.8      # порог скорости для следов шин
    rects = []            # список стен трассы (Rect)

    def __init__(self, screen, x0, y0, filename, start_angle=0.0):
        self.screen = screen
        base = pygame.transform.scale(pygame.image.load(filename), (32, 70))
        self.base_image = base
        self.image_to_draw = base
        # x0/y0 приходят как левый-верхний угол — переводим в центр
        self.x = float(x0 + 16)
        self.y = float(y0 + 35)
        # курс в градусах: 0 = нос вверх, 90 = вправо (восток), 270 = влево (запад)
        self.angle = float(start_angle)
        self.speed = 0.0       # знаковая скорость вдоль курса
        self.steering = 0.0    # текущее положение руля (-1..1) для скида
        self.ready_to_finish = False
        self.image_to_draw = pygame.transform.rotate(base, -self.angle)
        self.rect = self.image_to_draw.get_rect(center=(round(self.x), round(self.y)))
        self.hitbox = pygame.Rect(0, 0, self.HITBOX, self.HITBOX)
        self.hitbox.center = (round(self.x), round(self.y))

    @property
    def is_skidding(self):
        return abs(self.speed) > self.SKID_SPEED and abs(self.steering) > 0.1

    def draw_car(self):
        self.screen.blit(self.image_to_draw, self.rect)

    def update(self, inp):
        # --- продольная динамика ---
        if inp.gas:
            self.speed += self.ACCEL
        elif inp.brake:
            if self.speed > 0:
                self.speed -= self.BRAKE
            else:
                self.speed -= self.REVERSE_ACCEL
        else:
            self.speed *= self.ROLL
        self.speed = _clamp(self.speed, -self.MAX_REVERSE, self.MAX_SPEED)

        # --- поворот: чувствительность растёт со скоростью, в реверсе руль
        #     инвертируется (как при сдаче назад на реальной машине) ---
        self.steering = (-1.0 if inp.left else 0.0) + (1.0 if inp.right else 0.0)
        ratio = min(1.0, abs(self.speed) / self.TURN_FULL_AT)
        direction = 1.0 if self.speed >= 0 else -1.0
        self.angle += self.steering * self.TURN_SPEED * ratio * direction

        # --- интегрирование позиции вдоль курса ---
        rad = radians(self.angle)
        dx = sin(rad) * self.speed
        dy = -cos(rad) * self.speed
        self._move_axis(dx, 0.0)
        self._move_axis(0.0, dy)

        # --- отрисовочный спрайт ---
        self.image_to_draw = pygame.transform.rotate(self.base_image, -self.angle)
        self.rect = self.image_to_draw.get_rect(center=(round(self.x), round(self.y)))

    def _move_axis(self, dx, dy):
        """Двигает по одной оси и гасит её при упоре в стену (скольжение)."""
        self.x += dx
        self.y += dy
        self.hitbox.center = (round(self.x), round(self.y))
        for wall in self.rects:
            if self.hitbox.colliderect(wall):
                if dx > 0:
                    self.hitbox.right = wall.left
                elif dx < 0:
                    self.hitbox.left = wall.right
                if dy > 0:
                    self.hitbox.bottom = wall.top
                elif dy < 0:
                    self.hitbox.top = wall.bottom
                self.x = float(self.hitbox.centerx)
                self.y = float(self.hitbox.centery)
                self.speed *= self.WALL_BOUNCE
                break

    def move_car1(self):
        """Локальный адаптер клавиатуры для игрока 1 (WASD + Left Shift)."""
        k = pygame.key.get_pressed()
        self.update(Input(k[pygame.K_w], k[pygame.K_s],
                          k[pygame.K_a], k[pygame.K_d], k[pygame.K_LSHIFT]))

    def move_car2(self):
        """Локальный адаптер клавиатуры для игрока 2 (стрелки + Right Shift)."""
        k = pygame.key.get_pressed()
        self.update(Input(k[pygame.K_UP], k[pygame.K_DOWN],
                          k[pygame.K_LEFT], k[pygame.K_RIGHT], k[pygame.K_RSHIFT]))

    def collision_handing(self, rects):
        # столкновения теперь разрешаются внутри движения;
        # метод оставлен для совместимости с racing.py
        pass


class Car_road(BaseCar):
    """Техничная трасса с узкими коридорами — машина чуть медленнее и цепче."""

    ACCEL = 0.15
    MAX_SPEED = 4.2
    TURN_SPEED = 3.5

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


class Car_bio(BaseCar):
    """Открытая трасса — выше скорость, чуть больше инерция в поворотах."""

    ACCEL = 0.17
    MAX_SPEED = 4.8
    TURN_SPEED = 3.2

    rects = [pygame.rect.Rect(0, 0, 12, 768),
             pygame.rect.Rect(10, 0, 1014, 12),
             pygame.rect.Rect(1015, 13, 12, 758),
             pygame.rect.Rect(13, 757, 1004, 12)]
