# -*- coding: utf-8 -*-

JS_LAPIS2 = """
    // A variável pencil2Btn já foi definida no JS_HEADER do __init__.py
    if (pencil2Btn) {
        pencil2Btn.addEventListener('click', () => setTool('pencil2'));
        
        // Atalho de clique duplo para desmarcar
        pencil2Btn.addEventListener('dblclick', (e) => { 
            e.preventDefault(); 
            e.stopPropagation(); 
            setTool('none'); 
        });
    }
"""