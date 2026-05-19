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
# ---------------------------------------------------------------------------
BOARD_SIZE = 660
CELL       = BOARD_SIZE // 15   # 44 px

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
# TRACK CIRCULAR — 64 posiciones absolutas → grid 15×15
# Posición absoluta = (pos_rel + offset_color) % 64
# Offsets: red=0, blue=34, green=17, yellow=51
# ---------------------------------------------------------------------------
TRACK_GRID = [
    (6,14),(6,13),(6,12),(6,11),(6,10),(6,9),    # 0-5   salida roja en 0
    (5,8),(4,8),(3,8),(2,8),(1,8),(0,8),          # 6-11
    (0,7),                                         # 12
    (0,6),(1,6),(2,6),(3,6),(4,6),(5,6),          # 13-18
    (6,5),(6,4),(6,3),(6,2),(6,1),(6,0),          # 19-24
    (7,0),                                         # 25
    (8,0),(8,1),(8,2),(8,3),(8,4),(8,5),          # 26-31
    (9,6),(10,6),(11,6),(12,6),(13,6),(14,6),     # 32-37  salida azul en 34
    (14,7),                                        # 38
    (14,8),(13,8),(12,8),(11,8),(10,8),(9,8),     # 39-44
    (8,9),(8,10),(8,11),(8,12),(8,13),(8,14),     # 45-50
    (7,14),                                        # 51
    (7,13),(7,12),(7,11),(7,10),(7,9),            # 52-56
    (7,8),(7,7),(7,6),(7,5),(7,4),               # 57-61  camino final
    (7,3),(7,2),                                  # 62-63
]

# Offset de cada jugador en el track absoluto
PLAYER_OFFSET = {"red": 0, "blue": 34, "green": 17, "yellow": 51}

# Cárceles — grid coords para 4 fichas por color
JAIL_GRID = {
    "blue":   [(1.2,1.2),(2.7,1.2),(1.2,2.7),(2.7,2.7)],
    "yellow": [(11.8,1.2),(13.3,1.2),(11.8,2.7),(13.3,2.7)],
    "green":  [(1.2,11.8),(2.7,11.8),(1.2,13.3),(2.7,13.3)],
    "red":    [(11.8,11.8),(13.3,11.8),(11.8,13.3),(13.3,13.3)],
}

FINAL_PATH = 70

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
    return int((col+0.5)*CELL), int((row+0.5)*CELL)

def pos_to_px(color, pos_rel):
    """pos_rel (0-63) → píxeles, aplicando offset del jugador."""
    if pos_rel < 0: return None
    if pos_rel >= FINAL_PATH: return grid_to_px(7, 7)
    real = (pos_rel + PLAYER_OFFSET.get(color, 0)) % 64
    col, row = TRACK_GRID[real]
    return grid_to_px(col, row)

