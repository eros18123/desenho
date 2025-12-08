# -*- coding: utf-8 -*-
import base64
import re
from anki.template import TemplateRenderContext

# Filtro Python para tornar o campo editável
def edit_field_filter(field_text: str, field_name: str, filter_name: str, context: TemplateRenderContext) -> str:
    if filter_name != "edit": return field_text
    card = context.card()
    if not card: return field_text
    original_content = context.note()[field_name]
    encoded_original_content = base64.b64encode(original_content.encode('utf-8')).decode('utf-8')
    wrapper = (f'<div class="editable-field" style="position: relative;" '
               f'data-card-id="{card.id}" '
               f'data-field-name="{field_name}" '
               f'data-original-content="{encoded_original_content}">'
               f'{field_text}</div>')
    return wrapper

# JavaScript para edição e atalhos de cor
JS_DIGITAR = """
if (!window.inlineEditingEnabled) {
    window.inlineEditingEnabled = true;
    window.lastActiveEditableField = null;
    window.b64_to_utf8 = (str) => { try { return decodeURIComponent(escape(window.atob(str))); } catch (e) { return atob(str); } };
    window.utf8_to_b64 = (str) => { try { return window.btoa(unescape(encodeURIComponent(str))); } catch (e) { return btoa(str); } };

    window.insertDataFromPython = (content) => {
        document.execCommand('insertHTML', false, content);
    };

    const handleSymbolReplacement = (event) => {
        const fieldElement = event.target;
        if (typeof window.revisorSymbolMap === 'undefined') return;
        const regex = /:([a-zA-Z0-9_/\\-]+):/g;
        let newHTML = fieldElement.innerHTML.replace(regex, (match, code) => {
            return window.revisorSymbolMap[match] || match;
        });
        if (newHTML !== fieldElement.innerHTML) {
            const selection = window.getSelection();
            const range = selection.getRangeAt(0);
            fieldElement.innerHTML = newHTML;
            try {
                const newRange = document.createRange();
                newRange.selectNodeContents(fieldElement);
                newRange.collapse(false);
                selection.removeAllRanges();
                selection.addRange(newRange);
            } catch(e) {}
        }
    };
    
    window.startEditing = (fieldElement, skipReset = false) => {
        if (!fieldElement || fieldElement.isContentEditable) return;
        window.lastActiveEditableField = fieldElement;
        if (window.updateDrawingContext) window.updateDrawingContext(fieldElement.dataset.cardId, fieldElement.dataset.fieldName);

        const fieldName = fieldElement.dataset.fieldName;
        const encodedContent = fieldElement.dataset.originalContent;
        if (!fieldName || !encodedContent) return;
        
        const originalFieldContent = window.b64_to_utf8(encodedContent);
        const renderedHtml = fieldElement.innerHTML;
        
        if (!skipReset) fieldElement.innerHTML = originalFieldContent;
        
        fieldElement.contentEditable = true;
        fieldElement.style.outline = '2px solid #00aaff';
        fieldElement.style.display = 'block'; 
        if (!skipReset) fieldElement.focus();

        const cleanupListeners = () => {
            fieldElement.removeEventListener('blur', onBlur);
            fieldElement.removeEventListener('keydown', handleKeydown);
            fieldElement.removeEventListener('input', handleSymbolReplacement);
        };
        
        const saveChanges = (shouldResetPage, keepEditing = false) => {
            let newHtml = fieldElement.innerHTML;
            
            if (!keepEditing) {
                fieldElement.contentEditable = false;
                fieldElement.style.outline = 'none';
                fieldElement.style.display = '';
                cleanupListeners();
            }
            
            if (originalFieldContent.trim() !== newHtml.trim()) {
                const command = shouldResetPage ? "editField:reset:" : "editField:silent:";
                pycmd(`${command}${fieldElement.dataset.cardId}:${fieldName}::तां::${newHtml}`);
                if (!shouldResetPage) fieldElement.dataset.originalContent = window.utf8_to_b64(newHtml);
            } else if (!keepEditing && !skipReset) {
                fieldElement.innerHTML = renderedHtml;
            }
        };

        const onBlur = () => saveChanges(false);
        const handleKeydown = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { 
                if (e.target.closest('td')) return;
                e.preventDefault(); fieldElement.blur(); return; 
            }
            if (e.key === 'Escape') { e.preventDefault(); fieldElement.innerHTML = renderedHtml; fieldElement.contentEditable = false; fieldElement.style.outline = 'none'; cleanupListeners(); }

            // --- ATALHOS DE COR (SHIFT + LETRA) ---
            if (e.shiftKey && !e.ctrlKey && !e.altKey && !e.metaKey) {
                let color = null;
                switch (e.key.toLowerCase()) {
                    case 'r': color = '#FF4D4D'; break; // Vermelho
                    case 'z': color = '#4D96FF'; break; // Azul
                    case 'v': color = '#52D681'; break; // Verde
                    case 'a': color = '#FFD93D'; break; // Amarelo
                }
                if (color) {
                    e.preventDefault();
                    document.execCommand('styleWithCSS', false, true);
                    document.execCommand('hiliteColor', false, color);
                    document.execCommand('foreColor', false, '#000000');
                    document.execCommand('styleWithCSS', false, false);
                    saveChanges(false, true);
                    return;
                }
            }
            if (e.ctrlKey && e.key.toLowerCase() === 's') {
                 e.preventDefault();
                 document.execCommand('styleWithCSS', false, true);
                 document.execCommand('hiliteColor', false, 'transparent');
                 document.execCommand('styleWithCSS', false, false);
                 saveChanges(false, true);
                 return;
            }
        };

        fieldElement.addEventListener('blur', onBlur);
        fieldElement.addEventListener('keydown', handleKeydown);
        fieldElement.addEventListener('input', handleSymbolReplacement);
    };

    document.body.addEventListener('click', (event) => {
        const fieldElement = event.target.closest('.editable-field');
        if (fieldElement) {
            window.lastActiveEditableField = fieldElement;
            window.startEditing(fieldElement, false);
        }
    }, true);
    
    document.addEventListener('contextmenu', (event) => {
        const fieldElement = event.target.closest('.editable-field[contenteditable="true"]');
        pycmd(fieldElement ? "context:editable_field" : "context:clear");
    });
}
"""