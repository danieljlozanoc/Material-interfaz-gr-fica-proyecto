# gui_client.py
import sys, os
from PyQt5.QtCore import Qt, QRectF, pyqtSignal, QObject
from PyQt5.QtGui import (QPainter, QColor, QBrush, QPen, QFont,
                          QPixmap, QRadialGradient, QImage)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                              QPushButton, QVBoxLayout, QHBoxLayout,
                              QMessageBox, QFrame, QScrollArea)
from client_transport import GameClient

# ---------------------------------------------------------------------------
# RUTAS
# ---------------------------------------------------------------------------
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
def _assets(rel): return os.path.join(_SCRIPT_DIR, rel)

# ---------------------------------------------------------------------------
# DIMENSIONES
# Grilla 30×30 → CELL = 22px (doble resolución respecto a la grilla 15×15)
# Coordenadas medidas directamente sobre tablero.png con cuadrícula superpuesta
# ---------------------------------------------------------------------------
BOARD_SIZE = 660
CELL       = BOARD_SIZE // 30   # 22 px

# ---------------------------------------------------------------------------
# COLORES FALLBACK
# ---------------------------------------------------------------------------
C_DARK   = QColor("#5c3410")
C_RED    = QColor("#b81c1c")
C_BLUE   = QColor("#1a3a8c")
C_GREEN  = QColor("#1a7a2e")
C_YELLOW = QColor("#d4a800")
PLAYER_COLORS = {"red":C_RED,"blue":C_BLUE,"green":C_GREEN,"yellow":C_YELLOW}

# ---------------------------------------------------------------------------
# TRACK_GRID — 64 casillas del camino circular, grilla 30×30
# Coordenadas (col, row) leídas visualmente desde tablero.png
# ---------------------------------------------------------------------------
TRACK_GRID = [
    (18.05, 23.68),  # 0  - salida roja
    (19.0,  22.36),  # 1
    (19.18, 21.45),  # 2
    (19.45, 20.32),  # 3
    (20.32, 19.36),  # 4
    (21.59, 18.91),  # 5
    (22.82, 18.59),  # 6
    (24.05, 18.82),  # 7
    (25.32, 18.82),  # 8
    (26.45, 18.82),  # 9
    (27.64, 18.82),  # 10
    (29.0,  18.82),  # 11
    (28.77, 14.77),  # 12
    (29.05, 10.82),  # 13
    (27.73, 10.82),  # 14
    (26.64, 10.82),  # 15
    (25.36, 10.82),  # 16
    (24.05, 10.82),  # 17
    (22.82, 10.91),  # 18
    (21.5,  10.64),  # 19
    (20.68, 10.5 ),  # 20
    (19.82,  9.27),  # 21
    (19.18,  8.32),  # 22
    (18.77,  7.0 ),  # 23
    (18.77,  5.55),  # 24
    (18.91,  4.55),  # 25
    (18.91,  3.05),  # 26
    (18.91,  2.05),  # 27
    (18.91,  0.77),  # 28
    (15.0,   0.5 ),  # 29
    (10.86,  0.68),  # 30
    (10.86,  1.91),  # 31
    (10.86,  3.18),  # 32
    (10.86,  4.45),  # 33
    (10.05,  5.68),  # 34  <- salida azul  (PLAYER_OFFSET blue = 34)
    (11.18,  7.05),  # 35
    (10.91,  8.23),  # 36
    (10.32,  9.32),  # 37
    ( 9.55, 10.27),  # 38
    ( 8.55, 10.91),  # 39
    ( 7.18, 11.27),  # 40
    ( 5.82, 11.18),  # 41
    ( 4.41, 10.86),  # 42
    ( 3.32, 10.86),  # 43
    ( 2.05, 10.86),  # 44
    ( 0.95, 10.86),  # 45
    ( 0.86, 14.82),  # 46
    ( 0.73, 19.0 ),  # 47
    ( 1.86, 18.86),  # 48
    ( 3.0,  18.86),  # 49
    ( 4.23, 18.86),  # 50
    ( 5.5,  18.86),  # 51
    ( 6.64, 18.55),  # 52
    ( 7.86, 18.68),  # 53
    ( 9.0,  19.36),  # 54
    ( 9.95, 20.27),  # 55
    (10.5,  21.18),  # 56
    (10.82, 22.5 ),  # 57
    (10.77, 23.73),  # 58
    (10.68, 25.0 ),  # 59
    (10.68, 26.23),  # 60
    (10.68, 27.5 ),  # 61
    (10.68, 28.68),  # 62
    (14.77, 29.0 ),  # 63
]

