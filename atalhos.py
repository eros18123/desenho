# -*- coding: utf-8 -*-
import os
import json
from aqt import mw
from aqt.utils import tooltip
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QLineEdit, 
                             QDialogButtonBox, QLabel, QGroupBox, QCheckBox, QComboBox, QPushButton,
                             QScrollArea, QWidget)
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtCore import Qt

from .ingles import translations as en_translations

# --- CONFIGURAÇÃO DE ARQUIVOS ---
ADDON_FOLDER = os.path.dirname(__file__)
ZOOM_CONFIG_FILE = os.path.join(ADDON_FOLDER, "zoom_config.json")
SHORTCUT_CONFIG_FILE = os.path.join(ADDON_FOLDER, "drawing_shortcuts.json")
GENERAL_CONFIG_FILE = os.path.join(ADDON_FOLDER, "general_config.json")
UI_STATE_FILE = os.path.join(ADDON_FOLDER, "ui_state.json")

# --- PADRÕES ---
DEFAULT_SHORTCUTS = {
    "select": "Ctrl+Alt+S", "pencil": "Ctrl+Alt+D", "pencil2": "Ctrl+Alt+J",
    "spray": "Ctrl+Alt+A", "eraser": "Ctrl+Alt+R", "bucket": "Ctrl+Alt+K",
    "shapes": "Ctrl+Alt+Q", "text": "Ctrl+Alt+X", "scissors": "Ctrl+Alt+O",
    "table": "Ctrl+Alt+T", "icons": "Ctrl+Alt+I", "toggle3d": "Ctrl+Alt+3",
    "toggleBw": "Ctrl+Alt+B", "clear": "Ctrl+Alt+G", "save": "Ctrl+Alt+Z",
    "undo": "Ctrl+Z", "redo": "Ctrl+Y"
}

DEFAULT_GENERAL_CONFIG = {
    "autoClear": True, "confirmClear": True, "colorBehavior": "keep", "lastColor": "red",
    "pencilSize": 2, "eraserSize": 30, "shapeSize": 5, "textSize": 16,
    "lastShape": "arrow", "lastFilled": False, "autoSelectPencil": False,
    "lastOpacity": 1.0, "language": "pt"
}

# --- VARIÁVEL GLOBAL PARA GUARDAR A REFERÊNCIA DO ITEM DE MENU ---
g_config_action = None

# --- TRADUÇÕES ---
pt_translations = {
    "config_title": "Configurações de Desenho",
    "config_menu_entry": "Configurar Desenho (Atalhos e Opções)...",
    "shortcuts_group": "Atalhos de Teclado",
    "shortcuts_info": "Pressione o atalho (ex: Ctrl+Alt+O) para gravar, ou digite manualmente.",
    "select": "Selecionar", "pencil": "Lápis (Normal)", "pencil2": "Lápis Suave", "spray": "Spray (Aerosol)",
    "eraser": "Borracha", "bucket": "Balde de Tinta", "shapes": "Formas", "text": "Texto",
    "scissors": "Tesoura (Corte)", "table": "Tabela", "icons": "Biblioteca de Ícones",
    "toggle3d": "Efeito 3D / Sombra", "toggleBw": "Preto e Branco", "clear": "Limpar Tudo",
    "save": "Salvar", "undo": "Desfazer (Undo)", "redo": "Refazer (Redo)",
    "behavior_group": "Comportamento",
    "auto_clear_checkbox": "Apagar desenho automaticamente ao mudar de card",
    "confirm_clear_checkbox": "Exibir confirmação ao usar 'Limpar Tudo'",
    "auto_pencil_checkbox": "Selecionar Lápis automaticamente ao iniciar",
    "color_behavior_label": "Ao iniciar/mudar de baralho, a cor deve ser:",
    "color_always_red": "Sempre Vermelho (Padrão)",
    "color_keep_last": "Manter a Última Cor Usada",
    "maintenance_group": "Manutenção",
    "wipe_data_button": "Limpar Cache/Dados do Addon (Todos os Cards)",
    "settings_saved": "Configurações salvas!",
    "wipe_warning_title": "Limpeza Total do Addon",
    "wipe_warning_header": "ATENÇÃO: PERIGO!",
    "wipe_warning_body": (
        "Isso irá remover TODOS os desenhos, tabelas e formatações deste addon de TODOS os cartões da sua coleção.\n\n"
        "O texto escrito nos cartões será MANTIDO, mas os desenhos e tabelas desenhadas serão apagados permanentemente.\n\n"
        "Isso é útil para corrigir bugs ou limpar o cache, mas não pode ser desfeito.\n\n"
        "Tem certeza absoluta que deseja continuar?"
    ),
    "wiping_collection": "Limpando coleção...",
    "wipe_complete": "Limpeza concluída!\n\n{count} notas foram limpas e restauradas para o texto original.",
    "wipe_error": "Ocorreu um erro durante a limpeza: {error}"
}

