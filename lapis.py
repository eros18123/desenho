# -*- coding: utf-8 -*-
from .atalhos import load_general_config, save_general_config

def handle_state_save(message):
    try:
        parts = message.split(":")
        key = parts[1]
        value = parts[2]
        config = load_general_config()
        
        if key in ["pencilSize", "eraserSize", "shapeSize", "textSize"]:
            config[key] = int(value)
        elif key == "lastFilled":
            config[key] = (value == "true")
        else:
            config[key] = value
            
        save_general_config(config)
    except: pass

JS_LAPIS = """
    pencilBtn.addEventListener('click', () => setTool('pencil'));
    pencilBtn.addEventListener('dblclick', (e) => { e.preventDefault(); e.stopPropagation(); setTool('none'); });

    // Lógica de desenho do lápis está integrada no evento mousemove global
    // mas depende das variáveis configuradas aqui
    
    colorSwatches.forEach(s => s.addEventListener('click', () => { 
        const newColor = s.dataset.color;
        
        if (currentTool === 'shapes') {
            window.colorSizeMemory.shape[currentPencilColor] = currentShapeSize;
        } else if (currentTool === 'text') {
            window.colorSizeMemory.text[currentPencilColor] = currentTextSize;
        } else {
            window.colorSizeMemory.pencil[currentPencilColor] = currentPencilSize;
        }

        currentPencilColor = newColor; 
        document.querySelector('.color-swatch.active-color').classList.remove('active-color'); 
        s.classList.add('active-color'); 
        window.persistentDrawingState.color = currentPencilColor; 
        
        if (currentTool === 'shapes') {
            if (window.colorSizeMemory.shape[newColor]) currentShapeSize = window.colorSizeMemory.shape[newColor];
            brushSizeSlider.value = currentShapeSize;
            if (brushSizeValue) brushSizeValue.textContent = currentShapeSize;
            window.persistentDrawingState.shapeSize = currentShapeSize;
        } else if (currentTool === 'text') {
            if (window.colorSizeMemory.text[newColor]) currentTextSize = window.colorSizeMemory.text[newColor];
            brushSizeSlider.value = currentTextSize;
            if (brushSizeValue) brushSizeValue.textContent = currentTextSize;
            window.persistentDrawingState.textSize = currentTextSize;
        } else {
            if (window.colorSizeMemory.pencil[newColor]) currentPencilSize = window.colorSizeMemory.pencil[newColor];
            brushSizeSlider.value = currentPencilSize;
            if (brushSizeValue) brushSizeValue.textContent = currentPencilSize;
            window.persistentDrawingState.pencilSize = currentPencilSize;
        }
        
        // Atualiza cor da tabela se estiver editando
        if (textInputBox.style.display === 'block' && textInputBox.dataset.tableCell && textInputBox.dataset.editingId) {
            textInputBox.style.color = currentPencilColor;
            const targetObj = drawingHistory.find(o => o.id === textInputBox.dataset.editingId);
            if (targetObj) {
                if (!targetObj.cellData) targetObj.cellData = {};
                let currentData = targetObj.cellData[textInputBox.dataset.tableCell];
                if (typeof currentData !== 'object') {
                    currentData = { text: textInputBox.value, color: currentPencilColor, size: currentTextSize };
                } else {
                    currentData.color = currentPencilColor;
                }
                targetObj.cellData[textInputBox.dataset.tableCell] = currentData;
                redrawHistory();
            }
        }
        window.saveToolStateToPython();
    }));
    
    brushSizeSlider.addEventListener('input', (e) => {
        const newSize = e.target.value;
        if (brushSizeValue) brushSizeValue.textContent = newSize;
        
        if (currentTool === 'eraser') { 
            currentEraserSize = newSize; 
            window.persistentDrawingState.eraserSize = newSize; 
            eraserCursor.style.width = `${newSize}px`; 
            eraserCursor.style.height = `${newSize}px`; 
        }
        else if (currentTool === 'shapes') { 
            currentShapeSize = newSize; 
            window.persistentDrawingState.shapeSize = newSize;
            window.colorSizeMemory.shape[currentPencilColor] = newSize;
        }
        else if (currentTool === 'text') { 
            currentTextSize = newSize; 
            window.persistentDrawingState.textSize = newSize; 
            window.colorSizeMemory.text[currentPencilColor] = newSize;
            
            if (textInputBox.style.display === 'block' && textInputBox.dataset.tableCell && textInputBox.dataset.editingId) {
                textInputBox.style.fontSize = `${parseInt(newSize) + 10}px`;
                const targetObj = drawingHistory.find(o => o.id === textInputBox.dataset.editingId);
                if (targetObj) {
                    if (!targetObj.cellData) targetObj.cellData = {};
                    let currentData = targetObj.cellData[textInputBox.dataset.tableCell];
                    if (typeof currentData !== 'object') {
                        currentData = { text: textInputBox.value, color: currentPencilColor, size: newSize };
                    } else {
                        currentData.size = newSize;
                    }
                    targetObj.cellData[textInputBox.dataset.tableCell] = currentData;
                    redrawHistory();
                }
            }
        }
        else { 
            currentPencilSize = newSize; 
            window.persistentDrawingState.pencilSize = newSize;
            window.colorSizeMemory.pencil[currentPencilColor] = newSize;
        }
    });
    
    brushSizeSlider.addEventListener('change', (e) => {
        window.saveToolStateToPython();
    });
"""