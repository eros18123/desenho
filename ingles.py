# ingles.py

translations = {
    # Tooltips da barra de ferramentas principal
    "select": "Select",
    "pencil": "Pencil",
    "pencil2": "Smooth Pencil",
    "text": "Text",
    "bucket": "Paint Bucket",
    "spray": "Spray",
    "scissors": "Scissors (Cut)",
    "shapes": "Shapes",
    "eraser": "Eraser",
    "table": "Insert Table",
    "icons": "Icon Library",
    "toggle3d": "3D Effect / Shadow",
    "toggleBw": "Black and White",
    "clear": "Clear All",
    "save": "Save",

    # Opções de Ferramentas
    "change_font": "Change Font and Size (Aa)",
    "more_colors": "More colors...",

    # Janela de Tabela
    "insert_table": "Insert Table",
    "rows": "Rows:",
    "columns": "Columns:",
    "cancel": "Cancel",
    "ok": "OK",

    # Janela de Ícones
    "icon_library": "Icon Library",
    "add_icon": "Add Icon",
    "close": "Close",
    "search_icon": "Search icon (e.g., arr)...",
    "loading": "Loading...",
    "empty_folder": "The folder is empty.<br><br>Click <b>+ Add</b> to import images.",
    "delete_icon_confirm": "Permanently delete the icon \"{icon_name}\"?",
    "delete_this_icon": "Delete this icon",

    # Mensagens e Alertas
    "confirm_clear_all": "Are you sure you want to erase all drawings and tables?",
    "error_no_field": "ERROR: No editable field was found to save the drawing.",
    "drawing_removed_permanently": "Drawing permanently removed!",
    "drawing_removed_empty": "Drawing Removed (Empty)!",
    "drawing_and_text_saved": "Drawing and text saved!",
    "error_saving": "Error while saving: {error}",
    "icon_added": "Icon added!",
    "icon_deleted": "Icon deleted!",
    "error_add_image": "Error adding image:\n{error}",
    "error_delete_file": "Error deleting file:\n{error}",
    "file_not_found": "Error: File not found.",

    # Configurações (atalhos.py)
    "config_title": "Drawing Settings",
    "config_menu_entry": "Configure Drawing (Shortcuts & Options)...",
    "shortcuts_group": "Keyboard Shortcuts",
    "shortcuts_info": "Press the shortcut (e.g., Ctrl+Alt+O) to record, or type it manually.",
    "behavior_group": "Behavior",
    "auto_clear_checkbox": "Automatically clear drawing when changing cards",
    "confirm_clear_checkbox": "Show confirmation when using 'Clear All'",
    "auto_pencil_checkbox": "Automatically select Pencil on startup",
    "color_behavior_label": "On startup/deck change, the color should be:",
    "color_always_red": "Always Red (Default)",
    "color_keep_last": "Keep Last Used Color",
    "maintenance_group": "Maintenance",
    "wipe_data_button": "Clear Addon Cache/Data (All Cards)",
    "settings_saved": "Settings saved! Please restart Anki for the language change in the 'Tools' menu to take effect.",
    
    # Limpeza Total (limpeza.py)
    "wipe_warning_title": "Total Addon Cleanup",
    "wipe_warning_header": "WARNING: DANGER!",
    "wipe_warning_body": (
        "This will remove ALL drawings, tables, and formatting from this addon from ALL cards in your collection.\n\n"
        "The text written on the cards will be KEPT, but the drawings and tables will be permanently deleted.\n\n"
        "This is useful for fixing bugs or clearing the cache, but it cannot be undone.\n\n"
        "Are you absolutely sure you want to continue?"
    ),
    "wiping_collection": "Wiping collection...",
    "wipe_complete": "Cleanup complete!\n\n{count} notes were cleaned and restored to their original text.",
    "wipe_error": "An error occurred during cleanup: {error}"
}