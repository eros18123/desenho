# -*- coding: utf-8 -*-
import re
from aqt import mw
from aqt.utils import tooltip
from aqt.editor import Editor
from aqt.browser.browser import Browser

def remove_only_drawing_html(content):
    if not content: return content
    if 'anki-drawing-image' not in content and 'data:image/png;base64' not in content: return content
    pattern1 = r'<img\s+class="anki-drawing-image"[^>]*>'
    content = re.sub(pattern1, '', content, flags=re.IGNORECASE | re.DOTALL)
    pattern2 = r'<img[^>]*src="data:image/png;base64[^>]*style="[^"]*position:\s*absolute[^"]*"[^>]*>'
    content = re.sub(pattern2, '', content, flags=re.IGNORECASE | re.DOTALL)
    pattern3 = r'<img[^>]*z-index:\s*99[^>]*>'
    content = re.sub(pattern3, '', content, flags=re.IGNORECASE | re.DOTALL)
    return content

def handle_clear_message(message, context):
    try:
        header = message.replace("clearDrawing:", "")
        header_parts = header.split(":", 1)
        card_id = int(header_parts[0])
        field_name = header_parts[1]
        card = mw.col.get_card(card_id)
        if not card: return
        note = card.note()
        if field_name in note:
            note[field_name] = remove_only_drawing_html(note[field_name])
            mw.col.update_note(note)
            
            if mw.state == "review" and mw.reviewer.card and mw.reviewer.card.id == card_id:
                mw.reviewer.card.load()
            if isinstance(context, Editor): context.loadNote(focusTo=None)
            elif isinstance(context, Browser): context.onRowChanged(None, None)
            tooltip("Desenho removido permanentemente!")
    except: pass

JS_LIMPARTUDO = """
    clearBtn.addEventListener('click', () => {
        if (window.generalConfig && window.generalConfig.confirmClear) {
            if (!confirm('Tem certeza que deseja apagar todos os desenhos e tabelas?')) return;
        }
        
        saveState(); 
        drawingHistory = []; 
        selectedGroup = [];
        selectedObject = null; 
        redrawHistory();
        
        const existingImg = document.querySelector('img.anki-drawing-image');
        if (existingImg) {
            const field = existingImg.closest('.editable-field');
            if (field) { window.updateDrawingContext(field.dataset.cardId, field.dataset.fieldName); field.dispatchEvent(new Event('input', { bubbles: true })); }
            existingImg.remove();
        }
        saveDrawingToField();
    });
"""