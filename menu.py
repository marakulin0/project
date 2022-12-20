import pygame
import sys

window = pygame.display.set_mode((1024, 768))
pygame.display.set_caption('racing')
screen = pygame.Surface((1024, 768))


class Menu:
    def __init__(self, punkts, punkts1):
        self.punkts = punkts
        self.punkts1 = punkts1

    def render(self, poverhnost, font, num_punkt):
        for i in self.punkts:
            if num_punkt == i[5]:
                poverhnost.blit(font.render(i[2], 1, i[4]), (i[0], i[1]-30))
            else:
                poverhnost.blit(font.render(i[2], 1, i[3]), (i[0], i[1]-30))

    def menu(self):
        done = True
        font_menu = pygame.font.Font(None, 100)
        pygame.key.set_repeat(0, 0)
        pygame.mouse.set_visible(True)
        punkt = 0
        while done:
            screen.blit(pygame.image.load('menu_bg.jpg'), (0, 0))
            mp = pygame.mouse.get_pos()
            for i in self.punkts:
                if mp[0] > i[0] and mp[0] < i[0] + 155 and\
                     mp[1] > i[1] and mp[1] < i[1] + 50:
                    punkt = i[5]
            self.render(screen, font_menu, punkt)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        sys.exit()
                    if e.key == pygame.K_UP:
                        if punkt > 0:
                            punkt -= 1
                    if e.key == pygame.K_DOWN:
                        if punkt < len(self.punkts) - 1:
                            punkt += 1
                if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or\
                        (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN):
                    if punkt == 0:
                        done = False
                    elif punkt == 1:
                        sys.exit()
            window.blit(screen, (0, 0))
            pygame.display.flip()

    def menu_1(self):
        cycling = True
        road = pygame.image.load('road.png')
        road_image = pygame.transform.scale(road, (256, 192))
        bio = pygame.image.load('bio.png')
        bio_image = pygame.transform.scale(bio, (256, 192))
        pygame.key.set_repeat(0, 0)
        pygame.mouse.set_visible(True)
        punkt1 = 0
        while cycling:
            screen.blit(pygame.image.load('menu_bg.jpg'), (0, 0))
            screen.blit(road_image, (100, 100))
            screen.blit(bio_image, (600, 100))
            mp = pygame.mouse.get_pos()
            for i in self.punkts1:
                if mp[0] > i[0] and mp[0] < i[0]+256 and mp[1] > \
                        i[1] and mp[1] < i[1] + 192:
                    punkt1 = i[2]
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        sys.exit()
                    if e.key == pygame.K_LEFT:
                        if punkt1 > 0:
                            punkt1 -= 1
                    if e.key == pygame.K_RIGHT:
                        if punkt1 < len(self.punkts1)-1:
                            punkt1 += 1
                if (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or\
                        (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN):
                    if punkt1 == 0:
                        road = 0
                        cycling = False
                    elif punkt1 == 1:
                        road = 1
                        cycling = False
            window.blit(screen, (0, 0))
            pygame.display.flip()
        return road
