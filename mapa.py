# -*- coding: utf-8 -*-

JS_MAPA = """
    // ============================================================
    // LÓGICA DE MAPA MENTAL (CONEXÕES)
    // ============================================================

    // Função para desenhar a linha de conexão temporária enquanto arrasta
    function drawConnectionLine(ctx, startX, startY, endX, endY) {
        ctx.save();
        ctx.strokeStyle = '#9400D3'; // Cor roxa para combinar com o botão
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 3]);
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.stroke();
        ctx.restore();
    }

    // Função chamada ao soltar o mouse para criar o link
    function createMindMapLink(sourceObj, endX, endY) {
        const sourceBounds = getObjectBounds(sourceObj);
        const startX = sourceBounds.x + sourceBounds.w / 2;
        const startY = sourceBounds.y + sourceBounds.h / 2;

        // Verifica se o mouse foi solto sobre outro objeto
        let targetObj = getObjectAt(endX, endY);

        saveState(); // Salva o estado para permitir o 'desfazer'

        // CASO 1: Soltou em um espaço vazio -> Cria um novo círculo
        if (!targetObj || targetObj.id === sourceObj.id) {
            const newCircle = {
                id: crypto.randomUUID(),
                type: 'shape',
                shape: 'circle',
                x1: endX, y1: endY,
                x2: endX + 30, y2: endY, // Raio padrão de 30px
                color: currentPencilColor,
                size: currentShapeSize,
                isFilled: isShapeFilled,
                opacity: currentOpacity,
                group: crypto.randomUUID()
            };
            drawingHistory.push(newCircle);
            targetObj = newCircle; // O novo círculo se torna o alvo da conexão
        }

        // CASO 2: Soltou sobre um objeto existente (ou acabou de criar um)
        // Cria a linha de conexão entre o centro dos dois objetos
        const targetBounds = getObjectBounds(targetObj);
        const finalEndX = targetBounds.x + targetBounds.w / 2;
        const finalEndY = targetBounds.y + targetBounds.h / 2;

        const connectorLine = {
            id: crypto.randomUUID(),
            type: 'shape',
            shape: 'line', // Você pode mudar para 'arrow' se preferir setas
            x1: startX, y1: startY,
            x2: finalEndX, y2: finalEndY,
            color: '#333333', // Uma cor neutra para a linha de conexão
            size: 2,
            isFilled: false,
            opacity: 1.0,
            group: crypto.randomUUID() // A linha é um objeto independente
        };
        drawingHistory.push(connectorLine);

        // Desseleciona tudo e redesenha a tela
        selectedGroup = [];
        redrawHistory();
    }
"""