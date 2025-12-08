# -*- coding: utf-8 -*-
import json
from aqt import mw
from aqt.qt import QFontDialog, QFont

# Variável global para lembrar a última fonte escolhida
g_last_font = QFont()
g_last_font.setFamily("Arial")
g_last_font.setPointSize(16)

# --- LADO PYTHON ---
def handle_font_request():
    global g_last_font
    try:
        font, ok = QFontDialog.getFont(g_last_font, mw, "Selecionar Fonte")
        if ok:
            g_last_font = font
            return {
                "family": font.family(),
                "size": font.pointSize(),
                "bold": font.bold(),
                "italic": font.italic()
            }
    except:
        pass
    return None

# --- LADO JAVASCRIPT ---
JS_TEXTO = """
    if (!window.currentFontFamily) {
        window.currentFontFamily = 'sans-serif';
    }

    textBtn.addEventListener('click', () => {
        setTool('text');
        ensureFontButtonExists();
    });

    function ensureFontButtonExists() {
        const optionsContainer = document.getElementById('pencilOptions');
        if (!optionsContainer) return;

        // Define o container como relativo para podermos posicionar o botão "Aa" de forma absoluta dentro dele
        optionsContainer.style.position = 'relative';
        // Garante uma altura mínima para caber os sliders e sobrar espaço embaixo
        optionsContainer.style.minHeight = '110px'; 

        if (!document.getElementById('fontSelectBtn')) {
            const fontBtn = document.createElement('div');
            fontBtn.id = 'fontSelectBtn';
            fontBtn.className = 'tool-btn';
            fontBtn.title = 'Alterar Fonte e Tamanho (Aa)';
            fontBtn.innerHTML = '<span style="font-weight:bold; font-family: serif; font-size: 14px;">Aa</span>';
            
            // --- ESTILIZAÇÃO PARA POSICIONAR EMBAIXO DA BARRA DE TAMANHO ---
            fontBtn.style.position = 'absolute';
            fontBtn.style.bottom = '2px';  // Cola no fundo
            
            // MUDANÇA AQUI: Em vez de 'right', usamos 'left' para ficar ao lado das cores
            // 35px é o suficiente para pular a coluna de cores (que tem uns 25-30px)
            fontBtn.style.left = '35px';   
            fontBtn.style.right = 'auto';
            
            fontBtn.style.width = '28px';
            fontBtn.style.height = '28px';
            fontBtn.style.zIndex = '10';
            fontBtn.style.backgroundColor = 'rgba(255, 255, 255, 0.1)'; // Fundo sutil
            
            optionsContainer.appendChild(fontBtn);

            fontBtn.addEventListener('click', () => {
                pycmd('chooseFont', (response) => {
                    if (response && response !== 'null') {
                        try {
                            const fontData = JSON.parse(response);
                            const newFont = fontData.family;
                            const newSize = fontData.size;

                            window.currentFontFamily = newFont;
                            
                            if (newSize && newSize > 0) {
                                currentTextSize = newSize;
                                window.persistentDrawingState.textSize = newSize;
                                
                                const slider = document.getElementById('brushSizeSlider');
                                const display = document.getElementById('brushSizeValue');
                                if (slider) slider.value = newSize;
                                if (display) display.textContent = newSize;
                                
                                if (window.colorSizeMemory && window.colorSizeMemory.text) {
                                    window.colorSizeMemory.text[currentPencilColor] = newSize;
                                }
                            }

                            if (textInputBox.style.display === 'block') {
                                textInputBox.style.fontFamily = newFont;
                                textInputBox.style.fontSize = (parseInt(currentTextSize) + 10) + 'px';
                                
                                if (textInputBox.dataset.editingId) {
                                    const targetObj = drawingHistory.find(o => o.id === textInputBox.dataset.editingId);
                                    if (targetObj) {
                                        if (textInputBox.dataset.tableCell) {
                                            if (!targetObj.cellData) targetObj.cellData = {};
                                            let currentData = targetObj.cellData[textInputBox.dataset.tableCell];
                                            if (typeof currentData !== 'object') {
                                                currentData = { 
                                                    text: textInputBox.value, 
                                                    color: currentPencilColor, 
                                                    size: currentTextSize, 
                                                    font: newFont 
                                                };
                                            } else {
                                                currentData.font = newFont;
                                                currentData.size = currentTextSize;
                                            }
                                            targetObj.cellData[textInputBox.dataset.tableCell] = currentData;
                                        } else {
                                            targetObj.font = newFont;
                                            targetObj.size = currentTextSize;
                                        }
                                        redrawHistory();
                                    }
                                }
                            }
                        } catch(e) {
                            console.error("Erro ao processar fonte:", e);
                        }
                    }
                });
            });
        }
        
        const fontBtn = document.getElementById('fontSelectBtn');
        // Mostra o botão se for Texto, Tabela ou estiver editando
        if (currentTool === 'text' || currentTool === 'table_drawing' || (textInputBox.style.display === 'block')) {
            fontBtn.style.display = 'flex';
        } else {
            fontBtn.style.display = 'none';
        }
    }

    const originalUpdateToolUI_Text = window.updateToolUI || function(){};
    window.updateToolUI = function() {
        if (typeof originalUpdateToolUI_Text === 'function') originalUpdateToolUI_Text();
        const fontBtn = document.getElementById('fontSelectBtn');
        if (fontBtn) {
            if (currentTool === 'text' || (textInputBox.style.display === 'block')) {
                fontBtn.style.display = 'flex';
            } else {
                fontBtn.style.display = 'none';
            }
        }
    };

    function drawText(ctx, textObj) { 
        let sizeVal = parseInt(textObj.size);
        if (isNaN(sizeVal) || sizeVal <= 0) sizeVal = 16;
        
        const fontSize = sizeVal + 10; 
        
        let fontName = textObj.font || 'sans-serif';
        fontName = fontName.replace(/"/g, ""); 
        
        ctx.font = `${fontSize}px "${fontName}"`; 
        ctx.textBaseline = 'top'; 
        const lineHeight = fontSize * 1.2;
        
        const lines = textObj.text.split('\\\\n'); 
        
        for (let i = 0; i < lines.length; i++) { 
            ctx.fillText(lines[i], textObj.x, textObj.y + (i * lineHeight)); 
        } 
    }

    function handleTextToolClick(e) { 
        delete textInputBox.dataset.editingId;
        delete textInputBox.dataset.tableCell;
        textCommitData = { x: e.offsetX, y: e.offsetY }; 
        
        textInputBox.style.left = e.clientX + 'px'; 
        textInputBox.style.top = e.clientY + 'px'; 
        textInputBox.style.width = '200px';
        textInputBox.style.height = 'auto';
        textInputBox.style.color = currentPencilColor; 
        
        const size = parseInt(currentTextSize) || 16;
        textInputBox.style.fontSize = `${size + 10}px`; 
        
        textInputBox.style.fontFamily = window.currentFontFamily;
        
        textInputBox.style.display = 'block'; 
        textInputBox.value = ''; 
        setTimeout(() => textInputBox.focus(), 0); 
        canvas.style.pointerEvents = 'none'; 
        
        ensureFontButtonExists();
    }
    
    function commitText() { 
        if (textInputBox.style.display === 'none') return;

        const textValue = textInputBox.value; 
        const editingId = textInputBox.dataset.editingId;
        const tableCell = textInputBox.dataset.tableCell;
        
        const usedFont = (textInputBox.style.fontFamily || 'sans-serif').replace(/"/g, "");

        if (textValue || tableCell) { 
            saveState(); 
            isClearing = false; 
            
            if (tableCell && editingId) {
                const targetObj = drawingHistory.find(o => o.id === editingId);
                if (targetObj) {
                    if (!targetObj.cellData) targetObj.cellData = {};
                    let currentData = targetObj.cellData[tableCell];
                    if (typeof currentData !== 'object') {
                        currentData = { 
                            text: textValue, 
                            color: currentPencilColor, 
                            size: currentTextSize, 
                            font: usedFont 
                        };
                    } else {
                        currentData.text = textValue;
                        currentData.font = usedFont;
                        currentData.size = currentTextSize;
                    }
                    targetObj.cellData[tableCell] = currentData;
                }
            } else if (editingId) { 
                const targetObj = drawingHistory.find(o => o.id === editingId);
                if (targetObj) {
                    targetObj.text = textValue; 
                    
                    let newSize = parseInt(textInputBox.style.fontSize);
                    if (!isNaN(newSize)) {
                        targetObj.size = newSize - 10; 
                    }
                    
                    targetObj.color = textInputBox.style.color; 
                    targetObj.font = usedFont;
                    
                    if (selectedObject && selectedObject.id === editingId) {
                        selectedObject = targetObj;
                    }
                }
            } else if (textValue) { 
                drawingHistory.push({ 
                    id: crypto.randomUUID(), type: 'text', text: textValue, 
                    x: textCommitData.x, y: textCommitData.y, 
                    color: currentPencilColor, size: currentTextSize, 
                    font: window.currentFontFamily, 
                    group: crypto.randomUUID() 
                }); 
            } 
            redoStack = [];
            redrawHistory(); 
        } 
        
        textInputBox.style.display = 'none'; 
        textInputBox.value = ''; 
        tableTextToolbar.style.display = 'none'; 
        delete textInputBox.dataset.editingId; 
        delete textInputBox.dataset.tableCell;
        updateToolUI(); 
    }
    
    textInputBox.addEventListener('blur', (e) => {
        textBlurTimeout = setTimeout(() => {
            if (document.activeElement !== tableTextSizeSlider && 
                !document.activeElement.closest('#fontSelectBtn')) {
                commitText();
            }
        }, 150);
    });

    textInputBox.addEventListener('keydown', (ev) => { 
        if (ev.key === 'Enter' && !ev.shiftKey && !textInputBox.dataset.tableCell) { 
            ev.preventDefault(); 
            textInputBox.blur(); 
        } 
        if (ev.key === 'Escape') { 
            ev.preventDefault(); 
            textInputBox.value = ''; 
            textInputBox.blur(); 
        } 
    });
    
    textInputBox.addEventListener('input', () => {
        if (textInputBox.dataset.tableCell && textInputBox.dataset.editingId) {
            const targetObj = drawingHistory.find(o => o.id === textInputBox.dataset.editingId);
            if (targetObj) {
                if (!targetObj.cellData) targetObj.cellData = {};
                let currentData = targetObj.cellData[textInputBox.dataset.tableCell];
                const currentFont = (textInputBox.style.fontFamily || 'sans-serif').replace(/"/g, "");
                
                if (typeof currentData !== 'object') {
                    currentData = { text: textInputBox.value, color: 'black', size: 16, font: currentFont };
                } else {
                    currentData.text = textInputBox.value;
                    currentData.font = currentFont;
                }
                targetObj.cellData[textInputBox.dataset.tableCell] = currentData;
                redrawHistory(); 
            }
        }
    });
"""