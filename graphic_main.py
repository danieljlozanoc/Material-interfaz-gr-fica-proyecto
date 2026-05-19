# graphic_main.py

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QSpacerItem, QSizePolicy
)

from gui_client import GameWindow


class LoginWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.game_window = None

        self.setWindowTitle("Parqués - Ingresar")
        self.setWindowFlags(Qt.MSWindowsFixedSizeDialogHint)

        # =========================================================
        # TÍTULO
        # =========================================================

        title_emoji = QLabel("♟")
        title_emoji.setFont(QFont("Segoe UI Emoji", 24))
        title_emoji.setAlignment(Qt.AlignVCenter | Qt.AlignRight)
        title_emoji.setStyleSheet(
            "color: #4a2c00; background: transparent; padding: 0;"
        )
        title_emoji.setFixedWidth(36)

        title_text = QLabel("Parqués")
        title_text.setFont(QFont("Georgia", 24, QFont.Bold))
        title_text.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title_text.setStyleSheet("""
            color: #4a2c00;
            letter-spacing: 2px;
            background: transparent;
            padding: 0;
        """)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setAlignment(Qt.AlignCenter)
        title_row.addWidget(title_emoji)
        title_row.addWidget(title_text)

        # =========================================================
        # SUBTÍTULO
        # =========================================================

        subtitle = QLabel("¡Bienvenido al juego!")
        subtitle.setFont(QFont("Georgia", 11))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(
            "color: #7a4010; background: transparent;"
        )

        # =========================================================
        # LABEL NOMBRE
        # =========================================================

        lbl_name = QLabel("Nombre del jugador:")
        lbl_name.setFont(QFont("Georgia", 12))
        lbl_name.setStyleSheet(
            "color: #4a2c00; background: transparent;"
        )
        lbl_name.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        lbl_name.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # =========================================================
        # INPUT NOMBRE
        # =========================================================

        self.name_input = QLineEdit()

        self.name_input.setFont(QFont("Georgia", 12))
        self.name_input.setPlaceholderText("Tu nombre...")
        self.name_input.setFixedHeight(38)
        self.name_input.setFixedWidth(180)

        self.name_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #a0641a;
                border-radius: 8px;
                padding: 3px 10px;
                background-color: #fffaf0;
                color: #4a2c00;
            }

            QLineEdit:focus {
                border-color: #4a2c00;
                background-color: #ffffff;
            }
        """)

        self.name_input.returnPressed.connect(self.enter_game)

        # =========================================================
        # BOTÓN
        # =========================================================

        self.btn_enter = QPushButton("Entrar al juego")

        self.btn_enter.setFont(QFont("Georgia", 13, QFont.Bold))
        self.btn_enter.setFixedHeight(46)

        self.btn_enter.setStyleSheet("""
            QPushButton {
                background-color: #7a4010;
                color: white;
                border-radius: 10px;
                padding: 5px 20px;
                letter-spacing: 1px;
            }

            QPushButton:hover {
                background-color: #a0541a;
            }

            QPushButton:pressed {
                background-color: #4a2c00;
            }

            QPushButton:disabled {
                background-color: #5a3a1a;
                color: #c0b0a0;
            }
        """)

        self.btn_enter.clicked.connect(self.enter_game)

        # =========================================================
        # LAYOUT PRINCIPAL
        # =========================================================

        layout = QVBoxLayout()

        layout.setSpacing(10)
        layout.setContentsMargins(40, 28, 40, 28)

        layout.addLayout(title_row)
        layout.addWidget(subtitle)

        layout.addSpacerItem(
            QSpacerItem(
                0, 6,
                QSizePolicy.Minimum,
                QSizePolicy.Fixed
            )
        )

        # =========================================================
        # FILA INPUT
        # =========================================================

        input_row = QHBoxLayout()

        input_row.setSpacing(12)
        input_row.setAlignment(Qt.AlignCenter)

        input_row.addWidget(lbl_name)
        input_row.addWidget(self.name_input)

        layout.addLayout(input_row)

        layout.addSpacerItem(
            QSpacerItem(
                0, 8,
                QSizePolicy.Minimum,
                QSizePolicy.Fixed
            )
        )

        layout.addWidget(self.btn_enter)

        # =========================================================
        # CONTENEDOR
        # =========================================================

        widget = QWidget()

        widget.setStyleSheet("""
            background-color: #f5e6c8;
        """)

        widget.setLayout(layout)

        self.setCentralWidget(widget)

        self.setFixedSize(480, 230)

    # =============================================================
    # ENTRAR AL JUEGO
    # =============================================================

    def enter_game(self):

        # Evitar doble click rápido
        self.btn_enter.setEnabled(False)

        try:

            name = self.name_input.text().strip()

            # =====================================================
            # VALIDACIONES
            # =====================================================

            if not name:
                self._warn(
                    "Atención",
                    "Por favor ingresa tu nombre de jugador."
                )
                return

            if len(name) < 2:
                self._warn(
                    "Nombre muy corto",
                    "El nombre debe tener al menos 2 caracteres."
                )
                return

            if len(name) > 20:
                self._warn(
                    "Nombre muy largo",
                    "El nombre no puede tener más de 20 caracteres."
                )
                return

            # Solo letras, números, espacios y _
            if not name.replace("_", "").replace(" ", "").isalnum():
                self._warn(
                    "Nombre inválido",
                    "Usa solo letras, números, espacios o guiones bajos."
                )
                return

            # =====================================================
            # ABRIR JUEGO
            # =====================================================

            self.game_window = GameWindow(name)

            self.game_window.show()

            self.hide()

        except Exception as e:

            self._warn(
                "Error",
                f"No se pudo iniciar el juego:\n\n{e}"
            )

        finally:
            self.btn_enter.setEnabled(True)

    # =============================================================
    # MENSAJES
    # =============================================================

    def _warn(self, title, text):

        msg = QMessageBox(self)

        msg.setIcon(QMessageBox.Warning)

        msg.setWindowTitle(title)

        msg.setText(text)

        msg.setStandardButtons(QMessageBox.Ok)

        msg.exec()

    # =============================================================
    # CIERRE LIMPIO
    # =============================================================

    def closeEvent(self, event):

        QApplication.quit()

        event.accept()


# ================================================================
# MAIN
# ================================================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    win = LoginWindow()

    win.show()

    sys.exit(app.exec_())
