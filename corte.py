# -*- coding: utf-8 -*-

JS_CORTE = """
    // ============================================================
    // FERRAMENTA TESOURA (CORTE LIVRE / BISTURI) - VERSÃO FINAL
    // ============================================================

    scissorsBtn.addEventListener('click', () => setTool('scissors'));

    let cutPathPoints = [];
    let isCutting = false;

    // Algoritmo de Flood Fill para identificar ilhas de pixels
    function separateConnectedComponents(sourceCtx, width, height) {
        const imgData = sourceCtx.getImageData(0, 0, width, height);
        const data = imgData.data;
        const visited = new Uint8Array(width * height); 
        const components = [];

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                const pos = y * width + x;
                const idx = pos * 4;

                // Se o pixel tem opacidade (existe) e não foi visitado
                if (data[idx + 3] > 20 && visited[pos] === 0) {
                    
                    const stack = [pos];
                    visited[pos] = 1;
                    
                    let minX = x, maxX = x, minY = y, maxY = y;
                    const pixels = []; 

                    while (stack.length > 0) {
                        const currPos = stack.pop();
                        const cy = Math.floor(currPos / width);
                        const cx = currPos % width;
                        const cIdx = currPos * 4;
                        
                        pixels.push({
                            x: cx, y: cy,
                            r: data[cIdx], g: data[cIdx+1], b: data[cIdx+2], a: data[cIdx+3]
                        });

                        if (cx < minX) minX = cx;
                        if (cx > maxX) maxX = cx;
                        if (cy < minY) minY = cy;
                        if (cy > maxY) maxY = cy;

                        // Verifica vizinhos (Cima, Baixo, Esquerda, Direita)
                        const neighbors = [
                            currPos - width, // Cima
                            currPos + width, // Baixo
                            (cx > 0) ? currPos - 1 : -1, // Esquerda
                            (cx < width - 1) ? currPos + 1 : -1 // Direita
                        ];
                        
                        for (let nPos of neighbors) {
                            if (nPos >= 0 && nPos < visited.length) {
                                if (visited[nPos] === 0 && data[nPos * 4 + 3] > 20) {
                                    visited[nPos] = 1;
                                    stack.push(nPos);
                                }
                            }
                        }
                    }

                    // Ignora sujeira (menos de 10 pixels)
                    if (pixels.length > 10) {
                        components.push({ pixels, bounds: { minX, maxX, minY, maxY } });
                    }
                }
            }
        }
        return components;
    }

    function performFreehandCut(targetObj, points) {
        const bounds = getObjectBounds(targetObj);
        // Margem generosa para evitar cortes nas bordas do bounding box
        const padding = 50; 
        const width = Math.ceil(bounds.w + padding * 2);
        const height = Math.ceil(bounds.h + padding * 2);
        
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = width;
        tempCanvas.height = height;
        const ctxTemp = tempCanvas.getContext('2d');

        // 1. Desenha o objeto original centralizado no canvas temporário
        ctxTemp.save();
        // Move a origem para (padding, padding)
        ctxTemp.translate(padding, padding);
        // Move o objeto para que seu topo/esquerda fique na origem
        ctxTemp.translate(-bounds.x, -bounds.y);
        drawObject(ctxTemp, targetObj);
        ctxTemp.restore();

        // 2. Aplica o corte (Borracha) seguindo os pontos
        ctxTemp.save();
        ctxTemp.globalCompositeOperation = 'destination-out';
        ctxTemp.lineWidth = 5; // Espessura do corte (ajustável)
        ctxTemp.lineCap = 'round';
        ctxTemp.lineJoin = 'round';
        ctxTemp.beginPath();
        
        if (points.length > 0) {
            // Converte coordenadas globais do mouse para locais do canvas temporário
            // Fórmula: PontoGlobal - OrigemObjeto + Padding
            const startX = points[0].x - bounds.x + padding;
            const startY = points[0].y - bounds.y + padding;
            ctxTemp.moveTo(startX, startY);
            
            for (let i = 1; i < points.length; i++) {
                const px = points[i].x - bounds.x + padding;
                const py = points[i].y - bounds.y + padding;
                ctxTemp.lineTo(px, py);
            }
        }
        ctxTemp.stroke();
        ctxTemp.restore();

        // 3. Processa as partes resultantes
        const parts = separateConnectedComponents(ctxTemp, width, height);

        // Se algo deu errado ou apagou tudo, remove o objeto
        if (parts.length === 0) {
            saveState();
            drawingHistory = drawingHistory.filter(o => o.id !== targetObj.id);
            redrawHistory();
            return true;
        }

        // Aplica as mudanças (mesmo que seja apenas 1 parte modificada/furada)
        saveState();
        
        // Remove o objeto original
        drawingHistory = drawingHistory.filter(o => o.id !== targetObj.id);
        
        const newObjects = [];

        parts.forEach(part => {
            const pW = part.bounds.maxX - part.bounds.minX + 1;
            const pH = part.bounds.maxY - part.bounds.minY + 1;
            
            const partCanvas = document.createElement('canvas');
            partCanvas.width = pW;
            partCanvas.height = pH;
            const pCtx = partCanvas.getContext('2d');
            const pImgData = pCtx.createImageData(pW, pH);
            
            for (let p of part.pixels) {
                const localX = p.x - part.bounds.minX;
                const localY = p.y - part.bounds.minY;
                const idx = (localY * pW + localX) * 4;
                pImgData.data[idx] = p.r;
                pImgData.data[idx+1] = p.g;
                pImgData.data[idx+2] = p.b;
                pImgData.data[idx+3] = p.a;
            }
            pCtx.putImageData(pImgData, 0, 0);
            
            const dataURL = partCanvas.toDataURL();
            const img = new Image();
            img.src = dataURL;

            // Calcula a posição global exata para colocar a nova imagem
            const globalX = bounds.x - padding + part.bounds.minX;
            const globalY = bounds.y - padding + part.bounds.minY;

            const newObj = {
                id: crypto.randomUUID(),
                type: 'external_image',
                x: globalX,
                y: globalY,
                width: pW,
                height: pH,
                src: dataURL,
                imgElement: img,
                rotation: 0,
                opacity: targetObj.opacity || 1.0,
                group: crypto.randomUUID()
            };
            
            newObjects.push(newObj);
            drawingHistory.push(newObj);
        });

        // Seleciona os novos objetos automaticamente
        selectedGroup = newObjects;
        if (newObjects.length > 0) selectedObject = newObjects[0];
        
        // Garante que as imagens carreguem antes de desenhar
        let loadedCount = 0;
        if (newObjects.length > 0) {
            newObjects.forEach(obj => {
                obj.imgElement.onload = () => {
                    loadedCount++;
                    if (loadedCount === newObjects.length) redrawHistory();
                };
                // Fallback caso o onload falhe ou seja instantâneo (cache)
                if (obj.imgElement.complete) obj.imgElement.onload();
            });
        } else {
            redrawHistory();
        }

        return true;
    }

    // ============================================================
    // EVENTOS DO MOUSE (TESOURA)
    // ============================================================

    canvas.addEventListener('mousedown', (e) => {
        if (currentTool !== 'scissors') return;
        isCutting = true;
        cutPathPoints = [{x: e.offsetX, y: e.offsetY}];
    });

    canvas.addEventListener('mousemove', (e) => {
        if (currentTool !== 'scissors' || !isCutting) return;
        
        const pt = {x: e.offsetX, y: e.offsetY};
        cutPathPoints.push(pt);
        
        redrawHistory();
        
        // Desenha o rastro da tesoura
        ctx.save();
        ctx.strokeStyle = '#ff0000';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        if (cutPathPoints.length > 0) {
            ctx.moveTo(cutPathPoints[0].x, cutPathPoints[0].y);
            for (let i = 1; i < cutPathPoints.length; i++) {
                ctx.lineTo(cutPathPoints[i].x, cutPathPoints[i].y);
            }
        }
        ctx.stroke();
        ctx.restore();
    });

    // Usamos window.addEventListener para garantir que o evento dispare
    // mesmo se o usuário soltar o mouse fora do canvas
    window.addEventListener('mouseup', (e) => {
        if (currentTool !== 'scissors' || !isCutting) return;
        isCutting = false;
        
        if (cutPathPoints.length < 2) {
            cutPathPoints = [];
            return;
        }

        // 1. Encontra o objeto alvo (o que estiver mais "em cima" visualmente)
        let target = null;
        
        // Otimização: Bounding box do corte
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        cutPathPoints.forEach(p => {
            if(p.x < minX) minX = p.x; if(p.x > maxX) maxX = p.x;
            if(p.y < minY) minY = p.y; if(p.y > maxY) maxY = p.y;
        });
        const cutRect = { x: minX, y: minY, w: maxX - minX, h: maxY - minY };

        // Itera de trás para frente (objetos mais recentes primeiro)
        for (let i = drawingHistory.length - 1; i >= 0; i--) {
            const obj = drawingHistory[i];
            if (obj.type === 'eraser_path') continue;
            
            // Verifica intersecção básica
            if (isRectIntersect(cutRect, getObjectBounds(obj))) {
                target = obj;
                break; // Corta apenas o primeiro objeto encontrado
            }
        }

        if (target) {
            performFreehandCut(target, cutPathPoints);
        }
        
        // Sempre limpa o rastro e volta para seleção
        cutPathPoints = [];
        setTool('select');
        redrawHistory();
    });
"""