# ---------------------------------------------------------------------------
# SEÑAL PUENTE
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
        self.players        = []
        self.my_color       = None
        self.selected_piece = None
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
        C          = CELL
        piece_size = int(C * 1.10)
        radius     = int(C * 0.48)
        off        = C // 4
        GROUP_OFF  = [(-off,-off),(off,-off),(-off,off),(off,off)]

        active_colors = {pl.get("color") for pl in self.players}
        all_players   = list(self.players)
        for color in ("green","yellow"):
            if color not in active_colors:
                all_players.append({"color":color,"pieces":[-1,-1,-1,-1]})

        jail_indices = {c:0 for c in ("red","blue","green","yellow")}

        for player in all_players:
            cname  = player.get("color","red")
            color  = PLAYER_COLORS.get(cname, C_RED)
            pieces = player.get("pieces",[-1,-1,-1,-1])
            pixmap = PIECE_PIXMAPS.get(cname)
            is_deco = cname not in active_colors

            pos_count = {}
            for pos in pieces:
                if pos != -1: pos_count[pos] = pos_count.get(pos,0)+1
            pos_slot = {}

            for i, pos in enumerate(pieces):
                if pos == -1:
                    slots = JAIL_GRID.get(cname,[])
                    idx   = jail_indices[cname]
                    jail_indices[cname] += 1
                    if idx < len(slots):
                        gc,gr = slots[idx]
                        bx,by = int(gc*C), int(gr*C)
                    else: continue
                elif pos >= FINAL_PATH:
                    bx,by = grid_to_px(7,7)
                else:
                    coords = pos_to_px(cname, pos)
                    if coords is None: continue
                    bx,by = coords

                if pos != -1 and pos_count.get(pos,1) > 1:
                    slot = pos_slot.get(pos,0)
                    pos_slot[pos] = slot+1
                    ox,oy = GROUP_OFF[slot%4]
                    bx+=ox; by+=oy

                is_sel = (not is_deco and cname==self.my_color
                          and i==self.selected_piece)
                if is_sel:
                    p.setPen(QPen(QColor(255,255,180,220),5))
                    p.setBrush(QBrush(QColor(255,255,255,70)))
                    p.drawEllipse(bx-radius-7,by-radius-7,(radius+7)*2,(radius+7)*2)

                if pixmap:
                    sc = pixmap.scaled(piece_size,piece_size,
                                       Qt.KeepAspectRatio,Qt.SmoothTransformation)
                    p.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    p.drawPixmap(bx-sc.width()//2, by-sc.height()//2, sc)
                else:
                    grad = QRadialGradient(bx-radius//3,by-radius//3,radius*1.2)
                    grad.setColorAt(0.0, QColor(color).lighter(160))
                    grad.setColorAt(1.0, color)
                    p.setBrush(QBrush(grad))
                    p.setPen(QPen(C_DARK,2))
                    p.drawEllipse(bx-radius,by-radius,radius*2,radius*2)

                if not is_deco:
                    nr = max(7,int(radius*0.44))
                    bx2,by2 = bx+radius//2, by-radius//2
                    p.setBrush(QBrush(QColor(0,0,0,170)))
                    p.setPen(Qt.NoPen)
                    p.drawEllipse(bx2-nr,by2-nr,nr*2,nr*2)
                    p.setPen(QColor("white"))
                    p.setFont(QFont("Georgia",max(6,nr-2),QFont.Bold))
                    p.drawText(QRectF(bx2-nr,by2-nr,nr*2,nr*2),
                               Qt.AlignCenter, str(i+1))

    def mousePressEvent(self, event):
        if self.my_color is None: return
        C      = CELL
        radius = int(C*0.48) + 8
        mx,my  = event.x(), event.y()

        for player in self.players:
            if player.get("color") != self.my_color: continue
            jail_idx = 0
            for i, pos in enumerate(player.get("pieces",[])):
                if pos == -1:
                    slots = JAIL_GRID.get(self.my_color,[])
                    if jail_idx < len(slots):
                        gc,gr = slots[jail_idx]
                        px_,py_ = int(gc*C), int(gr*C)
                        jail_idx += 1
                    else: continue
                elif pos >= FINAL_PATH:
                    px_,py_ = grid_to_px(7,7)
                else:
                    coords = pos_to_px(self.my_color, pos)
                    if coords is None: continue
                    px_,py_ = coords

                if (mx-px_)**2+(my-py_)**2 <= radius**2:
                    self.selected_piece = i
                    self.update()
                    if hasattr(self.parent(),"on_piece_selected"):
                        self.parent().on_piece_selected(i)
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

    # ── UI ────────────────────────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle(f"Parqués — {self.player_name}")
        self.setStyleSheet("background-color: #2b1a0a;")
        self.board = BoardWidget()

        right = QWidget()
        right.setFixedWidth(230)
        right.setStyleSheet("background-color:#3d2208; border-radius:8px;")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(10,12,10,12)
        rl.setSpacing(8)

        self.lbl_player = QLabel(f"👤  {self.player_name}")
        self.lbl_player.setFont(QFont("Georgia",12,QFont.Bold))
        self.lbl_player.setStyleSheet("color:#f5e6c8;")
        self.lbl_player.setAlignment(Qt.AlignCenter)

        self.lbl_status = QLabel("⏳ Esperando jugadores...")
        self.lbl_status.setFont(QFont("Georgia",10))
        self.lbl_status.setStyleSheet("color:#d4a96a;")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setWordWrap(True)

        # Dados
        dice_frame = QFrame()
        dice_frame.setStyleSheet("background:#4a2c00;border-radius:8px;padding:4px;")
        dl = QHBoxLayout(dice_frame)
        dl.setContentsMargins(6,6,6,6); dl.setSpacing(10)
        self.dice_labels = []
        for _ in range(2):
            lbl = QLabel("🎲")
            lbl.setFont(QFont("Arial",28))
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color:#f5e6c8;background:transparent;")
            lbl.setFixedSize(90,90)
            self.dice_labels.append(lbl)
            dl.addWidget(lbl)

        # Botón lanzar
        self.btn_roll = QPushButton("🎲  Lanzar dados")
        self.btn_roll.setFont(QFont("Georgia",11,QFont.Bold))
        self.btn_roll.setFixedHeight(40)
        self.btn_roll.setStyleSheet(self._btn_style())
        self.btn_roll.clicked.connect(self._roll_dice)
        self.btn_roll.setEnabled(False)

        # Panel de movimiento: se muestra tras seleccionar ficha
        self.lbl_piece = QLabel("Clic en una ficha para seleccionarla")
        self.lbl_piece.setFont(QFont("Georgia",9))
        self.lbl_piece.setStyleSheet("color:#d4a96a;")
        self.lbl_piece.setWordWrap(True)
        self.lbl_piece.setAlignment(Qt.AlignCenter)

        # Contenedor de botones de movimiento (dinámico)
        self.move_frame = QFrame()
        self.move_frame.setStyleSheet(
            "background:#4a2c00;border-radius:6px;padding:2px;")
        self.move_layout = QVBoxLayout(self.move_frame)
        self.move_layout.setContentsMargins(4,4,4,4)
        self.move_layout.setSpacing(4)
        self.move_frame.setVisible(False)

        self.btn_state = QPushButton("📋  Ver estado")
        self.btn_state.setFont(QFont("Georgia",11,QFont.Bold))
        self.btn_state.setFixedHeight(40)
        self.btn_state.setStyleSheet(self._btn_style())
        self.btn_state.clicked.connect(self._get_state)

        # Log con scroll
        log_title = QLabel("📜  Registro")
        log_title.setFont(QFont("Georgia",10,QFont.Bold))
        log_title.setStyleSheet("color:#d4a96a;")

        self.log_content = QLabel("")
        self.log_content.setFont(QFont("Georgia",8))
        self.log_content.setStyleSheet("color:#c8a060;background:transparent;padding:4px;")
        self.log_content.setWordWrap(True)
        self.log_content.setAlignment(Qt.AlignTop|Qt.AlignLeft)

        self.log_scroll = QScrollArea()
        self.log_scroll.setWidget(self.log_content)
        self.log_scroll.setWidgetResizable(True)
        self.log_scroll.setFixedHeight(160)
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
        ml.setContentsMargins(12,12,12,12); ml.setSpacing(12)
        ml.addWidget(self.board)
        ml.addWidget(right)
        self.setCentralWidget(main)
        self.setFixedSize(BOARD_SIZE+254, BOARD_SIZE+24)
        self.board.on_piece_selected = self.on_piece_selected

    def _btn_style(self, color="#7a4010"):
        return f"""
            QPushButton{{background:{color};color:#f5e6c8;border-radius:7px;}}
            QPushButton:hover{{background:#a0541a;}}
            QPushButton:pressed{{background:#4a2c00;}}
            QPushButton:disabled{{background:#3d2208;color:#7a5030;}}
        """

    # ── Conexión ──────────────────────────────────────────────────────
    def _connect(self):
        self.client = GameClient(
            "ws://127.0.0.1:8765",
            lambda r: self._bridge.message_received.emit(r))
        self.client.connect()
        self.client.send_action("join", player_name=self.player_name)
        self.client.send_action("get_my_id")

    # ── Acciones ──────────────────────────────────────────────────────
    def _roll_dice(self):
        self.client.send_action("roll_dice")

    def _get_state(self):
        self.client.send_action("get_state")

    def on_piece_selected(self, idx):
        """Llamado cuando el jugador hace clic en una ficha propia."""
        if not self._is_my_turn() or self.dice_moves is None:
            return
        self.selected_piece = idx
        self.lbl_piece.setText(f"Ficha {idx+1} seleccionada")
        self._show_move_buttons()

    def _show_move_buttons(self):
        """Muestra botones con los valores de dados disponibles."""
        # Limpiar botones anteriores
        while self.move_layout.count():
            item = self.move_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        if self.dice_moves is None:
            self.move_frame.setVisible(False)
            return

        dm = self.dice_moves
        opciones = []
        if not dm.get("used_d1") and not dm.get("used_sum"):
            opciones.append(("d1", dm["d1"], f"Mover {dm['d1']} casillas (dado 1)"))
        if not dm.get("used_d2") and not dm.get("used_sum"):
            opciones.append(("d2", dm["d2"], f"Mover {dm['d2']} casillas (dado 2)"))
        if not dm.get("used_sum") and not (dm.get("used_d1") or dm.get("used_d2")):
            opciones.append(("sum", dm["sum"], f"Mover {dm['sum']} casillas (suma)"))

        if not opciones:
            self.move_frame.setVisible(False)
            return

        for move_type, value, label in opciones:
            btn = QPushButton(label)
            btn.setFont(QFont("Georgia", 9, QFont.Bold))
            btn.setFixedHeight(34)
            btn.setStyleSheet(self._btn_style("#5a3010"))
            btn.clicked.connect(lambda _, v=value: self._do_move(v))
            self.move_layout.addWidget(btn)

        self.move_frame.setVisible(True)

    def _do_move(self, cells):
        """Envía el movimiento al servidor."""
        if self.selected_piece is None:
            self._log("⚠ Selecciona una ficha primero.")
            return
        self.client.send_action("move_piece",
                                piece_id=self.selected_piece,
                                cells_to_move=cells)
        # Limpiar selección
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
                return all(p == -1 for p in pl.get("pieces",[]))
        return True

    # ── Respuestas servidor ───────────────────────────────────────────
    def _handle_response(self, data):
        # 1. Actualizar estado base PRIMERO
        if "id"             in data: self.my_id             = data["id"]
        if "current_player" in data: self.current_player_id = data["current_player"]
        if "game_state"     in data: self.game_state        = data["game_state"]

        # 2. board_state completo
        if "board_state" in data and isinstance(data["board_state"], dict):
            self._update_from_board(data["board_state"])

        # 3. Jugadores parcial (move_piece / join)
        if "players" in data and "board_state" not in data:
            self._sync_players(data["players"])

        # 4. Dados
        if "dice" in data:
            d1, d2 = int(data["dice"][0]), int(data["dice"][1])
            self._show_dice(d1, d2)
            self._log(f"🎲 Dados: {d1} y {d2}")

            if self.game_state == "in_progress" and self._is_my_turn():
                if data.get("is_double"):
                    self._log("🎯 ¡Presada! Fichas en salida. Vuelve a lanzar.")
                    self.dice_moves = None
                else:
                    self.dice_moves = {
                        "d1":d1,"d2":d2,"sum":d1+d2,
                        "used_d1":False,"used_d2":False,"used_sum":False
                    }
                    self._log("♟ Haz clic en una ficha para moverla.")

        # 5. Fichas actualizadas (presada)
        if "pieces" in data and "players" not in data and "board_state" not in data:
            # Identificar quién lanzó: el que YA NO tiene el turno
            # (el servidor swapeó current_player antes de responder)
            for pl in self.players_info:
                pid = pl.get("id")
                if pid and pid != self.current_player_id:
                    pl["pieces"] = list(data["pieces"])
                    break
            self.board.update_state(self.players_info, self.my_color)

        # 6. dice_moves explícito (respuesta move_piece)
        if "dice_moves" in data:
            self.dice_moves = data["dice_moves"]
            # Actualizar botones de movimiento si hay ficha seleccionada
            if self.selected_piece is not None and self.dice_moves:
                self._show_move_buttons()
            else:
                self.move_frame.setVisible(False)

        # 7. Mensajes
        if "warning" in data: self._log(f"⚠ {data['warning']}")
        if "error"   in data: self._log(f"❌ {data['error']}")
        if "message" in data: self._log(f"ℹ {data['message']}")

        # 8. Refrescar UI
        self._refresh_status()

        # 9. Fin del juego
        if self.game_state == "finished" or "winner" in data:
            winner_id = data.get("winner","")
            if winner_id == self.my_id:
                QMessageBox.information(self,"🏆 ¡Ganaste!",
                    "¡Felicitaciones! ¡Llevaste todas tus fichas a la meta!")
            else:
                QMessageBox.information(self,"Fin del juego",
                    "El otro jugador ganó la partida.")

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
                    # Todas en cárcel: solo lanzar buscando presada
                    self.btn_roll.setEnabled(True)
                    self.move_frame.setVisible(False)
                    status += "\n🔒 Lanza para sacar presada"
                else:
                    # Hay fichas fuera
                    self.btn_roll.setEnabled(self.dice_moves is None)
            else:
                status += "\n⏳ Turno del oponente"
                self.btn_roll.setEnabled(False)
                self.move_frame.setVisible(False)
                self.lbl_piece.setText("Clic en una ficha para seleccionarla")

        self.lbl_status.setText(status)

    def _show_dice(self, d1, d2):
        EMOJI = {1:"⚀",2:"⚁",3:"⚂",4:"⚃",5:"⚄",6:"⚅"}
        for val, lbl in zip((d1,d2), self.dice_labels):
            px = DICE_PIXMAPS.get(val)
            if px:
                lbl.setPixmap(px.scaled(84,84,Qt.KeepAspectRatio,Qt.SmoothTransformation))
                lbl.setText("")
            else:
                lbl.setPixmap(QPixmap())
                lbl.setText(EMOJI.get(val,"🎲"))

    def _log(self, msg):
        self.log_lines.append(msg)
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
