# -*- coding: utf-8 -*-

JS_IMAGENS = """
    // ============================================================
    // LÓGICA DE COLAR IMAGENS (CLIPBOARD)
    // ============================================================

    window.addEventListener('paste', (e) => {
        // Se o usuário estiver editando texto dentro de uma caixa de texto do addon,
        // deixamos o comportamento padrão (colar texto) acontecer, a menos que seja imagem.
        if (e.target === textInputBox && !e.clipboardData.types.includes('Files')) return;

        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        let blob = null;

        // Procura por um item de imagem no clipboard
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') === 0) {
                blob = items[i].getAsFile();
                break;
            }
        }

        if (blob) {
            e.preventDefault(); // Impede que a imagem seja colada no campo de texto do Anki duplicada
            
            const reader = new FileReader();
            reader.onload = (event) => {
                const img = new Image();
                img.onload = () => {
                    // Define um tamanho máximo inicial para não ocupar a tela toda
                    let w = img.width;
                    let h = img.height;
                    const maxSize = 500;
                    
                    if (w > maxSize || h > maxSize) {
                        const ratio = w / h;
                        if (w > h) {
                            w = maxSize;
                            h = maxSize / ratio;
                        } else {
                            h = maxSize;
                            w = maxSize * ratio;
                        }
                    }

                    // Centraliza na tela
                    const startX = (window.innerWidth / 2) - (w / 2);
                    const startY = (window.innerHeight / 2) - (h / 2);

                    saveState();
                    
                    const imageObj = {
                        id: crypto.randomUUID(),
                        type: 'external_image',
                        x: startX,
                        y: startY,
                        width: w,
                        height: h,
                        src: event.target.result, // Base64 da imagem
                        imgElement: img, // Cache do elemento DOM
                        rotation: 0,
                        opacity: 1.0,
                        group: crypto.randomUUID()
                    };

                    drawingHistory.push(imageObj);
                    
                    // Seleciona a imagem automaticamente para facilitar mover/redimensionar
                    setTool('select');
                    selectedGroup = [imageObj];
                    selectedObject = imageObj;
                    
                    redrawHistory();
                };
                img.src = event.target.result;
            };
            reader.readAsDataURL(blob);
        }
    });
"""