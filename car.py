import pygame
from math import sin, cos, pi

'''Создает класс: машина на первой трассе'''


class Car_road():

    def __init__(self, screen, x0, y0, filename):
        self.screen = screen
        car_image_load = pygame.image.load(filename)
        car_image_scaled = pygame.transform.scale(car_image_load, (32, 70))
        self.image = pygame.transform.rotate(car_image_scaled, 90.0)
        self.image_to_draw = self.image
        self.rect = self.image.get_rect()
        self.screen_rect = screen.get_rect()
        self.rect.x = x0
        self.rect.y = y0
        self.speed = 0
        self.acceleration = -0.015
        self.angle = 0
        self.ready_to_finish = False

    def draw_car(self):
        self.screen.blit(self.image_to_draw, self.rect)

    def move_car1(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.speed += self.acceleration
        elif keys[pygame.K_s]:
            self.speed -= self.acceleration
        if self.speed == 0:
            if keys[pygame.K_a] or keys[pygame.K_d]:
                self.angle += 0
        else:
            if keys[pygame.K_a]:
                self.angle += 0.035
            if keys[pygame.K_d]:
                self.angle -= 0.035
        if not (keys[pygame.K_w] or keys[pygame.K_s]):
            self.speed -= self.speed*0.05
        self.image_to_draw = pygame.transform.rotate(self.image,
                                                     self.angle / pi * 180)
        self.rect = self.image_to_draw.get_rect(center=(self.rect.center))
        self.rect.x += self.speed*cos(self.angle)
        self.rect.y -= self.speed*sin(self.angle)

    def move_car2(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.speed += self.acceleration
        elif keys[pygame.K_DOWN]:
            self.speed -= self.acceleration
        if self.speed == 0:
            if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
                self.angle += 0
        else:
            if keys[pygame.K_LEFT]:
                self.angle += 0.035
            if keys[pygame.K_RIGHT]:
                self.angle -= 0.035
        if not (keys[pygame.K_UP] or keys[pygame.K_DOWN]):
            self.speed -= self.speed*0.05
        self.image_to_draw = pygame.transform.rotate(self.image,
                                                     self.angle / pi * 180)
        self.rect = self.image_to_draw.get_rect(center=(self.rect.center))
        self.rect.x += self.speed*cos(self.angle)
        self.rect.y -= self.speed*sin(self.angle)

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

'''задает отражение от стен'''
    def collision_handing(self, rects):
        for i in rects:
            if pygame.rect.Rect.colliderect(self.rect, i):
                if cos(self.angle) < -0.01:
                    deltax = self.rect.right - i.left - cos(self.angle) *\
                            abs(self.speed)
                elif cos(self.angle) > 0.01:
                    deltax = i.right - self.rect.left + cos(self.angle) *\
                             abs(self.speed)
                else:
                    deltax = 2 * abs(self.speed)
                if sin(self.angle) < 0:
                    deltay = i.bottom - self.rect.top + sin(self.angle) *\
                             self.speed
                else:
                    deltay = self.rect.bottom - sin(self.angle) * self.speed -\
                             i.top
                if deltax < 2 * abs(self.speed):
                    if sin(self.angle) > 0:
                        self.angle = pi/2
                    elif sin(self.angle) < 0:
                        self.angle = -pi/2
                    else:
                        self.speed = 0
                    self.speed = 0.2*self.speed
                if deltay < 2 * abs(self.speed):
                    if cos(self.angle) > 0:
                        self.angle = 0
                    elif cos(self.angle) < 0:
                        self.angle = pi
                    else:
                        self.speed = 0
                    self.speed = 0.2*self.speed


class Car_bio():

    def __init__(self, screen, x0, y0, filename):
        self.screen = screen
        car_image_load = pygame.image.load(filename)
        self.image = pygame.transform.scale(car_image_load, (32, 70))
        self.image_to_draw = self.image
        self.rect = self.image.get_rect()
        self.screen_rect = screen.get_rect()
        self.rect.x = x0
        self.rect.y = y0
        self.speed = 0
        self.acceleration = -0.01
        self.angle = 0
        self.ready_to_finish = False

    def draw_car(self):
        self.screen.blit(self.image_to_draw, self.rect)

    def move_car1(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.speed += self.acceleration
        elif keys[pygame.K_s]:
            self.speed -= self.acceleration
        if self.speed == 0:
            if keys[pygame.K_a] or keys[pygame.K_d]:
                self.angle += 0
        else:
            if keys[pygame.K_a]:
                self.angle += 0.035
            if keys[pygame.K_d]:
                self.angle -= 0.035
        self.image_to_draw = pygame.transform.rotate(self.image,
                                                     self.angle / pi * 180)
        self.rect = self.image_to_draw.get_rect(center=(self.rect.center))
        if not (keys[pygame.K_w] or keys[pygame.K_s]):
            self.speed -= self.speed*0.05
        self.rect.y += self.speed*cos(self.angle)
        self.rect.x += self.speed*sin(self.angle)

    def move_car2(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.speed += self.acceleration
        elif keys[pygame.K_DOWN]:
            self.speed -= self.acceleration
        if self.speed == 0:
            if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
                self.angle += 0
        else:
            if keys[pygame.K_LEFT]:
                self.angle += 0.035
            if keys[pygame.K_RIGHT]:
                self.angle -= 0.035
        if not (keys[pygame.K_UP] or keys[pygame.K_DOWN]):
            self.speed -= self.speed*0.05
        self.image_to_draw = pygame.transform.rotate(self.image,
                                                     self.angle / pi * 180)
        self.rect = self.image_to_draw.get_rect(center=(self.rect.center))
        self.rect.y += self.speed*cos(self.angle)
        self.rect.x += self.speed*sin(self.angle)

    rects = [pygame.rect.Rect(0, 0, 12, 768),
             pygame.rect.Rect(10, 0, 1014, 12),
             pygame.rect.Rect(1015, 13, 12, 758),
             pygame.rect.Rect(13, 757, 1004, 12)]

    def collision_handing(self, rects):
        for i in rects:
            if pygame.rect.Rect.colliderect(self.rect, i):
                if cos(self.angle) < -0.01:
                    deltax = self.rect.right - i.left - cos(self.angle) *\
                            abs(self.speed)
                elif cos(self.angle) > 0.01:
                    deltax = i.right - self.rect.left + cos(self.angle) *\
                             abs(self.speed)
                else:
                    deltax = 2 * abs(self.speed)
                if sin(self.angle) < 0:
                    deltay = i.bottom - self.rect.top + sin(self.angle) *\
                             self.speed
                else:
                    deltay = self.rect.bottom - sin(self.angle) * self.speed -\
                             i.top
                if deltax < 2 * abs(self.speed):
                    if sin(self.angle) > 0:
                        self.angle = pi/2
                    elif sin(self.angle) < 0:
                        self.angle = -pi/2
                    else:
                        self.speed = 0
                    self.speed = 0.2*self.speed
                if deltay < 2 * abs(self.speed):
                    if cos(self.angle) > 0:
                        self.angle = 0
                    elif cos(self.angle) < 0:
                        self.angle = pi
                    else:
                        self.speed = 0
                    self.speed = 0.1*self.speed
