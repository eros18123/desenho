# -*- coding: utf-8 -*-

JS_TABELA = """
    // ============================================================
    // CRIAÇÃO DA JANELA MODAL DE CONFIGURAÇÃO DA TABELA
    // ============================================================
    if (!document.getElementById('table-config-modal')) {
        const modalStyle = document.createElement('style');
        modalStyle.innerHTML = `
            #table-config-modal {
                display: none;
                position: fixed;
                top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0, 0, 0, 0.5);
                z-index: 2000;
                justify-content: center;
                align-items: center;
            }
            #table-config-content {
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                display: flex;
                flex-direction: column;
                gap: 10px;
                min-width: 200px;
            }
            .nightMode #table-config-content {
                background: #2f3136;
                color: #dcddde;
                border: 1px solid #202225;
            }
            .tbl-input-group {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .tbl-input-group input {
                width: 60px;
                padding: 4px;
                margin-left: 10px;
            }
            .tbl-buttons {
                display: flex;
                justify-content: flex-end;
                gap: 10px;
                margin-top: 10px;
            }
            .tbl-btn {
                padding: 5px 10px;
                cursor: pointer;
                border: none;
                border-radius: 4px;
            }
            .tbl-btn-ok { background: #00aaff; color: white; }
            .tbl-btn-cancel { background: #ccc; color: black; }
        `;
        document.head.appendChild(modalStyle);

        const modalDiv = document.createElement('div');
        modalDiv.id = 'table-config-modal';
        modalDiv.innerHTML = `
            <div id="table-config-content">
                <h3 style="margin: 0 0 10px 0; font-size: 16px;">Inserir Tabela</h3>
                <div class="tbl-input-group">
                    <label>Linhas:</label>
                    <input type="number" id="tbl-rows-input" value="3" min="1" max="20">
                </div>
                <div class="tbl-input-group">
                    <label>Colunas:</label>
                    <input type="number" id="tbl-cols-input" value="3" min="1" max="20">
                </div>
                <div class="tbl-buttons">
                    <button class="tbl-btn tbl-btn-cancel" id="tbl-cancel-btn">Cancelar</button>
                    <button class="tbl-btn tbl-btn-ok" id="tbl-confirm-btn">OK</button>
                </div>
            </div>
        `;
        document.body.appendChild(modalDiv);

        // Eventos da Modal
        const closeModal = () => {
            modalDiv.style.display = 'none';
        };

        const confirmTable = () => {
            const r = parseInt(document.getElementById('tbl-rows-input').value) || 3;
            const c = parseInt(document.getElementById('tbl-cols-input').value) || 3;
            tableConfig = { rows: Math.max(1, r), cols: Math.max(1, c) };
            setTool('table_drawing');
            closeModal();
        };

        document.getElementById('tbl-cancel-btn').addEventListener('click', closeModal);
        document.getElementById('tbl-confirm-btn').addEventListener('click', confirmTable);
        
        // Confirmar com Enter dentro dos inputs
        modalDiv.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') confirmTable();
            if (e.key === 'Escape') closeModal();
        });
        
        // Impedir que cliques dentro da modal desenhem no canvas
        modalDiv.addEventListener('mousedown', (e) => e.stopPropagation());
    }

    // ============================================================
    // LÓGICA DA FERRAMENTA TABELA
    // ============================================================

    tableBtn.addEventListener('click', () => {
        if (currentTool === 'table_drawing') {
            setTool('select');
            return;
        }
        // Abre a modal em vez de usar prompt
        const modal = document.getElementById('table-config-modal');
        modal.style.display = 'flex';
        
        // Foca no input de linhas
        setTimeout(() => document.getElementById('tbl-rows-input').focus(), 50);
    });

    function updateActiveTableCellStyle(newColor, newSize) {
        if (textInputBox.style.display === 'block' && textInputBox.dataset.tableCell && textInputBox.dataset.editingId) {
            const targetObj = drawingHistory.find(o => o.id === textInputBox.dataset.editingId);
            if (targetObj) {
                if (!targetObj.cellData) targetObj.cellData = {};
                let currentData = targetObj.cellData[textInputBox.dataset.tableCell];
                
                if (typeof currentData !== 'object') {
                    currentData = { text: textInputBox.value, color: 'black', size: 16 };
                }
                
                if (newColor) {
                    currentData.color = newColor;
                    textInputBox.style.color = newColor;
                }
                if (newSize) {
                    currentData.size = newSize;
                    textInputBox.style.fontSize = `${newSize}px`;
                }
                
                targetObj.cellData[textInputBox.dataset.tableCell] = currentData;
                redrawHistory();
            }
        }
    }

    tableColorSwatches.forEach(swatch => {
        swatch.addEventListener('click', (e) => {
            e.stopPropagation();
            const color = swatch.dataset.color;
            updateActiveTableCellStyle(color, null);
        });
    });

    tableTextSizeSlider.addEventListener('input', (e) => {
        e.stopPropagation();
        const size = e.target.value;
        updateActiveTableCellStyle(null, size);
    });
    
    tableTextSizeSlider.addEventListener('mousedown', (e) => e.stopPropagation());

    function wrapText(ctx, text, maxWidth) {
        const words = text.split(' ');
        let lines = [];
        let currentLine = words[0];

        for (let i = 1; i < words.length; i++) {
            const word = words[i];
            const width = ctx.measureText(currentLine + " " + word).width;
            if (width < maxWidth) {
                currentLine += " " + word;
            } else {
                lines.push(currentLine);
                currentLine = word;
            }
        }
        lines.push(currentLine);
        
        let finalLines = [];
        text.split('\\\\n').forEach(paragraph => {
             const paraWords = paragraph.split(' ');
             let line = paraWords[0] || "";
             for(let i=1; i<paraWords.length; i++) {
                 const w = paraWords[i];
                 const width = ctx.measureText(line + " " + w).width;
                 if (width < maxWidth) {
                     line += " " + w;
                 } else {
                     finalLines.push(line);
                     line = w;
                 }
             }
             finalLines.push(line);
        });
        return finalLines;
    }

    function calculateTableMetrics(ctx, tableObj) {
        const x = Math.min(tableObj.x1, tableObj.x2);
        const y = Math.min(tableObj.y1, tableObj.y2);
        const w = Math.abs(tableObj.x1 - tableObj.x2);
        const rows = tableObj.rows;
        const cols = tableObj.cols;
        const cellW = w / cols;
        
        const currentHeight = Math.abs(tableObj.y1 - tableObj.y2);
        let minRowH = 40;
        if (currentHeight > 0) {
             minRowH = Math.max(40, currentHeight / rows);
        }
        
        const padding = 10;
        let rowHeights = [];

        for (let r = 0; r < rows; r++) {
            let maxLinesInRow = 1;
            let maxLineHeightInRow = 20; 

            for (let c = 0; c < cols; c++) {
                const key = `${r}-${c}`;
                if (tableObj.cellData && tableObj.cellData[key]) {
                    let text = "", size = 16;
                    if (typeof tableObj.cellData[key] === 'object') {
                        text = tableObj.cellData[key].text;
                        size = parseInt(tableObj.cellData[key].size);
                    } else {
                        text = tableObj.cellData[key];
                    }
                    
                    ctx.font = `${size}px sans-serif`;
                    const lineHeight = size * 1.2;
                    if (lineHeight > maxLineHeightInRow) maxLineHeightInRow = lineHeight;

                    const lines = wrapText(ctx, text, cellW - padding * 2);
                    if (lines.length > maxLinesInRow) maxLinesInRow = lines.length;
                }
            }
            const calculatedH = Math.max(minRowH, maxLinesInRow * maxLineHeightInRow + padding * 2);
            rowHeights.push(calculatedH);
        }
        
        const totalH = rowHeights.reduce((a, b) => a + b, 0);
        return { rowHeights, totalH, cellW, padding };
    }

    function drawTable(ctx, tableObj) {
        const x = Math.min(tableObj.x1, tableObj.x2);
        const y = Math.min(tableObj.y1, tableObj.y2);
        const w = Math.abs(tableObj.x1 - tableObj.x2);
        
        const metrics = calculateTableMetrics(ctx, tableObj);
        const { rowHeights, totalH, cellW, padding } = metrics;

        ctx.strokeRect(x, y, w, totalH);

        let currentY = y;
        ctx.beginPath();
        for (let j = 1; j < tableObj.cols; j++) {
            ctx.moveTo(x + j * cellW, y);
            ctx.lineTo(x + j * cellW, y + totalH);
        }
        
        for (let i = 0; i < tableObj.rows; i++) {
            const rowH = rowHeights[i];
            if (i < tableObj.rows - 1) {
                ctx.moveTo(x, currentY + rowH);
                ctx.lineTo(x + w, currentY + rowH);
            }

            for (let j = 0; j < tableObj.cols; j++) {
                const key = `${i}-${j}`;
                const isBeingEdited = (tableObj.id === textInputBox.dataset.editingId && key === textInputBox.dataset.tableCell && textInputBox.style.display === 'block');
                
                if (!isBeingEdited && tableObj.cellData && tableObj.cellData[key]) {
                    let text = "", color = "black", size = 16;
                    if (typeof tableObj.cellData[key] === 'object') {
                        text = tableObj.cellData[key].text;
                        color = tableObj.cellData[key].color;
                        size = parseInt(tableObj.cellData[key].size);
                    } else {
                        text = tableObj.cellData[key];
                    }

                    ctx.font = `${size}px sans-serif`;
                    ctx.textBaseline = "top";
                    ctx.textAlign = "left";
                    ctx.fillStyle = color;
                    
                    const lineHeight = size * 1.2;
                    const lines = wrapText(ctx, text, cellW - padding * 2);
                    
                    const cellX = x + j * cellW + padding;
                    const cellY = currentY + padding;
                    
                    lines.forEach((line, idx) => {
                        ctx.fillText(line, cellX, cellY + idx * lineHeight);
                    });
                }
            }
            currentY += rowH;
        }
        ctx.stroke();
    }
"""