# -*- coding: utf-8 -*-

JS_SPRAY = """
    // Usamos uma função auto-executável (IIFE) para evitar erro de "variável já declarada"
    (function() {
        var btn = document.getElementById('sprayTool');
        if (btn) {
            // Removemos listeners antigos para não duplicar (segurança extra)
            var newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', function() { setTool('spray'); });
            newBtn.addEventListener('dblclick', function(e) { 
                e.preventDefault(); 
                e.stopPropagation(); 
                setTool('none'); 
            });
        }
    })();

    // Função de desenho (pode ficar global)
    function drawSpray(ctx, obj) {
        ctx.fillStyle = obj.color;
        var dotSize = 1; 
        
        if (obj.points) {
            for (var i = 0; i < obj.points.length; i++) {
                var p = obj.points[i];
                ctx.fillRect(p.x, p.y, dotSize, dotSize);
            }
        }
    }
"""