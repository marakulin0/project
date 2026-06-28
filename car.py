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
    HALF_W = 15           # половина ширины кузова (для OBB-коллизии машин)
    HALF_L = 32           # половина длины кузова (для OBB-коллизии машин)
    COLLISION_BOUNCE = 0.55  # доля скорости после столкновения машин
    NITRO_MULT = 1.45     # множитель максимальной скорости при нитро
    NITRO_ACCEL = 1.8     # множитель ускорения при нитро
    NITRO_DRAIN = 1 / 120.0    # расход заряда в кадр (полный бак ~2 c)
    NITRO_RECHARGE = 1 / 420.0  # подзарядка в кадр (полный бак ~7 c)
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
        self.nitro = 1.0       # заряд нитро (0..1)
        self.boosting = False  # активно ли нитро в этом кадре
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

    def draw_skid(self, layer, color):
        """Оставляет след шин на слое layer при заносе."""
        if self.is_skidding:
            pygame.draw.circle(layer, color, self.rect.center, 3)

    def draw_boost(self, surface=None):
        """Свечение позади машины, пока активно нитро."""
        if not self.boosting:
            return
        surface = surface if surface is not None else self.screen
        rad = radians(self.angle)
        bx = int(self.x - sin(rad) * 32)   # позади машины (минус курс)
        by = int(self.y + cos(rad) * 32)
        pygame.draw.circle(surface, (120, 210, 255), (bx, by), 6)
        pygame.draw.circle(surface, (225, 245, 255), (bx, by), 3)

    def update(self, inp):
        # --- нитро активно при зажатой клавише, наличии заряда и газе вперёд ---
        self.boosting = bool(inp.boost) and self.nitro > 0 and inp.gas

        # --- продольная динамика ---
        if inp.gas:
            self.speed += self.ACCEL * (self.NITRO_ACCEL if self.boosting else 1.0)
        elif inp.brake:
            if self.speed > 0:
                self.speed -= self.BRAKE
            else:
                self.speed -= self.REVERSE_ACCEL
        else:
            self.speed *= self.ROLL

        # верхний предел: при нитро потолок выше; после нитро скорость плавно
        # спадает к обычному максимуму, а не обрезается резко
        ceiling = self.MAX_SPEED * (self.NITRO_MULT if self.boosting else 1.0)
        if self.speed > ceiling:
            self.speed = max(ceiling, self.speed * 0.96)
        if self.speed < -self.MAX_REVERSE:
            self.speed = -self.MAX_REVERSE

        # --- расход / подзарядка заряда нитро (подзарядка только когда
        #     клавиша отпущена — нельзя «дозаряжаться», удерживая нитро) ---
        if self.boosting:
            self.nitro = max(0.0, self.nitro - self.NITRO_DRAIN)
        elif not inp.boost:
            self.nitro = min(1.0, self.nitro + self.NITRO_RECHARGE)

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

    def _depenetrate_walls(self):
        """Выталкивает машину из любой перекрытой стены по оси наименьшего
        проникновения (используется после толчка машина-машина)."""
        for wall in self.rects:
            if self.hitbox.colliderect(wall):
                push_right = wall.right - self.hitbox.left
                push_left  = self.hitbox.right - wall.left
                push_down  = wall.bottom - self.hitbox.top
                push_up    = self.hitbox.bottom - wall.top
                dx = push_right if push_right < push_left else -push_left
                dy = push_down if push_down < push_up else -push_up
                if abs(dx) <= abs(dy):
                    self.hitbox.x += dx
                else:
                    self.hitbox.y += dy
                self.x = float(self.hitbox.centerx)
                self.y = float(self.hitbox.centery)
                self.speed *= self.WALL_BOUNCE

    def _obb_radius(self, axis):
        """Проекционный «радиус» повёрнутого кузова на ось axis (для SAT)."""
        rad = radians(self.angle)
        fx, fy = sin(rad), -cos(rad)        # вектор «вперёд» (вдоль кузова)
        rx, ry = cos(rad), sin(rad)         # вектор «вправо» (поперёк)
        return (self.HALF_W * abs(rx * axis[0] + ry * axis[1]) +
                self.HALF_L * abs(fx * axis[0] + fy * axis[1]))

    def collide_with(self, other):
        """Разрешает столкновение двух машин как повёрнутых прямоугольников
        (OBB, метод разделяющих осей): расталкивает ОБЕ машины по минимальному
        вектору раздвижки, гасит их скорость и выталкивает из стен."""
        ra, rb = radians(self.angle), radians(other.angle)
        axes = [(sin(ra), -cos(ra)), (cos(ra), sin(ra)),
                (sin(rb), -cos(rb)), (cos(rb), sin(rb))]
        dx, dy = other.x - self.x, other.y - self.y
        min_overlap, mtv = 1e9, None
        for ax in axes:
            dist = dx * ax[0] + dy * ax[1]
            overlap = self._obb_radius(ax) + other._obb_radius(ax) - abs(dist)
            if overlap <= 0:
                return                      # разделяющая ось — нет касания
            if overlap < min_overlap:
                min_overlap = overlap
                s = 1 if dist >= 0 else -1
                mtv = (ax[0] * s, ax[1] * s)   # ось, направленная от self к other
        push = min_overlap / 2
        self.x -= mtv[0] * push
        self.y -= mtv[1] * push
        other.x += mtv[0] * push
        other.y += mtv[1] * push
        for c in (self, other):
            c.hitbox.center = (round(c.x), round(c.y))
            c._depenetrate_walls()
            c.rect.center = (round(c.x), round(c.y))
            c.speed *= c.COLLISION_BOUNCE

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

    def to_state(self):
        """Снимок состояния машины для отправки по сети (JSON-сериализуемо)."""
        return [round(self.x, 1), round(self.y, 1), round(self.angle, 1),
                round(self.nitro, 3), self.boosting, round(abs(self.speed), 3)]

    def apply_state(self, cs):
        """Восстанавливает машину из снимка to_state() (на стороне клиента)."""
        self.x, self.y, self.angle, self.nitro, self.boosting, self.speed = cs
        self.image_to_draw = pygame.transform.rotate(self.base_image, -self.angle)
        self.rect = self.image_to_draw.get_rect(center=(round(self.x), round(self.y)))
        self.hitbox.center = (round(self.x), round(self.y))


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
