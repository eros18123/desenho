
# -*- coding: utf-8 -*-

JS_BALDE = """
    bucketBtn.addEventListener('click', () => setTool('bucket'));

    // Helper para converter cor CSS (ex: 'red', '#ff0000') para RGBA
    function cssColorToRGBA(color) {
        const tempDiv = document.createElement('div');
        tempDiv.style.color = color;
        document.body.appendChild(tempDiv);
        const computedColor = window.getComputedStyle(tempDiv).color;
        document.body.removeChild(tempDiv);
        
        // computedColor vem como "rgb(r, g, b)" ou "rgba(r, g, b, a)"
        const match = computedColor.match(/([\\d.]+)/g);
        if (!match) return [0, 0, 0, 255];
        
        return [
            parseInt(match[0]),
            parseInt(match[1]),
            parseInt(match[2]),
            match[3] ? Math.round(parseFloat(match[3]) * 255) : 255
        ];
    }

    function performFloodFill(startX, startY, fillColorStr, opacity) {
        const width = canvas.width;
        const height = canvas.height;
        
        const imgData = ctx.getImageData(0, 0, width, height);
        const data = imgData.data; 
        
        const fillColor = cssColorToRGBA(fillColorStr);
        fillColor[3] = Math.round(opacity * 255);

        const startPos = (startY * width + startX) * 4;
        const startR = data[startPos];
        const startG = data[startPos + 1];
        const startB = data[startPos + 2];
        const startA = data[startPos + 3];

        if (startR === fillColor[0] && startG === fillColor[1] && 
            startB === fillColor[2] && startA === fillColor[3]) {
            return;
        }

        const fillCanvas = document.createElement('canvas');
        fillCanvas.width = width;
        fillCanvas.height = height;
        const fillCtx = fillCanvas.getContext('2d');
        const fillImgData = fillCtx.createImageData(width, height);
        const fillData = fillImgData.data;

        const stack = [[startX, startY]];
        const tolerance = 30; 

        // Variáveis para calcular a Bounding Box (caixa delimitadora) da tinta
        let minX = width, maxX = 0, minY = height, maxY = 0;

        function matchColor(pos) {
            const r = data[pos];
            const g = data[pos + 1];
            const b = data[pos + 2];
            const a = data[pos + 3];
            
            return (
                Math.abs(r - startR) <= tolerance &&
                Math.abs(g - startG) <= tolerance &&
                Math.abs(b - startB) <= tolerance &&
                Math.abs(a - startA) <= tolerance
            );
        }

        while (stack.length) {
            const [x, y] = stack.pop();
            const pos = (y * width + x) * 4;

            if (fillData[pos + 3] > 0) continue; 

            // Atualiza limites da bounding box
            if (x < minX) minX = x;
            if (x > maxX) maxX = x;
            if (y < minY) minY = y;
            if (y > maxY) maxY = y;

            fillData[pos] = fillColor[0];
            fillData[pos + 1] = fillColor[1];
            fillData[pos + 2] = fillColor[2];
            fillData[pos + 3] = fillColor[3];

            const neighbors = [
                [x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]
            ];

            for (let i = 0; i < neighbors.length; i++) {
                const nx = neighbors[i][0];
                const ny = neighbors[i][1];

                if (nx >= 0 && nx < width && ny >= 0 && ny < height) {
                    const nPos = (ny * width + nx) * 4;
                    if (fillData[nPos + 3] === 0 && matchColor(nPos)) {
                        stack.push([nx, ny]);
                    }
                }
            }
        }

        // Se nada foi pintado, sai
        if (minX > maxX) return;

        fillCtx.putImageData(fillImgData, 0, 0);

        const dataURL = fillCanvas.toDataURL();
        
        saveState();
        
        const imgObj = new Image();
        imgObj.src = dataURL;

        const historyItem = {
            id: crypto.randomUUID(),
            type: 'fill',
            data: dataURL,
            x: 0, y: 0,
            width: width,
            height: height,
            // Salva a área exata que foi pintada
            bounds: { x: minX, y: minY, w: maxX - minX + 1, h: maxY - minY + 1 },
            opacity: 1.0, 
            group: crypto.randomUUID(),
            imgElement: imgObj 
        };

        drawingHistory.push(historyItem);
        
        imgObj.onload = () => redrawHistory();
        redrawHistory();
    }

    canvas.addEventListener('mousedown', (e) => {
        if (currentTool !== 'bucket') return;
        e.stopImmediatePropagation();
        e.preventDefault();
        setTimeout(() => {
            performFloodFill(e.offsetX, e.offsetY, currentPencilColor, currentOpacity);
        }, 0);
    });
"""