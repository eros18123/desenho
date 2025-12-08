# -*- coding: utf-8 -*-

JS_REDIMENSIONAR = """
    // ============================================================
    // LÓGICA DE REDIMENSIONAMENTO (MOUSE E TECLADO)
    // ============================================================
    
    const resizeHandle = document.getElementById('resizeHandle');
    const toolbar = document.getElementById('drawingTools');
    
    let isResizingToolbar = false;
    let startResizeX = 0;
    let startResizeScale = 1.0;

    // 1. Evento de Clique na Alça de Redimensionamento
    if (resizeHandle) {
        resizeHandle.addEventListener('mousedown', (e) => {
            e.preventDefault();
            e.stopPropagation(); // Impede que o arraste da caixa (mover) ative
            
            isResizingToolbar = true;
            startResizeX = e.clientX;
            startResizeScale = window.persistentDrawingState.zoomLevel || 1.0;
            
            document.body.style.cursor = 'nwse-resize';
        });
    }

    // 2. Evento de Movimento do Mouse (Global)
    window.addEventListener('mousemove', (e) => {
        if (!isResizingToolbar) return;
        
        e.preventDefault();
        
        // Calcula quanto o mouse moveu para a direita/esquerda
        const deltaX = e.clientX - startResizeX;
        
        // Sensibilidade: 300px de movimento = +1.0 de escala (ajuste conforme gosto)
        const scaleChange = deltaX / 300;
        
        let newScale = startResizeScale + scaleChange;
        
        // Limites de tamanho (0.5x até 3.0x)
        newScale = Math.max(0.5, Math.min(3.0, newScale));
        
        if (typeof applyZoom === 'function') {
            applyZoom(newScale);
        }
    });

    // 3. Soltar o Mouse
    window.addEventListener('mouseup', () => {
        if (isResizingToolbar) {
            isResizingToolbar = false;
            document.body.style.cursor = 'default';
        }
    });

    // 4. Atalhos de Teclado (Backup: Ctrl+Shift+ e Ctrl+Shift-)
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.shiftKey && !e.altKey) {
            if (e.key === '+' || e.key === '=') {
                e.preventDefault(); e.stopPropagation();
                if (typeof applyZoom === 'function') applyZoom(window.persistentDrawingState.zoomLevel + 0.1);
            }
            if (e.key === '-' || e.key === '_') {
                e.preventDefault(); e.stopPropagation();
                if (typeof applyZoom === 'function') applyZoom(window.persistentDrawingState.zoomLevel - 0.1);
            }
        }
    }, true);
"""