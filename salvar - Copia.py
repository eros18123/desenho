# -*- coding: utf-8 -*-
import base64
from aqt import mw
from aqt.utils import showInfo, tooltip
from aqt.editor import Editor
from aqt.browser.browser import Browser

def remove_only_drawing_html(content):
    import re
    if not content: return content
    if 'anki-drawing-image' not in content and 'data:image/png;base64' not in content: return content
    pattern1 = r'<img\s+class="anki-drawing-image"[^>]*>'
    content = re.sub(pattern1, '', content, flags=re.IGNORECASE | re.DOTALL)
    pattern2 = r'<img[^>]*src="data:image/png;base64[^>]*style="[^"]*position:\s*absolute[^"]*"[^>]*>'
    content = re.sub(pattern2, '', content, flags=re.IGNORECASE | re.DOTALL)
    pattern3 = r'<img[^>]*z-index:\s*99[^>]*>'
    content = re.sub(pattern3, '', content, flags=re.IGNORECASE | re.DOTALL)
    return content

def handle_save_message(message, context):
    try:
        parts = message.split("::तां::")
        header = parts[0].replace("saveDrawing:", "")
        img_html = parts[1]
        clean_html_b64 = parts[2] if len(parts) > 2 else None
        header_parts = header.split(":", 1)
        card_id = int(header_parts[0])
        field_name = header_parts[1]
        card = mw.col.get_card(card_id)
        if not card: return
        note = card.note()
        if field_name in note:
            if clean_html_b64:
                base_html = base64.b64decode(clean_html_b64).decode('utf-8')
                note[field_name] = base_html + img_html
            else:
                cleaned_content = remove_only_drawing_html(note[field_name])
                note[field_name] = cleaned_content + img_html
            
            mw.col.update_note(note)
            
            if mw.state == "review" and mw.reviewer.card and mw.reviewer.card.id == card_id:
                mw.reviewer.card.load()
            if isinstance(context, Editor): context.loadNote(focusTo=None)
            elif isinstance(context, Browser): context.onRowChanged(None, None)
            
            if not img_html:
                tooltip("Desenho Removido (Vazio)!")
            else:
                tooltip("Desenho e texto salvos!")
    except Exception as e:
        showInfo(f"Erro ao salvar: {e}")

JS_SALVAR = """
    saveBtn.addEventListener('click', () => {
        if (textInputBox.style.display === 'block') {
            if (typeof textBlurTimeout !== 'undefined') clearTimeout(textBlurTimeout);
            commitText();
        }
        saveDrawingToField();
    });

    function saveDrawingToField() {
        let targetField = window.lastActiveEditableField;
        if (!targetField || !document.body.contains(targetField)) {
            const existingImg = document.querySelector('img.anki-drawing-image');
            if (existingImg) targetField = existingImg.closest('.editable-field');
        }
        if (!targetField) targetField = document.querySelector('.editable-field');
        
        if (!targetField && drawingHistory.length === 0 && window.lastDrawingContext.cardId) {
             pycmd(`clearDrawing:${window.lastDrawingContext.cardId}:${window.lastDrawingContext.fieldName}`);
             return;
        }
        if (!targetField) { 
            if (drawingHistory.length > 0) alert("ERRO: Nenhum campo editável foi encontrado para salvar o desenho."); 
            return; 
        }
        
        window.updateDrawingContext(targetField.dataset.cardId, targetField.dataset.fieldName);
        const cardId = targetField.dataset.cardId;
        const fieldName = targetField.dataset.fieldName;
        
        let clone = targetField.cloneNode(true);
        clone.querySelectorAll('.anki-drawing-image').forEach(img => img.remove());
        let cleanHtml = clone.innerHTML;
        
        if (drawingHistory.length === 0) { 
            pycmd(`clearDrawing:${cardId}:${fieldName}`);
            return; 
        }

        // Cria uma cópia profunda do histórico para manipulação
        const historyToSave = JSON.parse(JSON.stringify(drawingHistory));

        // =================================================================
        // CORREÇÃO CRÍTICA PARA IMAGENS E BALDE DE TINTA:
        // O JSON.stringify remove o elemento 'imgElement' (DOM).
        // Precisamos reanexar a imagem já carregada do histórico original.
        // =================================================================
        historyToSave.forEach((item) => {
            if (item.type === 'fill' || item.type === 'external_image') { // <--- ADICIONADO external_image
                const original = drawingHistory.find(orig => orig.id === item.id);
                if (original && original.imgElement) {
                    item.imgElement = original.imgElement;
                }
            }
        });

        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        historyToSave.forEach(obj => { 
            const bounds = getObjectBounds(obj); 
            minX = Math.min(minX, bounds.x); 
            minY = Math.min(minY, bounds.y); 
            maxX = Math.max(maxX, bounds.x + bounds.w); 
            maxY = Math.max(maxY, bounds.y + bounds.h); 
        });
        
        const padding = 5; 
        minX -= padding; minY -= padding; maxX += padding; maxY += padding;
        const width = maxX - minX; const height = maxY - minY;
        
        if (width <= 0 || height <= 0) {
            pycmd(`clearDrawing:${cardId}:${fieldName}`);
            return;
        }
        
        const tempCanvas = document.createElement('canvas'); tempCanvas.width = width; tempCanvas.height = height;
        const tempCtx = tempCanvas.getContext('2d'); 
        
        tempCtx.translate(-minX, -minY);
        let layers = []; let processed = new Set();
        historyToSave.forEach(item => {
            if (processed.has(item.id)) return;
            if (item.group) {
                const groupItems = historyToSave.filter(h => h.group === item.group);
                layers.push(groupItems);
                groupItems.forEach(g => processed.add(g.id));
            } else {
                layers.push([item]);
                processed.add(item.id);
            }
        });
        
        // Renderiza usando a cópia que agora tem as imagens reanexadas
        layers.forEach(layer => renderLayerToContext(tempCtx, layer));
        
        const imgData = tempCtx.getImageData(0, 0, width, height);
        let hasPixels = false;
        for (let i = 3; i < imgData.data.length; i += 4) { if (imgData.data[i] > 0) { hasPixels = true; break; } }

        let imgHtml = "";
        if (hasPixels) {
            const dataURL = tempCanvas.toDataURL('image/png');
            const fieldRect = targetField.getBoundingClientRect();
            const relLeft = minX - fieldRect.left; const relTop = minY - fieldRect.top;
            
            // Remove propriedades temporárias antes de salvar no JSON do cartão
            const cleanHistory = historyToSave.map(obj => { 
                const { fromSaved, imgElement, ...rest } = obj; 
                return rest; 
            });
            
            const historyJson = JSON.stringify(cleanHistory);
            const escapedHistory = historyJson.replace(/'/g, "&apos;").replace(/"/g, '&quot;');
            imgHtml = `<img class="anki-drawing-image" src="${dataURL}" data-drawing-history='${escapedHistory}' style="position: absolute; left: ${relLeft}px; top: ${relTop}px; z-index: 1;">`;
            
            pycmd(`saveDrawing:${cardId}:${fieldName}::तां::${imgHtml}::तां::${window.utf8_to_b64(cleanHtml)}`);
        } else {
             pycmd(`clearDrawing:${cardId}:${fieldName}`);
             return;
        }
        
        drawingHistory.forEach(obj => {
            obj.fromSaved = true;
        });
    }
"""