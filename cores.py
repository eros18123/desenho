# -*- coding: utf-8 -*-

JS_CORES = """
    // ============================================================
    // LÓGICA DO SELETOR DE CORES (PALETA COMPLETA)
    // ============================================================
    
    const customColorPicker = document.getElementById('customColorPicker');
    const customColorBtn = document.getElementById('customColorBtn');

    if (customColorPicker && customColorBtn) {
        
        // Quando o usuário escolhe uma cor na paleta
        customColorPicker.addEventListener('input', (e) => {
            const newColor = e.target.value;
            
            // Atualiza variáveis globais
            currentPencilColor = newColor;
            window.persistentDrawingState.color = newColor;
            
            // Remove a classe 'active-color' dos botões padrões
            document.querySelectorAll('.color-swatch.active-color').forEach(el => el.classList.remove('active-color'));
            
            // Adiciona 'active-color' ao botão do arco-íris
            customColorBtn.classList.add('active-color');
            
            // Atualiza a memória de tamanho para essa cor (usa o tamanho atual)
            if (currentTool === 'shapes') {
                window.colorSizeMemory.shape['custom'] = currentShapeSize;
            } else if (currentTool === 'text') {
                window.colorSizeMemory.text['custom'] = currentTextSize;
            } else {
                window.colorSizeMemory.pencil['custom'] = currentPencilSize;
            }
            
            // Se estiver editando texto/tabela, atualiza a cor em tempo real
            if (textInputBox.style.display === 'block') {
                textInputBox.style.color = newColor;
                if (textInputBox.dataset.tableCell && textInputBox.dataset.editingId) {
                    // Lógica de atualização da tabela (duplicada do lapis.py para garantir funcionamento)
                    const targetObj = drawingHistory.find(o => o.id === textInputBox.dataset.editingId);
                    if (targetObj) {
                        if (!targetObj.cellData) targetObj.cellData = {};
                        let currentData = targetObj.cellData[textInputBox.dataset.tableCell];
                        if (typeof currentData !== 'object') {
                            currentData = { text: textInputBox.value, color: newColor, size: currentTextSize };
                        } else {
                            currentData.color = newColor;
                        }
                        targetObj.cellData[textInputBox.dataset.tableCell] = currentData;
                        redrawHistory();
                    }
                }
            }
        });

        // Salva o estado quando fecha a paleta
        customColorPicker.addEventListener('change', (e) => {
            window.saveToolStateToPython();
        });
        
        // Se clicar no botão colorido (mas não no input, embora o label propague), garante a ativação
        customColorBtn.addEventListener('click', (e) => {
            // Se já tiver uma cor selecionada no picker, reativa ela
            if (currentPencilColor !== customColorPicker.value) {
                currentPencilColor = customColorPicker.value;
                window.persistentDrawingState.color = currentPencilColor;
                
                document.querySelectorAll('.color-swatch.active-color').forEach(el => el.classList.remove('active-color'));
                customColorBtn.classList.add('active-color');
                window.saveToolStateToPython();
            }
        });
    }
"""