# Offset de cada jugador (igual que game_engine)
PLAYER_OFFSET = {"red": 0, "blue": 34, "green": 17, "yellow": 51}

# ---------------------------------------------------------------------------
# JAIL_GRID — posiciones de las 4 fichas dentro de cada cárcel, grilla 30×30
# ---------------------------------------------------------------------------
JAIL_GRID = {
    "blue":   [( 2.77, 3.18), ( 5.32, 3.18), ( 2.77, 5.5 ), ( 5.32, 5.5 )],
    "yellow": [(24.77, 3.18), (27.32, 3.18), (24.77, 5.5 ), (27.32, 5.5 )],
    "green":  [( 2.77,24.10), ( 5.32,24.10), ( 2.77,26.77), ( 5.32,26.77)],
    "red":    [(24.77,24.10), (27.32,24.10), (24.77,26.77), (27.32,26.77)],
}

FINAL_PATH = 70

# ---------------------------------------------------------------------------
# FINAL_TRACK — carril final hacia la meta, grilla 30×30
# pos_rel 64-69 = 6 casillas del carril, 70 = meta central
# ---------------------------------------------------------------------------
FINAL_TRACK = {
    "blue": [
        (15.0,  1.91),  # 64
        (15.0,  3.05),  # 65
        (15.0,  4.45),  # 66
        (15.0,  5.68),  # 67
        (15.0,  6.82),  # 68
        (15.0,  8.05),  # 69
        (15.0,  9.32),  # 70  meta central
    ],
    "red": [
        (15.0, 27.95),  # 64
        (15.0, 26.64),  # 65
        (15.0, 25.27),  # 66
        (15.0, 24.14),  # 67
        (15.0, 22.91),  # 68
        (15.0, 21.77),  # 69
        (15.0, 20.45),  # 70  meta central
    ],
}

# ---------------------------------------------------------------------------
# IMÁGENES
# ---------------------------------------------------------------------------
PIECE_PIXMAPS = {}
DICE_PIXMAPS  = {}
BOARD_PIXMAP  = None

def _load_pixmap(path, alpha=False):
    if not os.path.exists(path): return None
    px = QPixmap.fromImage(QImage(path).convertToFormat(
        QImage.Format_ARGB32)) if alpha else QPixmap(path)
    return px if not px.isNull() else None

def _init_pixmaps():
    global BOARD_PIXMAP
    BOARD_PIXMAP = _load_pixmap(_assets("tablero.png"))
    for c in ("red","blue","green","yellow"):
        px = _load_pixmap(_assets(f"fichas/ficha_{c}.png"), alpha=True)
        if px: PIECE_PIXMAPS[c] = px
    for v in range(1, 7):
        px = _load_pixmap(_assets(f"dados/dice_{v}.png"))
        if px: DICE_PIXMAPS[v] = px

# ---------------------------------------------------------------------------
# COORDENADAS
# ---------------------------------------------------------------------------
def grid_to_px(col, row):
    """Centro de la celda (col, row) en píxeles."""
    return int((col + 0.5) * CELL), int((row + 0.5) * CELL)