def get_config_translations():
    config = load_general_config()
    lang = config.get("language", "pt")
    return en_translations if lang == "en" else pt_translations

# --- FUNÇÕES DE CONFIGURAÇÃO ---

def load_zoom_config():
    try:
        if os.path.exists(ZOOM_CONFIG_FILE):
            with open(ZOOM_CONFIG_FILE, 'r') as f:
                return json.load(f).get("zoomLevel", 1.0)
    except: pass
    return 1.0

def save_zoom_config(zoom_level):
    try:
        with open(ZOOM_CONFIG_FILE, 'w') as f:
            json.dump({"zoomLevel": zoom_level}, f)
    except: pass

def load_shortcut_config():
    config = DEFAULT_SHORTCUTS.copy()
    try:
        if os.path.exists(SHORTCUT_CONFIG_FILE):
            with open(SHORTCUT_CONFIG_FILE, 'r') as f:
                config.update(json.load(f))
    except: pass
    return config

def save_shortcut_config(config):
    try:
        with open(SHORTCUT_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except: pass

def load_general_config():
    config = DEFAULT_GENERAL_CONFIG.copy()
    try:
        if os.path.exists(GENERAL_CONFIG_FILE):
            with open(GENERAL_CONFIG_FILE, 'r') as f:
                config.update(json.load(f))
    except: pass
    return config

def save_general_config(config):
    try:
        with open(GENERAL_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except: pass

def load_ui_state():
    try:
        if os.path.exists(UI_STATE_FILE):
            with open(UI_STATE_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {"top": "10px", "left": "auto", "right": "10px"}

def save_ui_state(state):
    try:
        with open(UI_STATE_FILE, 'w') as f:
            json.dump(state, f)
    except: pass

# --- CLASSE PERSONALIZADA PARA CAPTURAR ATALHOS ---

class ShortcutInput(QLineEdit):
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        is_shortcut_attempt = (modifiers & Qt.KeyboardModifier.ControlModifier) or \
                              (modifiers & Qt.KeyboardModifier.AltModifier) or \
                              (key >= Qt.Key.Key_F1 and key <= Qt.Key.Key_F12)
        if is_shortcut_attempt:
            parts = []
            if modifiers & Qt.KeyboardModifier.ControlModifier: parts.append("Ctrl")
            if modifiers & Qt.KeyboardModifier.AltModifier: parts.append("Alt")
            if modifiers & Qt.KeyboardModifier.ShiftModifier: parts.append("Shift")
            if modifiers & Qt.KeyboardModifier.MetaModifier: parts.append("Meta")
            if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
                if parts: self.setText("+".join(parts) + "+")
            else:
                key_text = QKeySequence(key).toString()
                if key_text: parts.append(key_text)
                self.setText("+".join(parts))
            event.accept()
        else:
            super().keyPressEvent(event)

# --- INTERFACE GRÁFICA ---

class ShortcutConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.translations = get_config_translations()
        self.setWindowTitle(self.translations["config_title"])
        self.resize(700, 650) 
        self.layout = QVBoxLayout(self)
        main_widget = QWidget()
        content_layout = QVBoxLayout(main_widget)
        self.shortcuts_group = QGroupBox(self.translations["shortcuts_group"])
        self.shortcuts_layout = QGridLayout()
        self.shortcuts_layout.setHorizontalSpacing(20)
        self.inputs = {}
        current_shortcuts = load_shortcut_config()
        info_label = QLabel(self.translations["shortcuts_info"])
        info_label.setStyleSheet("color: #ff5555; font-weight: bold; margin-bottom: 5px;")
        self.shortcuts_layout.addWidget(info_label, 0, 0, 1, 4)
        ordered_keys = [
            "select", "pencil", "pencil2", "spray", "eraser", "bucket", "shapes", 
            "text", "scissors", "table", "icons", "toggle3d", "toggleBw", "clear", "save", "undo", "redo"
        ]
        split_index = 9
        for idx, key in enumerate(ordered_keys):
            label_text = self.translations.get(key, key)
            label_widget = QLabel(label_text)
            line_edit = ShortcutInput()
            val = current_shortcuts.get(key, DEFAULT_SHORTCUTS.get(key, ""))
            line_edit.setText(val)
            self.inputs[key] = line_edit
            row, col_label, col_input = (idx + 1, 0, 1) if idx < split_index else ((idx - split_index) + 1, 2, 3)
            self.shortcuts_layout.addWidget(label_widget, row, col_label)
            self.shortcuts_layout.addWidget(line_edit, row, col_input)
        self.shortcuts_layout.setColumnStretch(1, 1)
        self.shortcuts_layout.setColumnStretch(3, 1)
        self.shortcuts_group.setLayout(self.shortcuts_layout)
        content_layout.addWidget(self.shortcuts_group)
        self.general_group = QGroupBox(self.translations["behavior_group"])
        self.general_layout = QVBoxLayout()
        current_general = load_general_config()
        self.chk_auto_clear = QCheckBox(self.translations["auto_clear_checkbox"])
        self.chk_auto_clear.setChecked(current_general.get("autoClear", True))
        self.general_layout.addWidget(self.chk_auto_clear)
        self.chk_confirm_clear = QCheckBox(self.translations["confirm_clear_checkbox"])
        self.chk_confirm_clear.setChecked(current_general.get("confirmClear", True))
        self.general_layout.addWidget(self.chk_confirm_clear)
        self.chk_auto_pencil = QCheckBox(self.translations["auto_pencil_checkbox"])
        self.chk_auto_pencil.setChecked(current_general.get("autoSelectPencil", False))
        self.general_layout.addWidget(self.chk_auto_pencil)
        self.lbl_color = QLabel(self.translations["color_behavior_label"])
        self.combo_color = QComboBox()
        self.combo_color.addItem(self.translations["color_always_red"], "red")
        self.combo_color.addItem(self.translations["color_keep_last"], "keep")
        idx = self.combo_color.findData(current_general.get("colorBehavior", "red"))
        if idx >= 0: self.combo_color.setCurrentIndex(idx)
        self.general_layout.addWidget(self.lbl_color)
        self.general_layout.addWidget(self.combo_color)
        self.general_group.setLayout(self.general_layout)
        content_layout.addWidget(self.general_group)
        self.maintenance_group = QGroupBox(self.translations["maintenance_group"])
        self.maintenance_layout = QVBoxLayout()
        self.btn_wipe = QPushButton(self.translations["wipe_data_button"])
        self.btn_wipe.setStyleSheet("background-color: #ffe6e6; color: red; font-weight: bold; padding: 5px;")
        self.btn_wipe.clicked.connect(self.handle_wipe)
        self.btn_wipe.setMaximumWidth(400)
        self.maintenance_layout.addWidget(self.btn_wipe, 0, Qt.AlignmentFlag.AlignCenter)
        self.maintenance_group.setLayout(self.maintenance_layout)
        content_layout.addWidget(self.maintenance_group)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(main_widget)
        self.layout.addWidget(scroll_area)
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

    def handle_wipe(self):
        from .limpeza import on_wipe_data
        on_wipe_data()

    def get_config(self):
        new_shortcuts = {key: input_field.text().strip() or DEFAULT_SHORTCUTS.get(key, "") for key, input_field in self.inputs.items()}
        new_general = load_general_config()
        new_general.update({
            "autoClear": self.chk_auto_clear.isChecked(),
            "confirmClear": self.chk_confirm_clear.isChecked(),
            "autoSelectPencil": self.chk_auto_pencil.isChecked(),
            "colorBehavior": self.combo_color.currentData()
        })
        return new_shortcuts, new_general

def open_config_dialog():
    dialog = ShortcutConfigDialog(mw)
    if dialog.exec():
        new_shortcuts, new_general = dialog.get_config()
        save_shortcut_config(new_shortcuts)
        save_general_config(new_general)
        tooltip(get_config_translations()["settings_saved"])

def update_config_menu_text():
    """Atualiza o texto do item de menu existente usando a referência global."""
    global g_config_action
    if g_config_action:
        translations = get_config_translations()
        menu_text = translations.get("config_menu_entry", "Configure Drawing...")
        g_config_action.setText(menu_text)

def add_config_menu_item():
    """Cria, adiciona e guarda a referência do item de menu na inicialização."""
    global g_config_action
    translations = get_config_translations()
    menu_text = translations.get("config_menu_entry", "Configure Drawing...")
    
    g_config_action = QAction(menu_text, mw)
    g_config_action.triggered.connect(open_config_dialog)
    mw.form.menuTools.addAction(g_config_action)