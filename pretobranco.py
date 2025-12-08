# -*- coding: utf-8 -*-

JS_PRETOBRANCO = """
    const btnBw = document.getElementById('tool-bw');

    if (btnBw) {
        btnBw.addEventListener('click', () => {
            // Só funciona se houver objetos selecionados
            if (selectedGroup.length > 0) {
                saveState(); // Permite desfazer a ação
                
                // Decide se vai aplicar ou remover o filtro baseado no estado do primeiro objeto
                const makeGray = !selectedGroup[0].isGrayscale;
                
                // Aplica o mesmo estado (ligado/desligado) para todos os objetos no grupo
                selectedGroup.forEach(obj => {
                    obj.isGrayscale = makeGray;
                });
                
                // Atualiza o estado visual do botão
                btnBw.classList.toggle('tool-active', makeGray);
                
                redrawHistory(); // Redesenha o canvas para mostrar o efeito
            }
        });
    }

    // Garante que o botão reflita o estado do objeto selecionado
    const originalUpdateToolUI_BW = window.updateToolUI || function(){};
    window.updateToolUI = function() {
        if (typeof originalUpdateToolUI_BW === 'function') originalUpdateToolUI_BW();
        
        if (btnBw) {
            if (selectedObject) {
                // Se o objeto selecionado tem a propriedade isGrayscale, ativa o botão
                btnBw.classList.toggle('tool-active', !!selectedObject.isGrayscale);
            } else {
                // Se nada estiver selecionado, o botão fica inativo
                btnBw.classList.remove('tool-active');
            }
        }
    };
"""