def pos_to_px(color, pos_rel):
    """pos_rel → píxeles. Aplica offset del jugador y camino final."""
    if pos_rel < 0:
        return None
    if pos_rel >= 64:
        track = FINAL_TRACK.get(color)
        if track:
            idx = min(pos_rel - 64, len(track) - 1)
            return grid_to_px(*track[idx])
        return grid_to_px(15, 14)   # fallback centro
    real = (pos_rel + PLAYER_OFFSET.get(color, 0)) % 64
    return grid_to_px(*TRACK_GRID[real])

# ---------------------------------------------------------------------------
# SEÑAL PUENTE (hilo seguro WebSocket → UI)
# ---------------------------------------------------------------------------
class _Bridge(QObject):
    message_received = pyqtSignal(dict)

# ---------------------------------------------------------------------------
# WIDGET DEL TABLERO
# ---------------------------------------------------------------------------
class BoardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(BOARD_SIZE, BOARD_SIZE)
        self.players               = []
        self.my_color              = None
        self.selected_piece        = None
        self.on_piece_selected_cb  = None
        _init_pixmaps()

    def update_state(self, players, my_color):
        self.players  = players
        self.my_color = my_color
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        if BOARD_PIXMAP:
            p.drawPixmap(0, 0, BOARD_SIZE, BOARD_SIZE, BOARD_PIXMAP)
        else:
            p.fillRect(0, 0, BOARD_SIZE, BOARD_SIZE, QColor("#d4a96a"))
        self._draw_pieces(p)
        p.end()

    def _draw_pieces(self, p):
        # CELL*2 = 44px → mismo tamaño visual que la versión 15×15
        C          = CELL * 2
        piece_size = int(C * 0.82)
        radius     = int(C * 0.42)
        off        = C // 6
        GROUP_OFF  = [(-24, 0), (-8, 0), (8, 0), (24, 0)]

        active_colors = {pl.get("color") for pl in self.players}
        all_players   = list(self.players)
        for color in ("green", "yellow"):
            if color not in active_colors:
                all_players.append({"color": color, "pieces": [-1, -1, -1, -1]})

        jail_indices = {c: 0 for c in ("red", "blue", "green", "yellow")}

        for player in all_players:
            cname   = player.get("color", "red")
            color   = PLAYER_COLORS.get(cname, C_RED)
            pieces  = player.get("pieces", [-1, -1, -1, -1])
            pixmap  = PIECE_PIXMAPS.get(cname)
            is_deco = cname not in active_colors

            pos_count = {}
            for pos in pieces:
                if pos != -1: pos_count[pos] = pos_count.get(pos, 0) + 1
            pos_slot = {}

            for i, pos in enumerate(pieces):
                if pos == -1:
                    slots = JAIL_GRID.get(cname, [])
                    idx   = jail_indices[cname]
                    jail_indices[cname] += 1
                    if idx < len(slots):
                        gc, gr = slots[idx]
                        # FIX v2: usar (gc+0.5)*CELL para centrar igual que grid_to_px
                        bx, by = int((gc + 0.5) * CELL), int((gr + 0.5) * CELL)
                    else:
                        continue
                else:
                    coords = pos_to_px(cname, pos)
                    if coords is None: continue
                    bx, by = coords
                    if pos >= FINAL_PATH:
                        meta_off = [(-10, -10), (10, -10), (-10, 10), (10, 10)]
                        ox, oy = meta_off[i % 4]
                        bx += ox; by += oy

                if pos != -1 and pos_count.get(pos, 1) > 1:
                    slot = pos_slot.get(pos, 0)
                    pos_slot[pos] = slot + 1
                    ox, oy = GROUP_OFF[slot % 4]
                    bx += ox; by += oy

                is_sel = (not is_deco and cname == self.my_color
                          and i == self.selected_piece)
                if is_sel:
                    p.setPen(QPen(QColor(255, 255, 180, 220), 5))
                    p.setBrush(QBrush(QColor(255, 255, 255, 70)))
                    p.drawEllipse(bx - radius - 7, by - radius - 7,
                                  (radius + 7) * 2, (radius + 7) * 2)

                if pixmap:
                    sc = pixmap.scaled(piece_size, piece_size,
                                       Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    p.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    p.drawPixmap(bx - sc.width() // 2, by - sc.height() // 2, sc)
                else:
                    grad = QRadialGradient(bx - radius // 3, by - radius // 3, radius * 1.2)
                    grad.setColorAt(0.0, QColor(color).lighter(160))
                    grad.setColorAt(1.0, color)
                    p.setBrush(QBrush(grad))
                    p.setPen(QPen(C_DARK, 2))
                    p.drawEllipse(bx - radius, by - radius, radius * 2, radius * 2)

                if not is_deco:
                    nr = max(7, int(radius * 0.44))
                    bx2, by2 = bx + radius // 2, by - radius // 2
                    p.setBrush(QBrush(QColor(0, 0, 0, 170)))
                    p.setPen(Qt.NoPen)
                    p.drawEllipse(bx2 - nr, by2 - nr, nr * 2, nr * 2)
                    p.setPen(QColor("white"))
                    p.setFont(QFont("Georgia", max(6, nr - 2), QFont.Bold))
                    p.drawText(QRectF(bx2 - nr, by2 - nr, nr * 2, nr * 2),
                               Qt.AlignCenter, str(i + 1))

    def mousePressEvent(self, event):
        if self.my_color is None: return
        C      = CELL * 2
        radius = int(C * 0.42) + 20
        mx, my = event.x(), event.y()

        for player in self.players:
            if player.get("color") != self.my_color: continue
            jail_idx = 0
            for i, pos in enumerate(player.get("pieces", [])):
                if pos == -1:
                    slots = JAIL_GRID.get(self.my_color, [])
                    if jail_idx < len(slots):
                        gc, gr = slots[jail_idx]
                        # FIX v2: centrar igual que grid_to_px / _draw_pieces
                        px_ = int((gc + 0.5) * CELL)
                        py_ = int((gr + 0.5) * CELL)
                        jail_idx += 1
                    else:
                        continue
                else:
                    coords = pos_to_px(self.my_color, pos)
                    if coords is None: continue
                    px_, py_ = coords

                if (mx - px_) ** 2 + (my - py_) ** 2 <= radius ** 2:
                    self.selected_piece = i
                    self.update()
                    if self.on_piece_selected_cb:
                        self.on_piece_selected_cb(i)
                    return

# ---------------------------------------------------------------------------
# VENTANA PRINCIPAL
# ---------------------------------------------------------------------------
class GameWindow(QMainWindow):
    def __init__(self, player_name):
        super().__init__()
        self.player_name       = player_name
        self.my_id             = None
        self.my_color          = None
        self.current_player_id = None
        self.game_state        = "waiting_for_players"
        self.players_info      = []
        self.dice_moves        = None
        self.selected_piece    = None
        self.log_lines         = []

        self._bridge = _Bridge()
        self._bridge.message_received.connect(self._handle_response)
        self._build_ui()
        self._connect()

    def _build_ui(self):
        self.setWindowTitle(f"PyParqués — {self.player_name}")
        self.setStyleSheet("background-color: #2b1a0a;")
        self.board = BoardWidget()

        right = QWidget()
        right.setFixedWidth(230)
        right.setStyleSheet("background-color:#3d2208; border-radius:8px;")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(10, 12, 10, 12)
        rl.setSpacing(8)

        self.lbl_player = QLabel(f"👤  {self.player_name}")
        self.lbl_player.setFont(QFont("Georgia", 12, QFont.Bold))
        self.lbl_player.setStyleSheet("color:#f5e6c8;")
        self.lbl_player.setAlignment(Qt.AlignCenter)

        self.lbl_status = QLabel("⏳ Esperando jugadores...")
        self.lbl_status.setFont(QFont("Georgia", 10))
        self.lbl_status.setStyleSheet("color:#d4a96a;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setWordWrap(True)

        dice_frame = QFrame()
        dice_frame.setStyleSheet("background:#4a2c00;border-radius:8px;padding:4px;")
        dl = QHBoxLayout(dice_frame)
        dl.setContentsMargins(6, 6, 6, 6); dl.setSpacing(10)
        self.dice_labels = []
        for _ in range(2):
            lbl = QLabel("🎲")
            lbl.setFont(QFont("Arial", 28))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color:#f5e6c8;background:transparent;")
            lbl.setFixedSize(90, 90)
            self.dice_labels.append(lbl)
            dl.addWidget(lbl)

        self.btn_roll = QPushButton("🎲  Lanzar dados")
        self.btn_roll.setFont(QFont("Georgia", 11, QFont.Bold))
        self.btn_roll.setFixedHeight(40)
        self.btn_roll.setStyleSheet(self._btn_style())
        self.btn_roll.clicked.connect(self._roll_dice)
        self.btn_roll.setEnabled(False)

        self.lbl_piece = QLabel("Clic en una ficha para seleccionarla")
        self.lbl_piece.setFont(QFont("Georgia", 9))
        self.lbl_piece.setStyleSheet("color:#d4a96a;")
        self.lbl_piece.setWordWrap(True)
        self.lbl_piece.setAlignment(Qt.AlignCenter)

        self.move_frame = QFrame()
        self.move_frame.setStyleSheet("background:#4a2c00;border-radius:6px;padding:2px;")
        self.move_layout = QVBoxLayout(self.move_frame)
        self.move_layout.setContentsMargins(4, 4, 4, 4)
        self.move_layout.setSpacing(4)
        self.move_frame.setVisible(False)

        self.btn_state = QPushButton("📋  Ver estado")
        self.btn_state.setFont(QFont("Georgia", 11, QFont.Bold))
        self.btn_state.setFixedHeight(40)
        self.btn_state.setStyleSheet(self._btn_style())
        self.btn_state.clicked.connect(self._get_state)

        log_title = QLabel("📜  Registro")
        log_title.setFont(QFont("Georgia", 10, QFont.Bold))
        log_title.setStyleSheet("color:#d4a96a;")

        self.log_content = QLabel("")
        self.log_content.setFont(QFont("Georgia", 8))
        self.log_content.setStyleSheet("color:#c8a060;background:transparent;padding:4px;")
        self.log_content.setWordWrap(True)
        self.log_content.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        self.log_scroll = QScrollArea()
        self.log_scroll.setWidget(self.log_content)
        self.log_scroll.setWidgetResizable(True)
        self.log_scroll.setFixedHeight(240)
        self.log_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.log_scroll.setStyleSheet("""
            QScrollArea{background:#2b1a0a;border:1px solid #7a4010;border-radius:6px;}
            QScrollBar:vertical{background:#3d2208;width:8px;border-radius:4px;}
            QScrollBar::handle:vertical{background:#a0541a;border-radius:4px;min-height:20px;}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0px;}
        """)

        rl.addWidget(self.lbl_player)
        rl.addWidget(self.lbl_status)
        rl.addWidget(dice_frame)
        rl.addWidget(self.btn_roll)
        rl.addWidget(self.lbl_piece)
        rl.addWidget(self.move_frame)
        rl.addWidget(self.btn_state)
        rl.addWidget(log_title)
        rl.addWidget(self.log_scroll)
        rl.addStretch()

        main = QWidget()
        ml   = QHBoxLayout(main)
        ml.setContentsMargins(12, 12, 12, 12); ml.setSpacing(12)
        ml.addWidget(self.board)
        ml.addWidget(right)
        self.setCentralWidget(main)
        self.setFixedSize(BOARD_SIZE + 254, BOARD_SIZE + 24)
        self.board.on_piece_selected_cb = self.on_piece_selected

    def _btn_style(self, color="#7a4010"):
        return f"""
            QPushButton{{background:{color};color:#f5e6c8;border-radius:7px;}}
            QPushButton:hover{{background:#a0541a;}}
            QPushButton:pressed{{background:#4a2c00;}}
            QPushButton:disabled{{background:#3d2208;color:#7a5030;}}
        """

    def _connect(self):
        self.client = GameClient(
            "ws://127.0.0.1:8765",
            lambda r: self._bridge.message_received.emit(r))
        self.client.connect()
        self.client.send_action("join", player_name=self.player_name)
        self.client.send_action("get_my_id")

    def _roll_dice(self):
        self.client.send_action("roll_dice")

    def _get_state(self):
        self.client.send_action("get_state")

    def on_piece_selected(self, idx):
        self.selected_piece = idx
        self.lbl_piece.setText(f"Ficha {idx+1} seleccionada")
        if self.dice_moves is not None:
            self._show_move_buttons()
        else:
            self._log("⚠ Lanza los dados primero.")

    def _show_move_buttons(self):
        while self.move_layout.count():
            item = self.move_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if self.dice_moves is None:
            self.move_frame.setVisible(False)
            return

        dm = self.dice_moves
        opciones = []
        if not dm.get("used_d1") and not dm.get("used_sum"):
            opciones.append((dm["d1"], f"Mover {dm['d1']} (dado 1)"))
        if not dm.get("used_d2") and not dm.get("used_sum"):
            opciones.append((dm["d2"], f"Mover {dm['d2']} (dado 2)"))
        if not dm.get("used_sum") and not (dm.get("used_d1") or dm.get("used_d2")):
            opciones.append((dm["sum"], f"Mover {dm['sum']} (suma)"))

        seen = set()
        opciones_unicas = []
        for v, label in opciones:
            if v not in seen:
                seen.add(v)
                opciones_unicas.append((v, label))

        if not opciones_unicas:
            self.move_frame.setVisible(False)
            return

        d1, d2 = self.dice_moves["d1"], self.dice_moves["d2"]
        info = QLabel(f"🎲 {d1} + {d2} = {d1+d2}{'  (par)' if d1==d2 else ''}")
        info.setFont(QFont("Georgia", 8))
        info.setStyleSheet("color:#d4a96a; background:transparent;")
        info.setAlignment(Qt.AlignCenter)
        self.move_layout.insertWidget(0, info)

        for value, label in opciones_unicas:
            btn = QPushButton(label)
            btn.setFont(QFont("Georgia", 10, QFont.Bold))
            btn.setFixedHeight(36)
            btn.setStyleSheet(self._btn_style("#5a3010"))
            btn.clicked.connect(lambda _, v=value: self._do_move(v))
            self.move_layout.addWidget(btn)

        nota = QLabel("Puedes usar cada dado en una ficha distinta")
        nota.setFont(QFont("Georgia", 7))
        nota.setStyleSheet("color:#7a5030; background:transparent;")
        nota.setWordWrap(True)
        nota.setAlignment(Qt.AlignCenter)
        self.move_layout.addWidget(nota)

        self.move_frame.setVisible(True)

    def _do_move(self, cells):
        if self.selected_piece is None:
            self._log("⚠ Selecciona una ficha primero.")
            return
        self.client.send_action("move_piece",
                                piece_id=self.selected_piece,
                                cells_to_move=cells)
        self.selected_piece       = None
        self.board.selected_piece = None
        self.board.update()
        self.move_frame.setVisible(False)
        self.lbl_piece.setText("Clic en una ficha para seleccionarla")

    def _is_my_turn(self):
        return self.my_id is not None and self.current_player_id == self.my_id

    def _all_in_jail(self):
        for pl in self.players_info:
            if pl.get("color") == self.my_color:
                return all(p == -1 for p in pl.get("pieces", []))
        return True

    def _handle_response(self, data):
        if data.get("_disconnected"):
            if self.game_state not in ("finished",):
                QMessageBox.warning(self, "Desconexión",
                    "El oponente se ha desconectado. La partida ha terminado.")
            return

        if "id"             in data: self.my_id             = data["id"]
        if "current_player" in data: self.current_player_id = data["current_player"]
        if "game_state"     in data: self.game_state        = data["game_state"]

        if "board_state" in data and isinstance(data["board_state"], dict):
            self._update_from_board(data["board_state"])

        if "players" in data and "board_state" not in data:
            old_pieces = {pl.get("color"): list(pl.get("pieces", []))
                         for pl in self.players_info}
            self._sync_players(data["players"])
            for pl in self.players_info:
                color = pl.get("color")
                if not color or color == self.my_color: continue
                old = old_pieces.get(color, [])
                new = pl.get("pieces", [])
                for i, (o, n) in enumerate(zip(old, new)):
                    if o != -1 and n == -1:
                        self._log(f"💥 ¡Ficha {i+1} {color} enviada a la cárcel!")

        if "dice" in data:
            d1, d2 = int(data["dice"][0]), int(data["dice"][1])
            self._show_dice(d1, d2)
            self._log(f"🎲 Dados: {d1} y {d2}")

            if self.game_state == "in_progress" and self._is_my_turn():
                if data.get("is_double"):
                    self._log("🎯 ¡Presada! Fichas en salida. Vuelve a lanzar.")
                    self.dice_moves = None
                elif not self._all_in_jail():
                    self.dice_moves = {
                        "d1": d1, "d2": d2, "sum": d1 + d2,
                        "used_d1": False, "used_d2": False, "used_sum": False
                    }
                    self._log("♟ Haz clic en una ficha para moverla.")

        if "dice_moves" in data:
            self.dice_moves = data["dice_moves"]
            if self.selected_piece is not None and self.dice_moves:
                self._show_move_buttons()
            else:
                self.move_frame.setVisible(False)

        if "warning" in data: self._log(f"⚠ {data['warning']}")
        if "error"   in data: self._log(f"❌ {data['error']}")
        if "message" in data: self._log(f"ℹ {data['message']}")

        self.board.update_state(self.players_info, self.my_color)
        self._refresh_status()

        if self.game_state == "finished" or "winner" in data:
            winner_id = data.get("winner", "")
            if winner_id == self.my_id:
                self._show_win_dialog(won=True)
            elif winner_id:
                self._show_win_dialog(won=False)

    def _sync_players(self, players):
        self.players_info = players
        if self.my_id and not self.my_color:
            for p in self.players_info:
                if p.get("id") == self.my_id:
                    self.my_color       = p.get("color")
                    self.board.my_color = self.my_color
        self.board.update_state(self.players_info, self.my_color)

    def _update_from_board(self, board):
        if "players"        in board: self._sync_players(board["players"])
        if "current_player" in board: self.current_player_id = board["current_player"]
        if "game_state"     in board: self.game_state        = board["game_state"]
        if "dices_value"    in board:
            d = board["dices_value"]
            if d and d[0]: self._show_dice(d[0], d[1])
        if "dice_moves"     in board:
            self.dice_moves = board["dice_moves"]

    def _refresh_status(self):
        msgs = {
            "waiting_for_players": "⏳ Esperando al otro jugador...",
            "defining_turn_order": "🎲 Definiendo quién empieza...",
            "in_progress":         "🎮 Partida en curso",
            "finished":            "🏁 Partida terminada",
        }
        status = msgs.get(self.game_state, self.game_state)
        is_my  = self._is_my_turn()

        if self.game_state == "defining_turn_order":
            if is_my:
                status += "\n✅ Lanza el dado"
                self.btn_roll.setEnabled(True)
            else:
                status += "\n⏳ Espera que el otro jugador lance"
                self.btn_roll.setEnabled(False)
            self.move_frame.setVisible(False)

        elif self.game_state == "in_progress":
            if is_my:
                status += "\n✅ Es TU turno"
                if self._all_in_jail():
                    self.btn_roll.setEnabled(True)
                    self.move_frame.setVisible(False)
                    status += "\n🔒 Lanza para sacar presada"
                else:
                    self.btn_roll.setEnabled(self.dice_moves is None)
            else:
                status += "\n⏳ Turno del oponente"
                self.btn_roll.setEnabled(False)
                self.move_frame.setVisible(False)
                self.lbl_piece.setText("Clic en una ficha para seleccionarla")

        self.lbl_status.setText(status)

    def _show_dice(self, d1, d2):
        EMOJI = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
        for val, lbl in zip((d1, d2), self.dice_labels):
            px = DICE_PIXMAPS.get(val)
            if px:
                lbl.setPixmap(px.scaled(84, 84, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                lbl.setText("")
            else:
                lbl.setPixmap(QPixmap())
                lbl.setText(EMOJI.get(val, "🎲"))

    def _show_win_dialog(self, won: bool):
        dialog = QMessageBox(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        if won:
            dialog.setWindowTitle("🏆 ¡Victoria!")
            dialog.setText(
                "<div style='text-align:center;'>"
                "<p style='font-size:48px; margin:0;'>🏆</p>"
                "<p style='font-size:22px; font-weight:bold; color:#f5c518; "
                "font-family:Georgia;'>¡GANASTE!</p>"
                "<p style='font-size:13px; color:#f5e6c8; font-family:Georgia;'>"
                "¡Felicitaciones! Llevaste todas<br>tus fichas a la meta.</p>"
                "</div>"
            )
            dialog.setStyleSheet("""
                QMessageBox{background-color:#2b1a0a;border:3px solid #f5c518;border-radius:12px;}
                QLabel{color:#f5e6c8;}
                QPushButton{background:#f5c518;color:#2b1a0a;font-family:Georgia;
                    font-weight:bold;font-size:13px;border-radius:8px;
                    padding:8px 28px;min-width:100px;}
                QPushButton:hover{background:#ffd700;}
            """)
        else:
            dialog.setWindowTitle("Fin del juego")
            dialog.setText(
                "<div style='text-align:center;'>"
                "<p style='font-size:42px; margin:0;'>😔</p>"
                "<p style='font-size:18px; font-weight:bold; color:#d4a96a; "
                "font-family:Georgia;'>El oponente ganó</p>"
                "<p style='font-size:12px; color:#c8a060; font-family:Georgia;'>"
                "Mejor suerte la próxima vez.</p>"
                "</div>"
            )
            dialog.setStyleSheet("""
                QMessageBox{background-color:#2b1a0a;border:3px solid #7a4010;border-radius:12px;}
                QLabel{color:#f5e6c8;}
                QPushButton{background:#7a4010;color:#f5e6c8;font-family:Georgia;
                    font-weight:bold;font-size:13px;border-radius:8px;
                    padding:8px 28px;min-width:100px;}
                QPushButton:hover{background:#a0541a;}
            """)
        dialog.setStandardButtons(QMessageBox.Ok)
        dialog.exec_()

    def _log_positions(self):
        for pl in self.players_info:
            nombre = pl.get("name", pl.get("color", "?"))
            color  = pl.get("color", "?")
            piezas = pl.get("pieces", [])
            partes = []
            for i, pos in enumerate(piezas):
                if pos == -1:           partes.append(f"F{i+1}:cárcel")
                elif pos >= FINAL_PATH: partes.append(f"F{i+1}:meta")
                else:                   partes.append(f"F{i+1}:pos{pos}")
            self._log(f"📍 {nombre}({color}): {', '.join(partes)}")

    def _log(self, msg):
        self.log_lines.append(msg)
        if len(self.log_lines) > 35:
            self.log_lines = self.log_lines[-35:]
        self.log_content.setText("\n".join(self.log_lines))
        self.log_scroll.verticalScrollBar().setValue(
            self.log_scroll.verticalScrollBar().maximum())

# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    name = input("Nombre del jugador: ")
    app  = QApplication(sys.argv)
    win  = GameWindow(name)
    win.show()
    sys.exit(app.exec_())
