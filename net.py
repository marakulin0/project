"""Сетевой слой для онлайн-режима (LAN PvP).

Модель: хост-авторитет. Хост считает всю физику и рассылает состояние;
клиент шлёт свой ввод и отрисовывает присланное состояние.

Транспорт: TCP с TCP_NODELAY (низкая задержка на LAN). Сообщения — это
строки JSON, разделённые '\\n'. Приём идёт в фоновом потоке; хранится
последнее принятое сообщение (latest-wins — для гонки на 60 Гц нам нужен
самый свежий ввод/состояние, а не вся история).
"""

import json
import socket
import threading

PORT = 50007


class NetChannel:
    """Дуплексный канал поверх TCP-сокета."""

    def __init__(self, sock):
        self.sock = sock
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._latest = None
        self._lock = threading.Lock()
        self._alive = True
        self._buf = b''
        self._thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._thread.start()

    def _recv_loop(self):
        while self._alive:
            try:
                data = self.sock.recv(8192)
            except OSError:
                break
            if not data:
                break                      # соединение закрыто другой стороной
            self._buf += data
            while b'\n' in self._buf:
                line, self._buf = self._buf.split(b'\n', 1)
                if not line:
                    continue
                try:
                    msg = json.loads(line.decode('utf-8'))
                except ValueError:
                    continue               # битый кадр — пропускаем
                with self._lock:
                    self._latest = msg
        self._alive = False

    def send(self, obj):
        """Отправляет один JSON-объект. При ошибке помечает канал мёртвым."""
        if not self._alive:
            return
        try:
            self.sock.sendall((json.dumps(obj) + '\n').encode('utf-8'))
        except OSError:
            self._alive = False

    def latest(self):
        """Последнее принятое сообщение (или None)."""
        with self._lock:
            return self._latest

    @property
    def alive(self):
        return self._alive

    def close(self):
        self._alive = False
        try:
            self.sock.close()
        except OSError:
            pass


def host(port=PORT, timeout=None):
    """Слушает порт, ждёт одного клиента, возвращает NetChannel.

    timeout (сек) ограничивает ожидание подключения; None — ждать бесконечно.
    Бросает socket.timeout, если клиент не подключился за timeout.
    """
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('', port))
    srv.listen(1)
    srv.settimeout(timeout)
    try:
        conn, _addr = srv.accept()
    finally:
        srv.close()
    return NetChannel(conn)


def join(ip, port=PORT, timeout=5):
    """Подключается к хосту по IP, возвращает NetChannel.

    Бросает OSError/socket.timeout, если подключиться не удалось.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((ip, port))
    sock.settimeout(None)
    return NetChannel(sock)


def local_ip():
    """Лучшее предположение о LAN-IP машины (для показа на экране хоста)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))        # никуда не шлёт, просто выбирает интерфейс
        return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        s.close()
