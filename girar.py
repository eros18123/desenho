# -*- coding: utf-8 -*-

JS_GIRAR = """
    // ============================================================
    // LÓGICA DE ROTAÇÃO
    // ============================================================

    function calculateRotationAngle(cx, cy, mx, my) {
        // Calcula o ângulo em radianos entre o centro do objeto e o mouse
        // Adicionamos Math.PI / 2 porque o "topo" é -90 graus (ou 270), 
        // mas queremos que o ponteiro do mouse alinhe com a alça superior.
        return Math.atan2(my - cy, mx - cx) + Math.PI / 2;
    }

    function rotateContext(ctx, x, y, rotation) {
        if (!rotation) return;
        ctx.translate(x, y);
        ctx.rotate(rotation);
        ctx.translate(-x, -y);
    }
    
    // Helper para rotacionar um ponto (para detecção de clique)
    function getRotatedPoint(x, y, cx, cy, angle) {
        if (!angle) return { x, y };
        const s = Math.sin(-angle);
        const c = Math.cos(-angle);
        const dx = x - cx;
        const dy = y - cy;
        return {
            x: dx * c - dy * s + cx,
            y: dx * s + dy * c + cy
        };
    }
"""