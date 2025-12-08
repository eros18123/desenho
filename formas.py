# -*- coding: utf-8 -*-

JS_FORMAS = """
    shapesBtn.addEventListener('click', () => setTool('shapes'));

    shapeBtns.forEach(btn => btn.addEventListener('click', () => { 
        currentShape = btn.dataset.shape; 
        document.querySelector('#shapeOptions .shape-active').classList.remove('shape-active'); 
        btn.classList.add('shape-active'); 
        window.persistentDrawingState.shape = currentShape; 
        window.saveToolStateToPython();
    }));

    fillToggleBtn.addEventListener('click', () => { 
        isShapeFilled = !isShapeFilled; 
        fillToggleBtn.classList.toggle('tool-active', isShapeFilled); 
        window.persistentDrawingState.filled = isShapeFilled; 
        window.saveToolStateToPython();
    });

    function drawShape(ctx, shape, x1, y1, x2, y2, color, size, isFilled) { 
        ctx.beginPath(); 
        switch (shape) { 
            case 'line': ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); break; 
            case 'arrow': const headlen = Math.max(10, size * 3), angle = Math.atan2(y2 - y1, x2 - x1); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.moveTo(x2, y2); ctx.lineTo(x2 - headlen * Math.cos(angle - Math.PI / 6), y2 - headlen * Math.sin(angle - Math.PI / 6)); ctx.moveTo(x2, y2); ctx.lineTo(x2 - headlen * Math.cos(angle + Math.PI / 6), y2 - headlen * Math.sin(angle + Math.PI / 6)); ctx.stroke(); break; 
            case 'square': ctx.rect(x1, y1, x2 - x1, y2 - y1); break; 
            case 'circle': const r = Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2)); ctx.arc(x1, y1, r, 0, 2 * Math.PI); break; 
            case 'triangle': ctx.moveTo((x1 + x2) / 2, y1); ctx.lineTo(x1, y2); ctx.lineTo(x2, y2); ctx.closePath(); break; 
            case 'rhombus': ctx.moveTo((x1 + x2) / 2, y1); ctx.lineTo(x2, (y1 + y2) / 2); ctx.lineTo((x1 + x2) / 2, y2); ctx.lineTo(x1, (y1 + y2) / 2); ctx.closePath(); break;
            case 'star': let rot = Math.PI / 2 * 3, x = (x1 + x2) / 2, y = (y1 + y2) / 2, step = Math.PI / 5, outerR = Math.abs(x2 - x1) / 2, innerR = outerR/2; ctx.moveTo(x, y - outerR); for (let i = 0; i < 5; i++) { x = (x1 + x2) / 2 + Math.cos(rot) * outerR; y = (y1 + y2) / 2 + Math.sin(rot) * outerR; ctx.lineTo(x, y); rot += step; x = (x1 + x2) / 2 + Math.cos(rot) * innerR; y = (y1 + y2) / 2 + Math.sin(rot) * innerR; ctx.lineTo(x, y); rot += step; } ctx.lineTo((x1 + x2) / 2, (y1 + y2) / 2 - outerR); ctx.closePath(); break;
            case 'heart': const topCurveHeight = (y2 - y1) * 0.3, w = x2 - x1, h = y2 - y1; ctx.moveTo(x1 + w / 2, y1 + topCurveHeight); ctx.bezierCurveTo(x1, y1, x1, y1 + h * 0.7, x1 + w / 2, y1 + h); ctx.bezierCurveTo(x1 + w, y1 + h * 0.7, x1 + w, y1, x1 + w / 2, y1 + topCurveHeight); ctx.closePath(); break;
        } 
        if (isFilled && shape !== 'line' && shape !== 'arrow') { ctx.fill(); } else { ctx.stroke(); } 
    }
"""