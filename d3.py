# -*- coding: utf-8 -*-

JS_3D = """
    const btn3d = document.getElementById('tool-3d');

    if (btn3d) {
        btn3d.addEventListener('click', () => {
            // Verifica se tem algo selecionado
            if (selectedGroup.length > 0) {
                saveState();
                
                // Verifica o estado do primeiro objeto para alternar (ligar/desligar)
                const isActive = !selectedGroup[0].effect3D;
                
                selectedGroup.forEach(obj => {
                    obj.effect3D = isActive;
                });
                
                // Atualiza visual do botão
                if (isActive) {
                    btn3d.classList.add('tool-active');
                } else {
                    btn3d.classList.remove('tool-active');
                }
                
                redrawHistory();
            } else {
                // Se nada estiver selecionado, alterna o modo global para os próximos desenhos
                window.persistentDrawingState.effect3D = !window.persistentDrawingState.effect3D;
                btn3d.classList.toggle('tool-active', window.persistentDrawingState.effect3D);
            }
        });
    }

    // Atualiza o botão quando selecionamos um objeto diferente
    const originalUpdateToolUI_3D = window.updateToolUI || function(){};
    window.updateToolUI = function() {
        if (typeof originalUpdateToolUI_3D === 'function') originalUpdateToolUI_3D();
        
        if (btn3d) {
            if (selectedObject) {
                if (selectedObject.effect3D) {
                    btn3d.classList.add('tool-active');
                } else {
                    btn3d.classList.remove('tool-active');
                }
            } else {
                // Se nada selecionado, mostra o estado global
                if (window.persistentDrawingState.effect3D) {
                    btn3d.classList.add('tool-active');
                } else {
                    btn3d.classList.remove('tool-active');
                }
            }
        }
    };
"""