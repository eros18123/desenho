# -*- coding: utf-8 -*-
from .atalhos import load_general_config, save_general_config

def handle_opacity_save(message):
    try:
        # Formato esperado: saveOpacity:0.5
        val = float(message.split(":")[1])
        config = load_general_config()
        config["lastOpacity"] = val
        save_general_config(config)
    except: pass

JS_TRANSPARENTE = """
    const opacitySlider = document.getElementById('opacitySlider');
    const opacityValue = document.getElementById('opacityValue');

    if (opacitySlider) {
        opacitySlider.addEventListener('input', (e) => {
            const val = parseFloat(e.target.value);
            currentOpacity = val;
            window.persistentDrawingState.opacity = val;
            
            if (opacityValue) {
                opacityValue.textContent = Math.round(val * 100) + '%';
            }
            
            // Atualiza opacidade do texto se estiver editando
            if (textInputBox.style.display === 'block') {
                textInputBox.style.opacity = val;
            }
        });

        opacitySlider.addEventListener('change', (e) => {
            pycmd(`saveOpacity:${e.target.value}`);
        });
    }
"""