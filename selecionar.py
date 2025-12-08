# -*- coding: utf-8 -*-

JS_SELECIONAR = """
    selectBtn.addEventListener('click', () => setTool('select'));

    function copySelection() {
        if (selectedGroup.length > 0) {
            internalClipboard = {
                type: 'canvas',
                data: JSON.parse(JSON.stringify(selectedGroup))
            };
        }
    }

    function pasteSelection() {
        if (!internalClipboard) return;
        saveState();
        if (internalClipboard.type === 'canvas') {
            const offset = 20;
            const newItems = [];
            const groupMap = {}; 

            internalClipboard.data.forEach(item => {
                const newItem = JSON.parse(JSON.stringify(item));
                newItem.id = crypto.randomUUID();

                if (newItem.group) {
                    if (!groupMap[newItem.group]) {
                        groupMap[newItem.group] = crypto.randomUUID();
                    }
                    newItem.group = groupMap[newItem.group];
                }

                if (newItem.type === 'path' || newItem.type === 'eraser_path') {
                    newItem.points.forEach(p => { p.x += offset; p.y += offset; });
                } else if (newItem.type === 'shape' || newItem.type === 'table') {
                    newItem.x1 += offset; newItem.y1 += offset;
                    newItem.x2 += offset; newItem.y2 += offset;
                } else if (newItem.type === 'text') {
                    newItem.x += offset; newItem.y += offset;
                } else if (newItem.type === 'fill') {
                    if (newItem.x !== undefined) newItem.x += offset;
                    if (newItem.y !== undefined) newItem.y += offset;
                    if (newItem.bounds) {
                        newItem.bounds.x += offset;
                        newItem.bounds.y += offset;
                    }
                }
                
                // Garante que objetos colados não tenham inclinação
                newItem.skewX = 0;
                newItem.skewY = 0;

                drawingHistory.push(newItem);
                newItems.push(newItem);
            });

            selectedGroup = newItems;
            redrawHistory();
        }
    }

    function drawSelectionBox(group) {
        ctx.save();
        ctx.strokeStyle = '#00aaff';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 2]);

        // Se for apenas um objeto e ele tiver rotação, giramos a caixa de seleção
        if (group.length === 1 && group[0].rotation) {
            const obj = group[0];
            const b = getObjectBounds(obj);
            const cx = b.x + b.w / 2;
            const cy = b.y + b.h / 2;
            rotateContext(ctx, cx, cy, obj.rotation);
        }

        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        group.forEach(obj => {
            if (obj.type === 'eraser_path') return;
            const b = getObjectBounds(obj);
            minX = Math.min(minX, b.x); minY = Math.min(minY, b.y);
            maxX = Math.max(maxX, b.x + b.w); maxY = Math.max(maxY, b.y + b.h);
        });

        if (minX !== Infinity) {
            ctx.strokeRect(minX - 2, minY - 2, (maxX - minX) + 4, (maxY - minY) + 4);
        }
        ctx.restore();
    }
    
    function drawSkewHandle(ctx, x, y, size, direction) {
        ctx.save();
        ctx.fillStyle = '#6f42c1'; // Roxo para diferenciar
        ctx.strokeStyle = 'white';
        ctx.lineWidth = 2;
        ctx.fillRect(x, y, size, size);
        ctx.strokeRect(x, y, size, size);
        
        ctx.beginPath();
        ctx.strokeStyle = 'white';
        if (direction === 'horizontal') {
            ctx.moveTo(x + 4, y + size/2); ctx.lineTo(x + size - 4, y + size/2);
            ctx.moveTo(x + 6, y + size/2 - 3); ctx.lineTo(x + 4, y + size/2); ctx.lineTo(x + 6, y + size/2 + 3);
            ctx.moveTo(x + size - 6, y + size/2 - 3); ctx.lineTo(x + size - 4, y + size/2); ctx.lineTo(x + size - 6, y + size/2 + 3);
        } else { // vertical
            ctx.moveTo(x + size/2, y + 4); ctx.lineTo(x + size/2, y + size - 4);
            ctx.moveTo(x + size/2 - 3, y + 6); ctx.lineTo(x + size/2, y + 4); ctx.lineTo(x + size/2 + 3, y + 6);
            ctx.moveTo(x + size/2 - 3, y + size - 6); ctx.lineTo(x + size/2, y + size - 4); ctx.lineTo(x + size/2 + 3, y + size - 6);
        }
        ctx.stroke();
        ctx.restore();
    }

    function calculateAndDrawUI(items) {
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        
        items.forEach(obj => {
            if (obj.type === 'eraser_path') return;
            const b = getObjectBounds(obj);
            minX = Math.min(minX, b.x); minY = Math.min(minY, b.y);
            maxX = Math.max(maxX, b.x + b.w); maxY = Math.max(maxY, b.y + b.h);
        });

        if (minX === Infinity) return;
        
        const handleSize = 20;
        const isSingle = items.length === 1;
        const rotation = (isSingle && items[0].rotation) ? items[0].rotation : 0;
        
        const cx = minX + (maxX - minX) / 2;
        const cy = minY + (maxY - minY) / 2;

        ctx.save();
        
        if (rotation) {
            rotateContext(ctx, cx, cy, rotation);
        }

        // --- BOTÃO DE MOVER ---
        const moveX = minX - handleSize - 5;
        const moveY = minY - 5;
        activeUIElements.push({ type: 'MOVE', x: moveX, y: moveY, size: handleSize, items: items, rotation: rotation, center: {x: cx, y: cy} });
        ctx.fillStyle = '#00aaff'; ctx.strokeStyle = 'white'; ctx.lineWidth = 2;
        ctx.fillRect(moveX, moveY, handleSize, handleSize);
        ctx.strokeRect(moveX, moveY, handleSize, handleSize);
        ctx.beginPath();
        ctx.moveTo(moveX + handleSize/2, moveY + 4); ctx.lineTo(moveX + handleSize/2, moveY + handleSize - 4);
        ctx.moveTo(moveX + 4, moveY + handleSize/2); ctx.lineTo(moveX + handleSize - 4, moveY + handleSize/2);
        ctx.stroke();

        // --- BOTÃO DE REDIMENSIONAR ---
        const resizeX = maxX + 5;
        const resizeY = maxY + 5;
        activeUIElements.push({ type: 'RESIZE', x: resizeX, y: resizeY, size: handleSize, items: items, bounds: {x: minX, y: minY, w: maxX-minX, h: maxY-minY}, rotation: rotation, center: {x: cx, y: cy} });
        ctx.fillStyle = '#ffaa00'; ctx.strokeStyle = 'white'; ctx.lineWidth = 2;
        ctx.fillRect(resizeX, resizeY, handleSize, handleSize);
        ctx.strokeRect(resizeX, resizeY, handleSize, handleSize);
        ctx.beginPath();
        ctx.moveTo(resizeX + 4, resizeY + 4); ctx.lineTo(resizeX + handleSize - 4, resizeY + handleSize - 4);
        ctx.moveTo(resizeX + handleSize - 4, resizeY + 4); ctx.lineTo(resizeX + handleSize - 4, resizeY + handleSize - 4);
        ctx.lineTo(resizeX + 4, resizeY + handleSize - 4);
        ctx.stroke();
        
        // --- NOVAS ALÇAS DE INCLINAÇÃO (SKEW) ---
        const bounds = {x: minX, y: minY, w: maxX-minX, h: maxY-minY};
        const topSkewX = cx - handleSize/2, topSkewY = minY - handleSize - 5;
        const bottomSkewX = cx - handleSize/2, bottomSkewY = maxY + 5;
        const leftSkewX = minX - handleSize - 5, leftSkewY = cy - handleSize/2;
        const rightSkewX = maxX + 5, rightSkewY = cy - handleSize/2;

        activeUIElements.push({ type: 'SKEW', x: topSkewX, y: topSkewY, size: handleSize, items: items, bounds: bounds, direction: 'top', rotation: rotation, center: {x: cx, y: cy} });
        activeUIElements.push({ type: 'SKEW', x: bottomSkewX, y: bottomSkewY, size: handleSize, items: items, bounds: bounds, direction: 'bottom', rotation: rotation, center: {x: cx, y: cy} });
        activeUIElements.push({ type: 'SKEW', x: leftSkewX, y: leftSkewY, size: handleSize, items: items, bounds: bounds, direction: 'left', rotation: rotation, center: {x: cx, y: cy} });
        activeUIElements.push({ type: 'SKEW', x: rightSkewX, y: rightSkewY, size: handleSize, items: items, bounds: bounds, direction: 'right', rotation: rotation, center: {x: cx, y: cy} });

        drawSkewHandle(ctx, topSkewX, topSkewY, handleSize, 'horizontal');
        drawSkewHandle(ctx, bottomSkewX, bottomSkewY, handleSize, 'horizontal');
        drawSkewHandle(ctx, leftSkewX, leftSkewY, handleSize, 'vertical');
        drawSkewHandle(ctx, rightSkewX, rightSkewY, handleSize, 'vertical');


        // --- BOTÕES DE OBJETO ÚNICO (GIRAR E CONECTAR) ---
        if (isSingle) {
            const rotateX = cx - handleSize/2;
            const rotateY = minY - 35;
            activeUIElements.push({ type: 'ROTATE', x: rotateX, y: rotateY, size: handleSize, items: items, rotation: rotation, center: {x: cx, y: cy} });
            ctx.fillStyle = '#28a745'; ctx.strokeStyle = 'white'; ctx.lineWidth = 2;
            ctx.beginPath(); ctx.arc(rotateX + handleSize/2, rotateY + handleSize/2, handleSize/2, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
            ctx.beginPath(); ctx.strokeStyle = 'white'; ctx.lineWidth = 2; ctx.arc(rotateX + handleSize/2, rotateY + handleSize/2, 6, 0.2 * Math.PI, 1.8 * Math.PI); ctx.stroke();
            ctx.beginPath(); ctx.moveTo(rotateX + handleSize - 4, rotateY + handleSize/2 - 3); ctx.lineTo(rotateX + handleSize - 4, rotateY + handleSize/2 + 3); ctx.lineTo(rotateX + handleSize - 9, rotateY + handleSize/2); ctx.fill();
            ctx.beginPath(); ctx.strokeStyle = '#00aaff'; ctx.setLineDash([2, 2]); ctx.moveTo(cx, minY); ctx.lineTo(cx, rotateY + handleSize); ctx.stroke();

            const connectX = cx - handleSize / 2;
            const connectY = maxY + 15;
            activeUIElements.push({ type: 'CONNECT', x: connectX, y: connectY, size: handleSize, items: items, rotation: rotation, center: {x: cx, y: cy} });
            ctx.fillStyle = '#9400D3'; ctx.strokeStyle = 'white'; ctx.lineWidth = 2;
            ctx.beginPath(); ctx.arc(connectX + handleSize/2, connectY + handleSize/2, handleSize/2, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
            ctx.beginPath(); ctx.strokeStyle = 'white';
            ctx.moveTo(connectX + handleSize/2, connectY + 5); ctx.lineTo(connectX + handleSize/2, connectY + handleSize - 5);
            ctx.moveTo(connectX + 5, connectY + handleSize/2); ctx.lineTo(connectX + handleSize - 5, connectY + handleSize/2);
            ctx.stroke();
            ctx.beginPath(); ctx.strokeStyle = '#00aaff'; ctx.moveTo(cx, maxY); ctx.lineTo(cx, connectY); ctx.stroke(); ctx.setLineDash([]);
        }

        // Controles de Tabela
        if (items.length === 1 && items[0].type === 'table') {
            const t = items[0];
            const b = getObjectBounds(t);
            const btnSize = 20;
            const cxT = b.x + b.w / 2;
            const cyT = b.y - 25;
            drawSimpleButton(ctx, cxT - 22, cyT, btnSize, "-", "red");
            activeUIElements.push({type: 'TABLE_COL_DEC', x: cxT - 22, y: cyT, size: btnSize, item: t, rotation: rotation, center: {x: cx, y: cy}});
            drawSimpleButton(ctx, cxT + 2, cyT, btnSize, "+", "green");
            activeUIElements.push({type: 'TABLE_COL_INC', x: cxT + 2, y: cyT, size: btnSize, item: t, rotation: rotation, center: {x: cx, y: cy}});
            const rx = b.x - 25;
            const ry = b.y + b.h / 2;
            drawSimpleButton(ctx, rx, ry - 22, btnSize, "-", "red");
            activeUIElements.push({type: 'TABLE_ROW_DEC', x: rx, y: ry - 22, size: btnSize, item: t, rotation: rotation, center: {x: cx, y: cy}});
            drawSimpleButton(ctx, rx, ry + 2, btnSize, "+", "green");
            activeUIElements.push({type: 'TABLE_ROW_INC', x: rx, y: ry + 2, size: btnSize, item: t, rotation: rotation, center: {x: cx, y: cy}});
        }
        
        ctx.restore();
    }
    
    function drawSimpleButton(ctx, x, y, size, label, color) {
        ctx.save();
        ctx.fillStyle = 'white';
        ctx.strokeStyle = color;
        ctx.lineWidth = 1;
        ctx.fillRect(x, y, size, size);
        ctx.strokeRect(x, y, size, size);
        
        ctx.fillStyle = color;
        ctx.font = "bold 16px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(label, x + size/2, y + size/2 + 1);
        ctx.restore();
    }
"""