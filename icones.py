# -*- coding: utf-8 -*-
import os
import base64
import json
import shutil
import uuid
from aqt import mw
from aqt.qt import QFileDialog
from aqt.utils import tooltip, showInfo

# --- FUNÇÕES AUXILIARES ---

def get_icons_folder():
    # Garante o caminho absoluto da pasta do addon
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(addon_dir, "icones")
    
    # Cria a pasta se não existir
    if not os.path.exists(icons_dir):
        try:
            os.makedirs(icons_dir)
        except Exception as e:
            showInfo(f"Erro crítico ao criar pasta de ícones:\n{e}")
    return icons_dir

def get_addon_icons():
    icons_dir = get_icons_folder()
    icons = []
    valid_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
    
    if not os.path.exists(icons_dir):
        return []

    try:
        # Lista arquivos ordenados
        files = sorted(os.listdir(icons_dir))
        for filename in files:
            if filename.lower().endswith(valid_extensions):
                try:
                    full_path = os.path.join(icons_dir, filename)
                    
                    with open(full_path, "rb") as image_file:
                        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        ext = filename.lower().split('.')[-1]
                        mime = "jpeg" if ext == "jpg" else ext
                        
                        icons.append({
                            "name": filename,
                            "src": f"data:image/{mime};base64,{encoded_string}"
                        })
                except Exception as e:
                    print(f"Erro ao ler imagem {filename}: {e}")
                    continue
    except Exception as e:
        print(f"Erro ao listar diretório: {e}")
        
    return icons

def add_icon_dialog():
    try:
        # Usa o diretório home do usuário como padrão, é mais seguro que Desktop
        start_dir = os.path.expanduser("~")
        
        # Abre o seletor de arquivos
        file_path, _ = QFileDialog.getOpenFileName(
            mw, 
            "Escolher Imagem", 
            start_dir, 
            "Imagens (*.png *.jpg *.jpeg *.gif *.bmp *.webp)"
        )
        
        if file_path:
            filename = os.path.basename(file_path)
            dest_dir = get_icons_folder()
            dest_path = os.path.join(dest_dir, filename)
            
            # Se já existe arquivo com mesmo nome, cria um nome único
            if os.path.exists(dest_path):
                name, ext = os.path.splitext(filename)
                # Adiciona 4 caracteres aleatórios
                filename = f"{name}_{uuid.uuid4().hex[:4]}{ext}"
                dest_path = os.path.join(dest_dir, filename)
            
            shutil.copy2(file_path, dest_path)
            tooltip("Ícone adicionado!")
            return True
            
    except Exception as e:
        showInfo(f"Erro ao adicionar imagem:\n{str(e)}")
        
    return False

def delete_icon(filename):
    icons_dir = get_icons_folder()
    target_path = os.path.join(icons_dir, filename)
    
    try:
        if os.path.exists(target_path):
            os.remove(target_path)
            tooltip("Ícone excluído!")
            return True
        else:
            # Tenta encontrar o arquivo caso haja diferença de encoding
            for f in os.listdir(icons_dir):
                if f.lower() == filename.lower(): # Tentativa case-insensitive
                    os.remove(os.path.join(icons_dir, f))
                    tooltip("Ícone excluído (match aproximado)!")
                    return True
            
            showInfo(f"Erro: Arquivo não encontrado.\nProcurado: {filename}\nNa pasta: {icons_dir}")
            return False
            
    except Exception as e:
        showInfo(f"Erro ao excluir arquivo:\n{str(e)}")
        return False

def handle_icons_request(message):
    # Esta função é a ponte entre JS e Python
    # Ela SEMPRE deve retornar a lista atualizada de ícones,
    # mesmo que ocorra um erro no meio do caminho.
    
    try:
        if message == "requestIcons":
            pass # Apenas retorna a lista no final
            
        elif message == "addIcon":
            add_icon_dialog()
            
        elif message.startswith("deleteIcon:"):
            filename = message.split(":", 1)[1]
            delete_icon(filename)
            
    except Exception as e:
        showInfo(f"Erro interno no addon:\n{e}")

    # Retorna a lista atualizada para redesenhar a tela
    return json.dumps(get_addon_icons())


