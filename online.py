"""Экраны лобби для онлайн-режима: выбор режима, ввод IP, ожидание/подключение.

Сетевые операции (host/join) идут в фоновом потоке, чтобы экран не зависал.
Возвращают установленный NetChannel либо None при отмене.
"""

import sys
import threading
import pygame

import net
from controls import screen        # поверхность дисплея (общая со всей игрой)
from menu import resource

_BG_CACHE = None


def _bg():
    global _BG_CACHE
    if _BG_CACHE is None:
        _BG_CACHE = pygame.image.load(resource('menu_bg.jpg'))
    return _BG_CACHE


def _shadow_center(font, text, y, color):
    surf = font.render(text, True, color)
    x = 512 - surf.get_width() // 2
    screen.blit(font.render(text, True, (0, 0, 0)), (x + 3, y + 3))
    screen.blit(surf, (x, y))


def _screen(title, title_color, lines):
    """Рисует фон, тёмную панель, заголовок и строки (text, color, size)."""
    screen.blit(_bg(), (0, 0))
    panel = pygame.Surface((760, 470), pygame.SRCALPHA)
    panel.fill((8, 10, 18, 205))
    pygame.draw.rect(panel, (90, 90, 110), panel.get_rect(), 2, border_radius=10)
    screen.blit(panel, (512 - 380, 95))
    _shadow_center(pygame.font.SysFont('arial', 60, bold=True), title, 125, title_color)
    for i, (text, color, size) in enumerate(lines):
        font = pygame.font.SysFont('arial', size, bold=(size >= 38))
        _shadow_center(font, text, 295 + i * 62, color)


def mode_menu():
    """Возвращает 'local' | 'host' | 'join'. Esc/закрытие — выход из игры."""
    options = [('Локальная игра (2 игрока)', 'local'),
               ('Создать сетевую игру (Host)', 'host'),
               ('Подключиться по сети (Join)', 'join')]
    sel = 0
    clock = pygame.time.Clock()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    sel = (sel + 1) % len(options)
                elif e.key in (pygame.K_UP, pygame.K_w):
                    sel = (sel - 1) % len(options)
                elif e.key == pygame.K_RETURN:
                    return options[sel][1]
        lines = []
        for i, (label, _) in enumerate(options):
            col = (255, 255, 255) if i == sel else (150, 150, 160)
            lines.append((('> ' if i == sel else '   ') + label, col, 40))
        lines.append(('Стрелки — выбор,  Enter — ОК,  Esc — выход', (175, 175, 185), 24))
        _screen('РЕЖИМ ИГРЫ', (240, 230, 90), lines)
        pygame.display.flip()
        clock.tick(60)


def ip_entry(default='192.168.'):
    """Ввод IP хоста. Возвращает строку IP либо None при отмене."""
    text = default
    clock = pygame.time.Clock()
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    return None
                elif e.key == pygame.K_RETURN:
                    return text.strip() or None
                elif e.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                elif e.unicode in '0123456789.':
                    text += e.unicode
        _screen('IP ХОСТА', (240, 230, 90), [
            (text + '_', (255, 255, 255), 48),
            ('Введите IP и нажмите Enter.  Esc — назад.', (175, 175, 185), 24),
        ])
        pygame.display.flip()
        clock.tick(60)


def _await_channel(worker, draw_title, draw_lines, on_fail_msg=None):
    """Общий цикл ожидания результата сетевого потока с отрисовкой экрана."""
    result = {}

    def run():
        try:
            result['ch'] = worker()
        except Exception:
            result['ch'] = None
    threading.Thread(target=run, daemon=True).start()

    clock = pygame.time.Clock()
    tick = 0
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return None
        if 'ch' in result:
            ch = result['ch']
            if ch is None and on_fail_msg:
                _flash(on_fail_msg)
            return ch
        dots = '.' * ((tick // 20) % 4)
        _screen(draw_title + dots, (240, 230, 90), draw_lines)
        pygame.display.flip()
        tick += 1
        clock.tick(60)


def _flash(message, seconds=2.2):
    clock = pygame.time.Clock()
    for _ in range(int(seconds * 60)):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                return
        _screen('ОШИБКА', (235, 90, 80), [(message, (235, 235, 235), 30),
                                          ('Любая клавиша — назад', (175, 175, 185), 24)])
        pygame.display.flip()
        clock.tick(60)


def host_lobby():
    """Поднимает сервер, ждёт клиента. Возвращает NetChannel или None."""
    ip = net.local_ip()
    return _await_channel(
        lambda: net.host(port=net.PORT, timeout=180),
        'Ожидание игрока',
        [('Ваш IP:  ' + ip, (255, 255, 255), 40),
         ('Сообщите IP второму игроку.  Esc — отмена.', (175, 175, 185), 24)])


def client_lobby(ip):
    """Подключается к хосту. Возвращает NetChannel или None."""
    return _await_channel(
        lambda: net.join(ip, port=net.PORT, timeout=10),
        'Подключение к ' + ip,
        [('Esc — отмена', (175, 175, 185), 24)],
        on_fail_msg='Не удалось подключиться к ' + ip)