# --- JAVASCRIPT ---

JS_ICONES = """
    // ============================================================
    // BIBLIOTECA DE ÍCONES (CORRIGIDA V2)
    // ============================================================

    if (!document.getElementById('icons-modal')) {
        const iconsStyle = document.createElement('style');
        iconsStyle.innerHTML = `
            #icons-modal {
                display: none;
                position: fixed;
                top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                width: 360px;
                background: #f5f5f5;
                border-radius: 8px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.5);
                z-index: 9999; /* Z-index alto para garantir que fique por cima */
                flex-direction: column;
                padding: 15px;
                border: 1px solid #ccc;
                font-family: sans-serif;
            }
            .nightMode #icons-modal {
                background: #2f3136;
                border-color: #202225;
                color: #dcddde;
            }
            
            #icons-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 8px;
            }
            
            #icons-actions {
                display: flex;
                gap: 10px;
                align-items: center;
            }

            .icon-btn-action {
                background: #00aaff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                cursor: pointer;
                font-size: 12px;
                font-weight: bold;
            }
            .icon-btn-action:hover { background: #0088cc; }
            
            #icons-search {
                width: 100%;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #ccc;
                margin-bottom: 10px;
                box-sizing: border-box;
            }
            
            #icons-grid {
                display: grid;
                grid-template-columns: repeat(7, 1fr);
                gap: 5px;
                max-height: 300px;
                overflow-y: auto;
                padding: 4px;
                background: rgba(0,0,0,0.05);
                border-radius: 4px;
                min-height: 120px;
            }
            
            .icon-item {
                position: relative;
                width: 40px;
                height: 40px;
                border: 1px solid #ddd;
                border-radius: 4px;
                cursor: pointer;
                background-color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                transition: transform 0.1s;
            }
            .icon-item:hover {
                transform: scale(1.1);
                border-color: #00aaff;
                z-index: 10;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            }
            .icon-item img {
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
                pointer-events: none;
            }
            
            .icon-delete-btn {
                display: none;
                position: absolute;
                top: 0;
                right: 0;
                width: 16px;
                height: 16px;
                background: red;
                color: white;
                font-size: 12px;
                line-height: 16px;
                text-align: center;
                border-bottom-left-radius: 4px;
                z-index: 20;
                font-weight: bold;
            }
            .icon-item:hover .icon-delete-btn {
                display: block;
            }
            .icon-delete-btn:hover {
                background: darkred;
            }
            
            #icons-close {
                cursor: pointer;
                font-weight: bold;
                color: #888;
                font-size: 18px;
                margin-left: 10px;
                padding: 0 5px;
            }
            #icons-close:hover { color: red; }
        `;
        document.head.appendChild(iconsStyle);

        const iconsModal = document.createElement('div');
        iconsModal.id = 'icons-modal';
        iconsModal.innerHTML = `
            <div id="icons-header">
                <span style="font-weight:bold; font-size: 14px;">Biblioteca de Ícones</span>
                <div id="icons-actions">
                    <button id="btn-add-icon" class="icon-btn-action" title="Importar imagem">+ Adicionar</button>
                    <span id="icons-close" title="Fechar">✕</span>
                </div>
            </div>
            <input type="text" id="icons-search" placeholder="Pesquisar ícone (ex: bra)...">
            <div id="icons-grid">
                <div style="grid-column: 1/-1; text-align: center; padding: 20px; color: #888;">Carregando...</div>
            </div>
            <div style="font-size: 10px; color: #888; margin-top: 5px; text-align: center;">
                Passe o mouse sobre um ícone para ver a opção de excluir.
            </div>
        `;
        document.body.appendChild(iconsModal);

        // Eventos
        document.getElementById('icons-close').addEventListener('click', () => {
            iconsModal.style.display = 'none';
        });
        
        const searchInput = document.getElementById('icons-search');
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const items = document.querySelectorAll('.icon-item');
            items.forEach(item => {
                const name = item.dataset.name.toLowerCase();
                if (name.includes(term)) {
                    item.style.display = 'flex';
                } else {
                    item.style.display = 'none';
                }
            });
        });
        
        document.getElementById('btn-add-icon').addEventListener('click', () => {
            // Chama Python para adicionar e espera a lista atualizada
            pycmd('addIcon', (response) => {
                try {
                    const icons = JSON.parse(response);
                    renderIcons(icons);
                } catch(e) {
                    console.error("Erro ao processar resposta do addIcon:", e);
                }
            });
        });
        
        // Previne cliques de passar para o canvas
        iconsModal.addEventListener('mousedown', (e) => e.stopPropagation());
        iconsModal.addEventListener('mouseup', (e) => e.stopPropagation());
        searchInput.addEventListener('keydown', (e) => e.stopPropagation());
    }

    const iconsBtn = document.getElementById('iconsTool');
    const iconsModal = document.getElementById('icons-modal');
    const iconsGrid = document.getElementById('icons-grid');

    function renderIcons(icons) {
        iconsGrid.innerHTML = ''; 
        
        if (!icons || icons.length === 0) {
            iconsGrid.innerHTML = '<div style="grid-column: 1/-1; padding: 20px; font-size: 13px; text-align: center; color: #666;">A pasta está vazia.<br><br>Clique em <b>+ Adicionar</b> para importar imagens.</div>';
            return;
        }

        icons.forEach(icon => {
            const div = document.createElement('div');
            div.className = 'icon-item';
            div.title = icon.name;
            div.dataset.name = icon.name;
            
            const img = document.createElement('img');
            img.src = icon.src;
            div.appendChild(img);
            
            const delBtn = document.createElement('div');
            delBtn.className = 'icon-delete-btn';
            delBtn.textContent = '×';
            delBtn.title = 'Excluir este ícone';
            
            delBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm(`Excluir o ícone "${icon.name}" permanentemente?`)) {
                    // Envia comando de delete e espera a lista atualizada
                    pycmd(`deleteIcon:${icon.name}`, (response) => {
                        try {
                            const updatedIcons = JSON.parse(response);
                            renderIcons(updatedIcons);
                        } catch(e) {
                            console.error("Erro ao processar resposta do deleteIcon:", e);
                        }
                    });
                }
            });
            div.appendChild(delBtn);
            
            div.addEventListener('click', () => {
                addIconToCanvas(icon.src);
                iconsModal.style.display = 'none';
            });
            
            iconsGrid.appendChild(div);
        });
        
        // Reaplica filtro se houver
        const searchTerm = document.getElementById('icons-search').value;
        if (searchTerm) {
            document.getElementById('icons-search').dispatchEvent(new Event('input'));
        }
    }

    if (iconsBtn) {
        iconsBtn.addEventListener('click', () => {
            if (iconsModal.style.display === 'flex') {
                iconsModal.style.display = 'none';
                return;
            }
            
            iconsModal.style.display = 'flex';
            document.getElementById('icons-search').focus();

            pycmd('requestIcons', (response) => {
                try {
                    renderIcons(JSON.parse(response));
                } catch(e) {
                    console.error("Erro ao carregar ícones:", e);
                }
            });
        });
    }

    function addIconToCanvas(base64Src) {
        const img = new Image();
        img.onload = () => {
            let w = img.width;
            let h = img.height;
            const maxSize = 100; 
            
            if (w > maxSize || h > maxSize) {
                const ratio = w / h;
                if (w > h) { w = maxSize; h = maxSize / ratio; } 
                else { h = maxSize; w = maxSize * ratio; }
            }

            const startX = (window.innerWidth / 2) - (w / 2);
            const startY = (window.innerHeight / 2) - (h / 2);

            saveState();
            
            const iconObj = {
                id: crypto.randomUUID(),
                type: 'external_image',
                x: startX,
                y: startY,
                width: w,
                height: h,
                src: base64Src,
                imgElement: img,
                rotation: 0,
                opacity: 1.0,
                group: crypto.randomUUID()
            };

            drawingHistory.push(iconObj);
            setTool('select');
            selectedGroup = [iconObj];
            selectedObject = iconObj;
            redrawHistory();
        };
        img.src = base64Src;
    }
"""