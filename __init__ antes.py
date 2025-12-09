# -*- coding: utf-8 -*-

import json
import re
import base64
import uuid
import os

from aqt import mw, gui_hooks
from aqt.utils import tooltip
from anki.cards import Card
from aqt.editor import Editor
from aqt.browser.browser import Browser
from aqt.webview import AnkiWebView
from anki import hooks
from aqt.qt import QTimer, QGuiApplication, QBuffer, QIODevice, QAction

from .atalhos import add_config_menu_item, update_config_menu_text, load_zoom_config, save_zoom_config, load_shortcut_config, load_general_config, save_general_config, load_ui_state, save_ui_state, pt_translations
from .ingles import translations as en_translations
from .digitar import edit_field_filter, JS_DIGITAR
from .lapis import handle_state_save, JS_LAPIS
from .lapis2 import JS_LAPIS2
from .selecionar import JS_SELECIONAR
from .texto import JS_TEXTO
from .formas import JS_FORMAS
from .borracha import JS_BORRACHA
from .tabela import JS_TABELA
from .limpartudo import handle_clear_message, JS_LIMPARTUDO 
from .salvar import handle_save_message, JS_SALVAR
from .redimensionar import JS_REDIMENSIONAR
from .transparente import handle_opacity_save, JS_TRANSPARENTE
from .cores import JS_CORES
from .balde import JS_BALDE
from .girar import JS_GIRAR
from .imagens import JS_IMAGENS
from .corte import JS_CORTE
from .icones import JS_ICONES, handle_icons_request
from .spray import JS_SPRAY
from .d3 import JS_3D
from .pretobranco import JS_PRETOBRANCO
from .mapa import JS_MAPA

g_editable_context_active = False

def remove_only_drawing_html(content):
    if not content: return content
    if 'anki-drawing-image' not in content and 'data:image/png;base64' not in content: return content
    
    pattern1 = r'<img\s+class="anki-drawing-image"[^>]*>'
    content = re.sub(pattern1, '', content, flags=re.IGNORECASE | re.DOTALL)
    
    pattern2 = r'<img[^>]*src="data:image/png;base64[^>]*style="[^"]*position:\s*absolute[^"]*"[^>]*>'
    content = re.sub(pattern2, '', content, flags=re.IGNORECASE | re.DOTALL)
    
    pattern3 = r'<img[^>]*z-index:\s*99[^>]*>'
    content = re.sub(pattern3, '', content, flags=re.IGNORECASE | re.DOTALL)
    
    return content

JS_HEADER = """
window.parseShortcut = (shortcutStr) => {
    if (!shortcutStr) return null;
    const parts = shortcutStr.toLowerCase().split('+').map(s => s.trim());
    return {
        ctrl: parts.includes('ctrl') || parts.includes('control'),
        alt: parts.includes('alt'),
        shift: parts.includes('shift'),
        key: parts[parts.length - 1]
    };
};

window.checkShortcut = (event, configKey) => {
    if (!window.userShortcuts || !window.userShortcuts[configKey]) return false;
    const cfg = window.parseShortcut(window.userShortcuts[configKey]);
    if (!cfg) return false;
    const eventKey = event.key.toLowerCase();
    if (event.ctrlKey !== cfg.ctrl) return false;
    if (event.altKey !== cfg.alt) return false;
    if (event.shiftKey !== cfg.shift) return false;
    return eventKey === cfg.key;
};

window.getToolTitle = (name, configKey) => {
    const shortcut = window.userShortcuts && window.userShortcuts[configKey] ? window.userShortcuts[configKey] : '';
    return shortcut ? `${name} (${shortcut})` : name;
};

if (!window.persistentDrawingState) {
    const cfg = window.generalConfig || {};
    window.persistentDrawingState = {
        tool: 'none', 
        color: cfg.lastColor || 'red', 
        pencilSize: cfg.pencilSize || 2, 
        eraserSize: cfg.eraserSize || 30, 
        shapeSize: cfg.shapeSize || 5, 
        textSize: cfg.textSize || 16,
        shape: cfg.lastShape || 'arrow', 
        filled: cfg.lastFilled || false, 
        effect3D: false,
        opacity: cfg.lastOpacity !== undefined ? cfg.lastOpacity : 1.0,
        zoomLevel: window.initialZoomLevel || 1.0
    };
}

if (!window.colorSizeMemory) {
    window.colorSizeMemory = { pencil: {}, shape: {}, text: {} };
    window.colorSizeMemory.pencil[window.persistentDrawingState.color] = window.persistentDrawingState.pencilSize;
    window.colorSizeMemory.shape[window.persistentDrawingState.color] = window.persistentDrawingState.shapeSize;
    window.colorSizeMemory.text[window.persistentDrawingState.color] = window.persistentDrawingState.textSize;
}

if (!window.lastDrawingContext) window.lastDrawingContext = { cardId: null, fieldName: null };

if (!window.drawingCanvasInitialized) {
    window.drawingCanvasInitialized = true;
    window.currentCardId = null; 
    let internalClipboard = null;

    const drawingStyle = document.createElement('style');
    drawingStyle.innerHTML = `
        #drawingCanvas { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: 2; pointer-events: none; }
        .anki-drawing-image { display: none !important; opacity: 0 !important; pointer-events: none; }
        
        #drawingTools { 
            position: fixed; top: 10px; right: 10px; z-index: 1000; 
            display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px;
            background-color: #f5f5f5; padding: 6px; border-radius: 5px; 
            box-shadow: 0 0 5px rgba(0,0,0,0.3); cursor: move; transform-origin: top right; 
            padding-bottom: 12px;
        }
        
        #languageSelector {
            position: fixed;
            display: flex;
            flex-direction: column;
            gap: 4px;
            z-index: 1000;
        }
        .lang-flag {
            width: 24px;
            height: 18px;
            cursor: pointer;
            border: 2px solid transparent;
            border-radius: 3px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }
        .lang-flag.active {
            border-color: red;
        }
        
        #resizeHandle {
            width: 15px; height: 15px;
            background: linear-gradient(135deg, transparent 50%, #999 50%);
            position: absolute; bottom: 2px; right: 2px;
            cursor: nwse-resize; border-radius: 0 0 5px 0;
            z-index: 1001;
        }
        #resizeHandle:hover { background: linear-gradient(135deg, transparent 50%, #00aaff 50%); }

        .tool-btn, .shape-btn { 
            width: 28px; height: 28px; cursor: pointer; 
            border: 1px solid #ccc; border-radius: 5px; 
            display: flex; align-items: center; justify-content: center; 
            background-color: #ffffff; padding: 4px; box-sizing: border-box; 
        }
        .tool-btn svg, .shape-btn svg { stroke: #333333; }
        .tool-btn.tool-active { border-color: #00aaff; background-color: #cceeff; }
        .shape-btn.shape-active { border-color: #ff6600; background-color: #fff0e0; }
        .shape-btn.shape-active svg { stroke: #ff6600; }
        #pencilOptions, #shapeSubOptions { display: none; grid-column: 1 / -1; flex-direction: row; gap: 8px; margin-top: 6px; padding-top: 6px; border-top: 1px solid #ccc; align-items: center; }
        
        #color-palette { display: flex; flex-direction: column; gap: 4px; }
        .color-swatch { width: 18px; height: 18px; border: 2px solid #fff; border-radius: 50%; cursor: pointer; box-shadow: 0 0 3px rgba(0,0,0,0.4); }
        .color-swatch.active-color { border-color: #007bff; transform: scale(1.2); box-shadow: 0 0 5px #007bff; }
        
        #customColorBtn {
            background: conic-gradient(red, yellow, lime, aqua, blue, magenta, red);
            border: 2px solid #ccc;
            display: flex; align-items: center; justify-content: center;
        }
        #customColorPicker {
            opacity: 0; width: 100%; height: 100%; cursor: pointer; padding: 0; margin: 0; border: none;
        }

        #brushSizeSlider { -webkit-appearance: slider-vertical; width: 18px; height: 90px; cursor: pointer; }
        
        #opacityContainer { display: flex; flex-direction: column; align-items: center; gap: 2px; }
        #opacitySlider { -webkit-appearance: slider-vertical; width: 18px; height: 90px; cursor: pointer; }
        
        #shapeOptions { display: none; grid-column: 1 / -1; grid-template-columns: 1fr 1fr 1fr; gap: 4px; margin-top: 6px; padding-top: 6px; border-top: 1px solid #ccc; }
        #text-input-box { display: none; position: absolute; z-index: 1002; background: transparent; border: none; outline: none; padding: 4px; font-family: sans-serif; font-size: 16px; resize: none; overflow: hidden; line-height: 1.2; }
        #table-text-toolbar { display: none; position: absolute; z-index: 1003; background-color: #f5f5f5; border: 1px solid #ccc; border-radius: 5px; padding: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); flex-direction: row; gap: 5px; align-items: center; }
        .mini-swatch { width: 16px; height: 16px; border-radius: 50%; border: 1px solid #999; cursor: pointer; }
        .mini-swatch:hover { transform: scale(1.2); }
        #eraser-cursor-preview { display: none; position: fixed; pointer-events: none; border-radius: 50%; border: 1px solid rgba(0, 0, 0, 0.8); background-color: rgba(255, 255, 255, 0.5); z-index: 10000; }
        .nightMode #drawingTools, .nightMode #table-text-toolbar { background-color: #2f3136; border: 1px solid #202225; }
        .nightMode .tool-btn, .nightMode .shape-btn { background-color: #36393f; border-color: #202225; }
        .nightMode .tool-btn svg, .nightMode .shape-btn svg { stroke: #dcddde; } 
        .nightMode .tool-btn.tool-active { background-color: #40444b; border-color: #7289da; }
        .nightMode .tool-btn:hover { background-color: #40444b; }
        .nightMode .shape-btn.shape-active { background-color: #4a2c00; border-color: #ff9900; }
        .nightMode .shape-btn.shape-active svg { stroke: #ff9900; }
    `;
    document.head.appendChild(drawingStyle);

    const canvas = document.createElement('canvas'); canvas.id = 'drawingCanvas'; document.body.appendChild(canvas);
    const helperCanvas = document.createElement('canvas'); const hCtx = helperCanvas.getContext('2d', { willReadFrequently: true });
    const eraserCursor = document.createElement('div'); eraserCursor.id = 'eraser-cursor-preview'; document.body.appendChild(eraserCursor);

    const toolsContainer = document.createElement('div');
    toolsContainer.id = 'drawingTools';
    toolsContainer.innerHTML = `
        <div id="selectTool" class="tool-btn"></div>
        <div id="pencilTool" class="tool-btn"></div>
        <div id="pencilTool2" class="tool-btn"></div>
        <div id="textTool" class="tool-btn"></div>
        <div id="bucketTool" class="tool-btn"></div>
        <div id="sprayTool" class="tool-btn"></div>
        <div id="scissorsTool" class="tool-btn"></div>
        <div id="shapesTool" class="tool-btn"></div>
        <div id="eraserTool" class="tool-btn"></div>
        <div id="tableTool" class="tool-btn"></div>
        <div id="iconsTool" class="tool-btn"></div>
        <div id="tool-3d" class="tool-btn"></div>
        <div id="tool-bw" class="tool-btn"></div>
        <div id="clearTool" class="tool-btn"></div>
        <div id="saveTool" class="tool-btn"></div>
        <div id="pencilOptions">
            <div id="color-palette">
                <div class="color-swatch" data-color="black" style="background-color: black;"></div>
                <div class="color-swatch" data-color="white" style="background-color: white;"></div>
                <div class="color-swatch active-color" data-color="red" style="background-color: red;"></div>
                <div class="color-swatch" data-color="yellow" style="background-color: yellow;"></div>
                <div class="color-swatch" data-color="blue" style="background-color: blue;"></div>
                <div class="color-swatch" data-color="green" style="background-color: green;"></div>
                <label id="customColorBtn" class="color-swatch">
                    <input type="color" id="customColorPicker">
                </label>
            </div>
            <div style="display: flex; flex-direction: column; align-items: center; gap: 4px;">
                <input type="range" id="brushSizeSlider" min="1" max="150" value="2">
                <span id="brushSizeValue" style="font-size: 11px; color: currentColor; background-color: rgba(0,0,0,0.1); padding: 1px 4px; border-radius: 3px; min-width: 20px; text-align: center;">2</span>
            </div>
            <div id="opacityContainer">
                <input type="range" id="opacitySlider" min="0.1" max="1.0" step="0.1" value="1.0">
                <span id="opacityValue" style="font-size: 11px; color: currentColor; background-color: rgba(0,0,0,0.1); padding: 1px 4px; border-radius: 3px; min-width: 20px; text-align: center;">100%</span>
            </div>
        </div>
        <div id="shapeSubOptions"><div id="fillToggle" class="tool-btn"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2" fill="currentColor"></rect></svg></div></div>
        <div id="shapeOptions">
            <div class="shape-btn shape-active" data-shape="arrow"><svg viewBox="0 0 24 24"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg></div>
            <div class="shape-btn" data-shape="line"><svg viewBox="0 0 24 24"><line x1="5" y1="19" x2="19" y2="5"></line></svg></div>
            <div class="shape-btn" data-shape="square"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg></div>
            <div class="shape-btn" data-shape="circle"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle></svg></div>
            <div class="shape-btn" data-shape="triangle"><svg viewBox="0 0 24 24"><path d="M12 2L2 22h20L12 2z"></path></svg></div>
            <div class="shape-btn" data-shape="rhombus"><svg viewBox="0 0 24 24"><path d="M12 2l10 10-10 10-10-10L12 2z"></path></svg></div>
            <div class="shape-btn" data-shape="star"><svg viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"></path></svg></div>
            <div class="shape-btn" data-shape="heart"><svg viewBox="0 0 24 24"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg></div>
        </div>
        <div id="resizeHandle" title="Arraste para redimensionar"></div>
    `;
    document.body.appendChild(toolsContainer);
    
    const icons = {
        selectTool: '<svg viewBox="0 0 24 24"><path d="M12 2L4 20h16L12 2z" transform="rotate(90 12 12) translate(0, 4) scale(0.8)"/><path d="M5 15l7-7 7 7"/></svg>',
        pencilTool: '<svg viewBox="0 0 24 24"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>',
        pencilTool2: '<svg viewBox="0 0 24 24"><path d="M12 19l7-7 3 3-7 7-3-3z" fill="currentColor"></path><path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z" fill="none" stroke="currentColor" stroke-width="2"></path><path d="M2 2l3.5 14.5L13 18l5-5" fill="none"></path></svg>',
        textTool: '<svg viewBox="0 0 24 24"><polyline points="4 7 4 4 20 4 20 7"></polyline><line x1="9" y1="20" x2="15" y2="20"></line><line x1="12" y1="4" x2="12" y2="20"></line></svg>',
        bucketTool: '<svg viewBox="0 0 24 24"><path d="M19 11L12 17L6 11" fill="none" stroke="currentColor" stroke-width="2"/><path d="M19 11L12 4L6 11" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 17V21" stroke="currentColor" stroke-width="2"/><path d="M12 17C12 17 16 17 16 20" stroke="currentColor" stroke-width="2"/></svg>',
        sprayTool: '<svg viewBox="0 0 24 24"><rect x="9" y="11" width="6" height="10" rx="1" /><path d="M12 11V8"/><path d="M10 8h4"/><circle cx="12" cy="6" r="1"/><circle cx="15" cy="5" r="0.5"/><circle cx="9" cy="5" r="0.5"/></svg>',
        scissorsTool: '<svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><line x1="20" y1="4" x2="8.12" y2="15.88"></line><line x1="14.47" y1="14.48" x2="20" y2="20"></line><line x1="8.12" y1="8.12" x2="12" y2="12"></line></svg>',
        shapesTool: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>',
        eraserTool: '<svg viewBox="0 0 24 24"><path d="M21.49 2.51a2.828 2.828 0 0 0-4 0L11 9l-2 2 4 4 6.5-6.5a2.828 2.828 0 0 0 0-4Z"></path><path d="m18 11-8-8"></path><path d="m2 22 5.5-1.5L21.5 6.5l-4-4L2 16.5l-1.5 5.5Z"></path></svg>',
        tableTool: '<svg viewBox="0 0 24 24"><path d="M3 3h18v18H3zM3 9h18M3 15h18M9 3v18M15 3v18"/></svg>',
        iconsTool: '<svg viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>',
        'tool-3d': '<svg viewBox="0 0 24 24"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"></path></svg>',
        'tool-bw': '<svg viewBox="0 0 24 24"><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"></path><path d="M12 3v18"></path></svg>',
        clearTool: '<svg viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>',
        saveTool: '<svg viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>'
    };
    const toolNameMap = {
        selectTool: "select", pencilTool: "pencil", pencilTool2: "pencil2", textTool: "text", bucketTool: "bucket",
        sprayTool: "spray", scissorsTool: "scissors", shapesTool: "shapes", eraserTool: "eraser", tableTool: "table",
        iconsTool: "icons", "tool-3d": "toggle3d", "tool-bw": "toggleBw", clearTool: "clear", saveTool: "save"
    };

    function updateUIText(t) {
        window.translations = t;
        for (const id in icons) {
            const el = document.getElementById(id);
            if (el) {
                el.innerHTML = icons[id];
                const key = toolNameMap[id];
                el.title = window.getToolTitle(t[key], key);
            }
        }
        document.getElementById('customColorBtn').title = t.more_colors;
        if (document.getElementById('fontSelectBtn')) {
            document.getElementById('fontSelectBtn').title = t.change_font;
        }
    }
    updateUIText(window.translations);
    
    toolsContainer.querySelectorAll('svg').forEach(svg => {
        if (!svg.parentElement.id.includes('fillToggle')) { svg.setAttribute('fill', 'none'); }
        svg.setAttribute('stroke-width', '2');
        svg.setAttribute('stroke-linecap', 'round');
        svg.setAttribute('stroke-linejoin', 'round');
    });
    
    if (window.initialToolPosition && window.initialToolPosition.top && window.initialToolPosition.left) {
        toolsContainer.style.top = window.initialToolPosition.top;
        toolsContainer.style.left = window.initialToolPosition.left;
        toolsContainer.style.right = 'auto';
    }
    
    const langSelector = document.createElement('div');
    langSelector.id = 'languageSelector';
    langSelector.innerHTML = `
        <img src="${window.flag_br}" class="lang-flag" data-lang="pt" title="Português">
        <img src="${window.flag_us}" class="lang-flag" data-lang="en" title="English">
    `;
    document.body.appendChild(langSelector);
    
    function positionLanguageSelector() {
        const toolsRect = toolsContainer.getBoundingClientRect();
        langSelector.style.top = toolsRect.top + 'px';
        langSelector.style.left = (toolsRect.left - langSelector.offsetWidth - 10) + 'px';
    }
    
    langSelector.querySelectorAll('.lang-flag').forEach(flag => {
        flag.addEventListener('click', () => {
            const lang = flag.dataset.lang;
            pycmd(`saveLanguage:${lang}`, (response) => {
                const newTranslations = JSON.parse(response);
                updateUIText(newTranslations);
                document.querySelectorAll('.lang-flag').forEach(f => f.classList.remove('active'));
                flag.classList.add('active');
            });
        });
    });
    
    const tableTextToolbar = document.createElement('div');
    tableTextToolbar.id = 'table-text-toolbar';
    tableTextToolbar.innerHTML = `
        <div class="mini-swatch" style="background-color: black;" data-color="black"></div>
        <div class="mini-swatch" style="background-color: red;" data-color="red"></div>
        <div class="mini-swatch" style="background-color: blue;" data-color="blue"></div>
        <div class="mini-swatch" style="background-color: green;" data-color="green"></div>
        <div class="mini-swatch" style="background-color: white;" data-color="white"></div>
        <div class="mini-swatch" style="background-color: yellow;" data-color="yellow"></div>
        <input type="range" id="tableTextSizeSlider" min="10" max="60" value="16" style="width: 60px;">
    `;
    document.body.appendChild(tableTextToolbar);
    
    const makeToolsDraggable = (elmnt) => {
        let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
        elmnt.onmousedown = dragMouseDown;
        function dragMouseDown(e) {
            if (e.target.closest('.tool-btn, .shape-btn, input, .color-swatch, #resizeHandle')) return;
            e.preventDefault();
            pos3 = e.clientX; pos4 = e.clientY;
            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
            elmnt.style.cursor = 'grabbing';
        }
        function elementDrag(e) {
            e.preventDefault();
            pos1 = pos3 - e.clientX; pos2 = pos4 - e.clientY;
            pos3 = e.clientX; pos4 = e.clientY;
            elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
            elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
            elmnt.style.right = 'auto';
            positionLanguageSelector();
        }
        function closeDragElement() {
            document.onmouseup = null; document.onmousemove = null;
            elmnt.style.cursor = 'move';
            pycmd(`saveToolPosition:${elmnt.style.top}:${elmnt.style.left}`);
        }
    };
    makeToolsDraggable(toolsContainer);

    const textInputBox = document.createElement('textarea'); textInputBox.id = 'text-input-box'; document.body.appendChild(textInputBox);
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    
    const selectBtn = document.getElementById('selectTool');
    const pencilBtn = document.getElementById('pencilTool');
    const pencil2Btn = document.getElementById('pencilTool2');
    const textBtn = document.getElementById('textTool');
    const shapesBtn = document.getElementById('shapesTool');
    const eraserBtn = document.getElementById('eraserTool');
    const tableBtn = document.getElementById('tableTool');
    const bucketBtn = document.getElementById('bucketTool');
    const scissorsBtn = document.getElementById('scissorsTool');
    const sprayBtn = document.getElementById('sprayTool');
    const saveBtn = document.getElementById('saveTool');
    const clearBtn = document.getElementById('clearTool');
    const pencilOptions = document.getElementById('pencilOptions');
    const shapeOptions = document.getElementById('shapeOptions');
    const shapeSubOptions = document.getElementById('shapeSubOptions');
    const fillToggleBtn = document.getElementById('fillToggle');
    const colorSwatches = document.querySelectorAll('.color-swatch');
    const brushSizeSlider = document.getElementById('brushSizeSlider');
    const shapeBtns = document.querySelectorAll('.shape-btn');
    const brushSizeValue = document.getElementById('brushSizeValue');
    const tableTextSizeSlider = document.getElementById('tableTextSizeSlider');
    const tableColorSwatches = tableTextToolbar.querySelectorAll('.mini-swatch');

    let drawingHistory = [];
    let undoStack = []; 
    let redoStack = []; 
    
    let isDrawing = false, currentTool = window.persistentDrawingState.tool, lastX = 0, lastY = 0;
    let previousTool = 'none'; 
    
    let currentPencilColor = window.persistentDrawingState.color;
    let currentPencilSize = window.persistentDrawingState.pencilSize;
    let currentEraserSize = window.persistentDrawingState.eraserSize;
    let currentShapeSize = window.persistentDrawingState.shapeSize;
    let currentTextSize = window.persistentDrawingState.textSize || 16;
    let currentShape = window.persistentDrawingState.shape, isShapeFilled = window.persistentDrawingState.filled;
    let currentOpacity = window.persistentDrawingState.opacity !== undefined ? window.persistentDrawingState.opacity : 1.0;
    let isShiftDown = false, textCommitData = {};
    let isDrawingUIHidden = false;
    let currentZoomLevel = window.persistentDrawingState.zoomLevel;
    
    let selectedGroup = []; 
    let selectedObject = null; 
    let interactionMode = 'NONE'; 
    let dragLastX = 0, dragLastY = 0;
    let selectionStart = { x: 0, y: 0 };
    let resizeSnapshot = [];
    let resizeStartBounds = null;
    let activeUIElements = []; 
    
    let currentPath = null;
    let isClearing = false; 
    let tableConfig = { rows: 3, cols: 3 };
    let tableStartPos = null;
    let shapeStart = null;
    let currentSelectionBox = null;
    let textBlurTimeout = null;
    
    let connectionSource = null;
    let connectionStart = null;
    
    let skewInteractionData = null;

    window.updateDrawingContext = (cardId, fieldName) => {
        if (cardId && fieldName) {
            window.lastDrawingContext.cardId = cardId;
            window.lastDrawingContext.fieldName = fieldName;
        }
    };
    
    window.saveToolStateToPython = () => {
        pycmd(`saveToolState:pencilSize:${currentPencilSize}`);
        pycmd(`saveToolState:eraserSize:${currentEraserSize}`);
        pycmd(`saveToolState:shapeSize:${currentShapeSize}`);
        pycmd(`saveToolState:textSize:${currentTextSize}`);
        pycmd(`saveToolState:lastShape:${currentShape}`);
        pycmd(`saveToolState:lastFilled:${isShapeFilled}`);
        pycmd(`saveToolState:lastColor:${currentPencilColor}`);
    };

    function resizeCanvas() { canvas.width = window.innerWidth; canvas.height = window.innerHeight; redrawHistory(); }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    function toggleDrawingInterface() {
        isDrawingUIHidden = !isDrawingUIHidden;
        toolsContainer.style.display = isDrawingUIHidden ? 'none' : 'grid';
        langSelector.style.display = isDrawingUIHidden ? 'none' : 'flex';
        updateToolUI();
    }

    function setTool(tool) {
        textInputBox.blur();
        if (tool === currentTool) {
            if (tool === 'eraser' && (previousTool === 'pencil' || previousTool === 'pencil2')) { 
                currentTool = previousTool; previousTool = 'eraser'; 
            } 
            else { currentTool = 'none'; previousTool = 'none'; }
        } else {
            if ((currentTool === 'pencil' || currentTool === 'pencil2') && tool === 'eraser') { previousTool = currentTool; } else { previousTool = 'none'; }
            currentTool = tool;
        }
        window.persistentDrawingState.tool = currentTool;
        selectedGroup = []; selectedObject = null; interactionMode = 'NONE'; shapeStart = null; currentSelectionBox = null;
        updateToolUI(); redrawHistory();
    }
    
    function updateToolUI() {
        [selectBtn, pencilBtn, pencil2Btn, textBtn, shapesBtn, eraserBtn, tableBtn, bucketBtn, scissorsBtn, sprayBtn].forEach(btn => btn.classList.remove('tool-active'));
        [pencilOptions, shapeOptions, shapeSubOptions].forEach(p => p.style.display = 'none');
        
        if (currentTool === 'eraser') {
            eraserBtn.classList.add('tool-active'); pencilOptions.style.display = 'flex';
            brushSizeSlider.value = currentEraserSize; if (brushSizeValue) brushSizeValue.textContent = currentEraserSize;
            eraserCursor.style.display = 'block';
        } else {
            eraserCursor.style.display = 'none';
            if (currentTool === 'pencil' || currentTool === 'pencil2' || currentTool === 'text' || currentTool === 'bucket' || currentTool === 'spray') {
                if(currentTool === 'pencil') pencilBtn.classList.add('tool-active');
                if(currentTool === 'pencil2') pencil2Btn.classList.add('tool-active');
                if(currentTool === 'text') textBtn.classList.add('tool-active');
                if(currentTool === 'bucket') bucketBtn.classList.add('tool-active');
                if(currentTool === 'spray') sprayBtn.classList.add('tool-active');
                
                brushSizeSlider.value = currentTool === 'text' ? currentTextSize : currentPencilSize;
                if (brushSizeValue) brushSizeValue.textContent = brushSizeSlider.value;
                pencilOptions.style.display = 'flex';
            } else if (currentTool === 'shapes') {
                shapesBtn.classList.add('tool-active'); pencilOptions.style.display = 'flex'; shapeOptions.style.display = 'grid'; shapeSubOptions.style.display = 'flex';
                brushSizeSlider.value = currentShapeSize; if (brushSizeValue) brushSizeValue.textContent = currentShapeSize;
            } else if (currentTool === 'select') { selectBtn.classList.add('tool-active'); } 
            else if (currentTool === 'table_drawing') { tableBtn.classList.add('tool-active'); }
            else if (currentTool === 'scissors') { scissorsBtn.classList.add('tool-active'); }
        }
        const isCanvasActive = currentTool !== 'none' && !isDrawingUIHidden;
        canvas.style.pointerEvents = isCanvasActive ? 'auto' : 'none';
        canvas.style.zIndex = isCanvasActive ? '999' : '2';
        canvas.style.cursor = (currentTool === 'pencil' || currentTool === 'pencil2' || currentTool === 'table_drawing' || currentTool === 'spray') ? 'crosshair' : (currentTool === 'text' ? 'text' : (currentTool === 'eraser' ? 'none' : (currentTool === 'bucket' || currentTool === 'scissors' ? 'crosshair' : 'default')));
    }

    function saveState() { if (undoStack.length > 50) undoStack.shift(); undoStack.push(JSON.parse(JSON.stringify(drawingHistory))); redoStack = []; }
    function undoLastAction() { if (undoStack.length === 0) return; redoStack.push(JSON.parse(JSON.stringify(drawingHistory))); drawingHistory = undoStack.pop(); redrawHistory(); }
    function redoLastAction() { if (redoStack.length === 0) return; undoStack.push(JSON.parse(JSON.stringify(drawingHistory))); drawingHistory = redoStack.pop(); redrawHistory(); }

    function applyZoom(newZoom) {
        currentZoomLevel = Math.max(0.5, Math.min(2.5, newZoom));
        window.persistentDrawingState.zoomLevel = currentZoomLevel;
        toolsContainer.style.transform = `scale(${currentZoomLevel})`;
        pycmd(`saveZoom:${currentZoomLevel}`);
    }

    function redrawHistory() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        activeUIElements = [];
        let layers = []; let processed = new Set();
        drawingHistory.forEach(item => {
            if (processed.has(item.id)) return;
            if (item.group) { const groupItems = drawingHistory.filter(h => h.group === item.group); layers.push(groupItems); groupItems.forEach(g => processed.add(g.id)); } 
            else { layers.push([item]); processed.add(item.id); }
        });
        layers.forEach(layer => { renderLayerToContext(ctx, layer); });

        if (interactionMode === 'DRAW' && currentPath) { 
            if (currentPath.type === 'spray') {
                drawSpray(ctx, currentPath);
            } else {
                drawObject(ctx, currentPath); 
            }
        }
        if (interactionMode === 'DRAW' && currentTool === 'shapes' && shapeStart) {
            ctx.save(); ctx.strokeStyle = currentPencilColor; ctx.lineWidth = currentShapeSize; ctx.fillStyle = currentPencilColor;
            ctx.globalAlpha = currentOpacity;
            drawShape(ctx, currentShape, shapeStart.x, shapeStart.y, lastX, lastY, currentPencilColor, currentShapeSize, isShapeFilled);
            ctx.restore();
        }
        if (currentTool === 'table_drawing' && tableStartPos) {
            ctx.save(); ctx.strokeStyle = '#00aaff'; ctx.lineWidth = 2; ctx.setLineDash([5, 5]);
            ctx.strokeRect(tableStartPos.x, tableStartPos.y, lastX - tableStartPos.x, lastY - tableStartPos.y);
            ctx.restore();
        }
        if (interactionMode === 'SELECT_AREA') {
            ctx.save(); ctx.strokeStyle = '#00aaff'; ctx.lineWidth = 1; ctx.setLineDash([5, 3]);
            ctx.strokeRect(selectionStart.x, selectionStart.y, lastX - selectionStart.x, lastY - selectionStart.y);
            ctx.restore();
        }
        if (interactionMode === 'CONNECT' && connectionStart) {
            drawConnectionLine(ctx, connectionStart.x, connectionStart.y, lastX, lastY);
        }
        if (selectedGroup.length > 0) { drawSelectionBox(selectedGroup); calculateAndDrawUI(selectedGroup); }
    }

    function renderLayerToContext(targetCtx, items) {
        const isGroup = items.length > 0 && items[0].group;
        if (isGroup || items.some(i => i.type === 'eraser_path')) {
            helperCanvas.width = canvas.width; helperCanvas.height = canvas.height;
            hCtx.clearRect(0, 0, helperCanvas.width, helperCanvas.height);
            items.forEach(obj => { if(obj.type !== 'eraser_path') drawObject(hCtx, obj); });
            items.forEach(obj => { if(obj.type === 'eraser_path') drawObject(hCtx, obj); });
            targetCtx.drawImage(helperCanvas, 0, 0);
        } else { items.forEach(obj => drawObject(targetCtx, obj)); }
    }

    function drawObject(context, obj) {
        context.save();
        context.lineCap = 'round';
        context.lineJoin = 'round';
        
        if (obj.isGrayscale) {
            context.filter = 'grayscale(100%)';
        }

        if (obj.opacity !== undefined) {
            context.globalAlpha = obj.opacity;
        } else {
            context.globalAlpha = 1.0;
        }

        if (obj.effect3D) {
            const isNightMode = document.body.classList.contains('nightMode');
            context.shadowColor = isNightMode ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.6)';
            context.shadowBlur = 10;
            context.shadowOffsetX = 6;
            context.shadowOffsetY = 6;
        } else {
            context.shadowColor = 'transparent';
            context.shadowBlur = 0;
            context.shadowOffsetX = 0;
            context.shadowOffsetY = 0;
        }
        
        const b = getObjectBounds(obj);
        const cx = b.x + b.w / 2;
        const cy = b.y + b.h / 2;

        if (obj.rotation) {
            context.translate(cx, cy);
            context.rotate(obj.rotation);
            context.translate(-cx, -cy);
        }
        
        if (obj.skewX || obj.skewY) {
            const pivotX = b.x;
            const pivotY = b.y + b.h;
            context.translate(pivotX, pivotY);
            context.transform(1, obj.skewY || 0, obj.skewX || 0, 1, 0, 0);
            context.translate(-pivotX, -pivotY);
        }

        if (obj.type === 'eraser_path') {
            context.globalCompositeOperation = 'destination-out'; context.lineWidth = obj.size; context.strokeStyle = 'rgba(0,0,0,1)';
            if (obj.points.length > 0) { context.beginPath(); context.moveTo(obj.points[0].x, obj.points[0].y); for (let i = 1; i < obj.points.length; i++) context.lineTo(obj.points[i].x, obj.points[i].y); context.stroke(); }
        } else if (obj.type === 'path') {
            context.globalCompositeOperation = 'source-over'; context.strokeStyle = obj.color; context.lineWidth = obj.size;
            if (obj.points.length > 0) { context.beginPath(); context.moveTo(obj.points[0].x, obj.points[0].y); for (let i = 1; i < obj.points.length; i++) context.lineTo(obj.points[i].x, obj.points[i].y); context.stroke(); }
        } else if (obj.type === 'smooth_path') {
            context.globalCompositeOperation = 'source-over'; context.strokeStyle = obj.color; context.lineWidth = obj.size;
            if (obj.points.length > 0) {
                context.beginPath();
                context.moveTo(obj.points[0].x, obj.points[0].y);
                if (obj.points.length < 3) {
                    for (let i = 1; i < obj.points.length; i++) context.lineTo(obj.points[i].x, obj.points[i].y);
                } else {
                    for (let i = 1; i < obj.points.length - 2; i++) {
                        const xc = (obj.points[i].x + obj.points[i + 1].x) / 2;
                        const yc = (obj.points[i].y + obj.points[i + 1].y) / 2;
                        context.quadraticCurveTo(obj.points[i].x, obj.points[i].y, xc, yc);
                    }
                    context.quadraticCurveTo(
                        obj.points[obj.points.length - 2].x,
                        obj.points[obj.points.length - 2].y,
                        obj.points[obj.points.length - 1].x,
                        obj.points[obj.points.length - 1].y
                    );
                }
                context.stroke();
            }
        } else if (obj.type === 'spray') {
            context.globalCompositeOperation = 'source-over';
            drawSpray(context, obj);
        } else if (obj.type === 'shape') {
            context.globalCompositeOperation = 'source-over'; context.strokeStyle = obj.color; context.lineWidth = obj.size; context.fillStyle = obj.color;
            drawShape(context, obj.shape, obj.x1, obj.y1, obj.x2, obj.y2, obj.color, obj.size, obj.isFilled);
        } else if (obj.type === 'text') {
            context.globalCompositeOperation = 'source-over'; context.fillStyle = obj.color; drawText(context, obj);
        } else if (obj.type === 'table') {
            context.globalCompositeOperation = 'source-over'; context.strokeStyle = obj.color || 'black'; context.lineWidth = 2; context.fillStyle = 'black'; drawTable(context, obj);
        } else if (obj.type === 'external_image') {
            context.globalCompositeOperation = 'source-over';
            if (obj.imgElement) {
                context.drawImage(obj.imgElement, obj.x, obj.y, obj.width, obj.height);
            } else {
                const img = new Image();
                img.onload = () => { if (typeof redrawHistory === 'function') redrawHistory(); };
                img.src = obj.src;
                obj.imgElement = img;
            }
        } else if (obj.type === 'fill') {
            context.globalCompositeOperation = 'source-over';
            if (obj.imgElement) {
                const drawX = obj.x !== undefined ? obj.x : 0;
                const drawY = obj.y !== undefined ? obj.y : 0;
                const drawW = obj.width !== undefined ? obj.width : canvas.width;
                const drawH = obj.height !== undefined ? obj.height : canvas.height;
                context.drawImage(obj.imgElement, drawX, drawY, drawW, drawH);
            } else {
                const img = new Image();
                img.src = obj.data;
                obj.imgElement = img;
                img.onload = () => { if (typeof redrawHistory === 'function') redrawHistory(); };
            }
        }
        context.restore();
    }

    function getObjectBounds(obj) {
        let padding = (obj.size || 2) / 2 + 5;
        if (obj.type === 'path' || obj.type === 'eraser_path' || obj.type === 'smooth_path' || obj.type === 'spray') {
            let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
            obj.points.forEach(p => { minX = Math.min(minX, p.x); minY = Math.min(minY, p.y); maxX = Math.max(maxX, p.x); maxY = Math.max(maxY, p.y); });
            return { x: minX - padding, y: minY - padding, w: (maxX - minX) + padding*2, h: (maxY - minY) + padding*2 };
        } else if (obj.type === 'shape') {
            if (obj.shape === 'circle') { const r = Math.sqrt(Math.pow(obj.x2 - obj.x1, 2) + Math.pow(obj.y2 - obj.y1, 2)); return { x: obj.x1 - r - padding, y: obj.y1 - r - padding, w: (r * 2) + padding*2, h: (r * 2) + padding*2 }; } 
            else { const x = Math.min(obj.x1, obj.x2); const y = Math.min(obj.y1, obj.y2); const w = Math.abs(obj.x1 - obj.x2); const h = Math.abs(obj.y1 - obj.y2); return { x: x - padding, y: y - padding, w: w + padding*2, h: h + padding*2 }; }
        } else if (obj.type === 'table') {
            const metrics = calculateTableMetrics(ctx, obj); const x = Math.min(obj.x1, obj.x2); const y = Math.min(obj.y1, obj.y2); const w = Math.abs(obj.x1 - obj.x2);
            return { x: x - padding, y: y - padding, w: w + padding*2, h: metrics.totalH + padding*2 };
        } else if (obj.type === 'text') {
            const fontSize = parseInt(obj.size) + 10; const lineHeight = fontSize * 1.2; ctx.font = `${fontSize}px sans-serif`; ctx.textBaseline = 'top'; 
            const lines = obj.text.split('\\\\n'); let maxWidth = 0; for (let line of lines) { const width = ctx.measureText(line).width; if (width > maxWidth) maxWidth = width; }
            const totalHeight = lines.length * lineHeight; return { x: obj.x - padding, y: obj.y - padding, w: maxWidth + padding*2, h: totalHeight + padding*2 };
        } else if (obj.type === 'external_image') {
            return { x: obj.x, y: obj.y, w: obj.width, h: obj.height };
        } else if (obj.type === 'fill') {
            if (obj.bounds) return obj.bounds;
            return { x: 0, y: 0, w: obj.width, h: obj.height };
        }
        return { x: 0, y: 0, w: 0, h: 0 };
    }

    function isRectIntersect(r1, r2) { return !(r2.x > r1.x + r1.w || r2.x + r2.w < r1.x || r2.y > r1.y + r1.h || r2.y + r2.h < r1.y); }
    
    function isPointInObjectBounds(x, y, obj) { 
        let checkX = x; let checkY = y;
        if (obj.rotation) {
            const b = getObjectBounds(obj);
            const cx = b.x + b.w / 2;
            const cy = b.y + b.h / 2;
            const rotated = getRotatedPoint(x, y, cx, cy, obj.rotation);
            checkX = rotated.x; checkY = rotated.y;
        }
        const b = getObjectBounds(obj); 
        if (!(checkX >= b.x && checkX <= b.x + b.w && checkY >= b.y && checkY <= b.y + b.h)) return false;
        if (obj.type === 'fill') {
            hCtx.clearRect(0, 0, helperCanvas.width, helperCanvas.height);
            if (obj.imgElement) {
                const drawX = obj.x !== undefined ? obj.x : 0;
                const drawY = obj.y !== undefined ? obj.y : 0;
                const drawW = obj.width !== undefined ? obj.width : canvas.width;
                const drawH = obj.height !== undefined ? obj.height : canvas.height;
                hCtx.save();
                if (obj.rotation) {
                    const cx = b.x + b.w / 2;
                    const cy = b.y + b.h / 2;
                    hCtx.translate(cx, cy);
                    hCtx.rotate(obj.rotation);
                    hCtx.translate(-cx, -cy);
                }
                hCtx.drawImage(obj.imgElement, drawX, drawY, drawW, drawH);
                hCtx.restore();
                const pixel = hCtx.getImageData(x, y, 1, 1).data;
                return pixel[3] > 10; 
            }
        }
        return true;
    }
    
    function getObjectAt(x, y) { for (let i = drawingHistory.length - 1; i >= 0; i--) { const obj = drawingHistory[i]; if (obj.type === 'eraser_path') continue; if (isPointInObjectBounds(x, y, obj)) return obj; } return null; }
"""

JS_MOUSE_EVENTS = """
    canvas.addEventListener('mousedown', (e) => {
        if (textInputBox.style.display === 'block') { commitText(); }
        const x = e.offsetX; const y = e.offsetY; lastX = x; lastY = y;

        if (currentTool === 'select') {
            let clickedUI = null;
            for (let i = activeUIElements.length - 1; i >= 0; i--) { 
                const ui = activeUIElements[i]; 
                let checkX = x; let checkY = y;
                if (ui.rotation && ui.center) {
                    const rotated = getRotatedPoint(x, y, ui.center.x, ui.center.y, ui.rotation);
                    checkX = rotated.x; checkY = rotated.y;
                }
                if (checkX >= ui.x && checkX <= ui.x + ui.size && checkY >= ui.y && checkY <= ui.y + ui.size) { clickedUI = ui; break; } 
            }

            if (clickedUI) {
                if (clickedUI.type === 'MOVE') { saveState(); selectedGroup = clickedUI.items; interactionMode = 'DRAG'; dragLastX = x; dragLastY = y; } 
                else if (clickedUI.type === 'RESIZE') { saveState(); selectedGroup = clickedUI.items; interactionMode = 'RESIZE'; resizeSnapshot = JSON.parse(JSON.stringify(selectedGroup)); resizeStartBounds = clickedUI.bounds; } 
                else if (clickedUI.type === 'ROTATE') { saveState(); selectedGroup = clickedUI.items; interactionMode = 'ROTATE'; }
                else if (clickedUI.type === 'SKEW') {
                    saveState();
                    selectedGroup = clickedUI.items;
                    interactionMode = 'SKEW';
                    skewInteractionData = clickedUI;
                    resizeSnapshot = JSON.parse(JSON.stringify(selectedGroup));
                    dragLastX = x; dragLastY = y;
                }
                else if (clickedUI.type === 'CONNECT') {
                    interactionMode = 'CONNECT';
                    connectionSource = clickedUI.items[0];
                    const b = getObjectBounds(connectionSource);
                    connectionStart = { x: b.x + b.w / 2, y: b.y + b.h / 2 };
                }
                else if (clickedUI.type.startsWith('TABLE_')) {
                    saveState(); const t = clickedUI.item;
                    if (clickedUI.type === 'TABLE_COL_INC') t.cols++; else if (clickedUI.type === 'TABLE_COL_DEC') t.cols = Math.max(1, t.cols - 1);
                    else if (clickedUI.type === 'TABLE_ROW_INC') t.rows++; else if (clickedUI.type === 'TABLE_ROW_DEC') t.rows = Math.max(1, t.rows - 1);
                }
                redrawHistory(); return;
            }
            const obj = getObjectAt(x, y);
            if (obj) {
                const isAlreadySelected = selectedGroup.some(s => s.id === obj.id);
                if (!isAlreadySelected) {
                    if (obj.group) { selectedGroup = drawingHistory.filter(h => h.group === obj.group); } else { selectedGroup = [obj]; }
                    bindErasersToSelection();
                    if (!selectedGroup[0].group) { const newGroupId = crypto.randomUUID(); selectedGroup.forEach(o => o.group = newGroupId); }
                    selectedObject = selectedGroup[0]; 
                }
                saveState();
                interactionMode = 'DRAG'; dragLastX = x; dragLastY = y;
            } else { selectedGroup = []; selectedObject = null; interactionMode = 'SELECT_AREA'; selectionStart = {x, y}; }
            redrawHistory(); return;
        }
        
        if (currentTool === 'text') { handleTextToolClick(e); return; }
        if (currentTool === 'table_drawing') { tableStartPos = { x: e.offsetX, y: e.offsetY }; return; }
        if (currentTool === 'bucket') return;
        if (currentTool === 'scissors') return;

        interactionMode = 'DRAW'; isDrawing = true; isClearing = false;
        const newObjDefaults = { skewX: 0, skewY: 0 };
        if (currentTool === 'pencil') { 
            saveState(); 
            currentPath = { ...newObjDefaults, id: crypto.randomUUID(), type: 'path', points: [{x: e.offsetX, y: e.offsetY}], color: currentPencilColor, size: currentPencilSize, opacity: currentOpacity, group: null }; 
            drawingHistory.push(currentPath); 
        } 
        else if (currentTool === 'pencil2') { 
            saveState(); 
            currentPath = { ...newObjDefaults, id: crypto.randomUUID(), type: 'smooth_path', points: [{x: e.offsetX, y: e.offsetY}], color: currentPencilColor, size: currentPencilSize, opacity: currentOpacity, group: null }; 
            drawingHistory.push(currentPath); 
        }
        else if (currentTool === 'spray') {
            saveState();
            currentPath = { ...newObjDefaults, id: crypto.randomUUID(), type: 'spray', points: [], color: currentPencilColor, size: currentPencilSize, opacity: currentOpacity, group: null };
            drawingHistory.push(currentPath);
            const density = currentPencilSize * 2;
            for (let i = 0; i < density; i++) {
                const angle = Math.random() * 2 * Math.PI;
                const radius = Math.random() * currentPencilSize * 2;
                const offsetX = Math.cos(angle) * radius;
                const offsetY = Math.sin(angle) * radius;
                currentPath.points.push({x: x + offsetX, y: y + offsetY});
            }
            redrawHistory();
        }
        else if (currentTool === 'eraser') { 
            saveState(); 
            currentPath = { ...newObjDefaults, id: crypto.randomUUID(), type: 'eraser_path', points: [{x: e.offsetX, y: e.offsetY}], size: currentEraserSize, group: null }; 
            drawingHistory.push(currentPath); 
        } 
        else if (currentTool === 'shapes') { shapeStart = { x: x, y: y }; }
        redrawHistory();
    });

    canvas.addEventListener('mousemove', (e) => {
        const x = e.offsetX; const y = e.offsetY; lastX = x; lastY = y;
        if (currentTool === 'eraser') { eraserCursor.style.display = 'block'; eraserCursor.style.width = currentEraserSize + 'px'; eraserCursor.style.height = currentEraserSize + 'px'; eraserCursor.style.left = (e.clientX - currentEraserSize/2) + 'px'; eraserCursor.style.top = (e.clientY - currentEraserSize/2) + 'px'; } else { eraserCursor.style.display = 'none'; }

        if (currentTool === 'select') {
            if (interactionMode === 'SELECT_AREA') { redrawHistory(); } 
            else if (interactionMode === 'DRAG' && selectedGroup.length > 0) {
                const dx = x - dragLastX; const dy = y - dragLastY;
                selectedGroup.forEach(obj => {
                    if (obj.type === 'path' || obj.type === 'eraser_path' || obj.type === 'smooth_path' || obj.type === 'spray') obj.points.forEach(p => { p.x += dx; p.y += dy; });
                    else if (obj.type === 'shape' || obj.type === 'table') { obj.x1 += dx; obj.y1 += dy; obj.x2 += dx; obj.y2 += dy; }
                    else if (obj.type === 'text') { obj.x += dx; obj.y += dy; }
                    else if (obj.type === 'fill' || obj.type === 'external_image') {
                        if (obj.x === undefined) obj.x = 0; if (obj.y === undefined) obj.y = 0;
                        obj.x += dx; obj.y += dy;
                        if (obj.bounds) { obj.bounds.x += dx; obj.bounds.y += dy; }
                    }
                });
                dragLastX = x; dragLastY = y; redrawHistory();
            } else if (interactionMode === 'RESIZE' && selectedGroup.length > 0) {
                const newWidth = Math.max(10, x - resizeStartBounds.x); const newHeight = Math.max(10, y - resizeStartBounds.y);
                const scaleX = newWidth / resizeStartBounds.w; const scaleY = newHeight / resizeStartBounds.h;
                for (let i = 0; i < selectedGroup.length; i++) {
                    const origObj = resizeSnapshot[i]; const currObj = selectedGroup[i]; currObj.size = origObj.size * ((scaleX + scaleY) / 2);
                    if (currObj.type === 'path' || currObj.type === 'eraser_path' || currObj.type === 'smooth_path' || currObj.type === 'spray') { for (let j = 0; j < currObj.points.length; j++) { currObj.points[j].x = resizeStartBounds.x + (origObj.points[j].x - resizeStartBounds.x) * scaleX; currObj.points[j].y = resizeStartBounds.y + (origObj.points[j].y - resizeStartBounds.y) * scaleY; } } 
                    else if (currObj.type === 'shape' || currObj.type === 'table') { currObj.x1 = resizeStartBounds.x + (origObj.x1 - resizeStartBounds.x) * scaleX; currObj.y1 = resizeStartBounds.y + (origObj.y1 - resizeStartBounds.y) * scaleY; currObj.x2 = resizeStartBounds.x + (origObj.x2 - resizeStartBounds.x) * scaleX; currObj.y2 = resizeStartBounds.y + (origObj.y2 - resizeStartBounds.y) * scaleY; } 
                    else if (currObj.type === 'text') { currObj.x = resizeStartBounds.x + (origObj.x - resizeStartBounds.x) * scaleX; currObj.y = resizeStartBounds.y + (origObj.y - resizeStartBounds.y) * scaleY; }
                    else if (currObj.type === 'fill' || currObj.type === 'external_image') {
                        const startX = origObj.x !== undefined ? origObj.x : 0; const startY = origObj.y !== undefined ? origObj.y : 0;
                        currObj.x = resizeStartBounds.x + (startX - resizeStartBounds.x) * scaleX; currObj.y = resizeStartBounds.y + (startY - resizeStartBounds.y) * scaleY;
                        const startW = origObj.width !== undefined ? origObj.width : canvas.width; const startH = origObj.height !== undefined ? origObj.height : canvas.height;
                        currObj.width = startW * scaleX; currObj.height = startH * scaleY;
                        if (currObj.bounds && origObj.bounds) {
                            currObj.bounds.x = resizeStartBounds.x + (origObj.bounds.x - resizeStartBounds.x) * scaleX; currObj.bounds.y = resizeStartBounds.y + (origObj.bounds.y - resizeStartBounds.y) * scaleY;
                            currObj.bounds.w = origObj.bounds.w * scaleX; currObj.bounds.h = origObj.bounds.h * scaleY;
                        }
                    }
                }
                redrawHistory();
            } else if (interactionMode === 'ROTATE' && selectedGroup.length === 1) {
                const obj = selectedGroup[0]; const b = getObjectBounds(obj); const cx = b.x + b.w / 2; const cy = b.y + b.h / 2;
                const angle = calculateRotationAngle(cx, cy, x, y); obj.rotation = angle; redrawHistory();
            } else if (interactionMode === 'SKEW' && selectedGroup.length > 0) {
                const dx = x - dragLastX; const dy = y - dragLastY;
                const dir = skewInteractionData.direction;
                const bounds = skewInteractionData.bounds;

                for (let i = 0; i < selectedGroup.length; i++) {
                    const origObj = resizeSnapshot[i];
                    const currObj = selectedGroup[i];
                    
                    if (dir === 'top' || dir === 'bottom') {
                        let skewX = (origObj.skewX || 0) + (dx / bounds.h);
                        currObj.skewX = Math.max(-5, Math.min(5, skewX)); // Limita a inclinação
                    } else if (dir === 'left' || dir === 'right') {
                        let skewY = (origObj.skewY || 0) + (dy / bounds.w);
                        currObj.skewY = Math.max(-5, Math.min(5, skewY)); // Limita a inclinação
                    }
                }
                redrawHistory();
            }
            else if (interactionMode === 'CONNECT') {
                redrawHistory();
            } else {
                let isOverUI = false; 
                for (let ui of activeUIElements) { 
                    let checkX = x; let checkY = y;
                    if (ui.rotation && ui.center) { const rotated = getRotatedPoint(x, y, ui.center.x, ui.center.y, ui.rotation); checkX = rotated.x; checkY = rotated.y; }
                    if (checkX >= ui.x && checkX <= ui.x + ui.size && checkY >= ui.y && checkY <= ui.y + ui.size) { isOverUI = true; break; } 
                }
                canvas.style.cursor = isOverUI ? 'pointer' : (getObjectAt(x, y) ? 'move' : 'default');
            }
            return;
        }
        if (interactionMode === 'DRAW') {
            if (currentTool === 'pencil' || currentTool === 'pencil2' || currentTool === 'eraser') { if (currentPath) { currentPath.points.push({x, y}); redrawHistory(); } } 
            else if (currentTool === 'spray' && currentPath) {
                const density = currentPencilSize * 1.5;
                for (let i = 0; i < density; i++) {
                    const angle = Math.random() * 2 * Math.PI;
                    const radius = Math.random() * currentPencilSize * 2;
                    const offsetX = Math.cos(angle) * radius;
                    const offsetY = Math.sin(angle) * radius;
                    currentPath.points.push({x: x + offsetX, y: y + offsetY});
                }
                redrawHistory();
            }
            else if (currentTool === 'shapes' && shapeStart) { redrawHistory(); }
        }
        if (currentTool === 'table_drawing' && tableStartPos) { redrawHistory(); }
    });

    canvas.addEventListener('mouseup', (e) => {
        const newObjDefaults = { skewX: 0, skewY: 0 };
        if (currentTool === 'eraser' && currentPath) { bindNewEraserToObjects(currentPath); currentPath = null; redrawHistory(); }
        if ((currentTool === 'pencil' || currentTool === 'pencil2' || currentTool === 'spray') && currentPath) { currentPath = null; }
        if (currentTool === 'shapes' && interactionMode === 'DRAW' && shapeStart) {
            saveState();
            drawingHistory.push({ ...newObjDefaults, id: crypto.randomUUID(), type: 'shape', shape: currentShape, x1: shapeStart.x, y1: shapeStart.y, x2: e.offsetX, y2: e.offsetY, color: currentPencilColor, size: currentShapeSize, isFilled: isShapeFilled, opacity: currentOpacity, group: crypto.randomUUID() });
            shapeStart = null; redrawHistory();
        }
        if (currentTool === 'table_drawing' && tableStartPos) {
            saveState();
            drawingHistory.push({ ...newObjDefaults, id: crypto.randomUUID(), type: 'table', x1: tableStartPos.x, y1: tableStartPos.y, x2: e.offsetX, y2: e.offsetY, rows: tableConfig.rows, cols: tableConfig.cols, color: 'black', size: 2, cellData: {}, group: crypto.randomUUID() });
            tableStartPos = null; setTool('select'); redrawHistory();
        }
        if (currentTool === 'select') {
            if (interactionMode === 'SELECT_AREA') {
                const minX = Math.min(selectionStart.x, lastX); const maxX = Math.max(selectionStart.x, lastX); const minY = Math.min(selectionStart.y, lastY); const maxY = Math.max(selectionStart.y, lastY);
                const selRect = { x: minX, y: minY, w: Math.max(1, maxX-minX), h: Math.max(1, maxY-minY) };
                selectedGroup = [];
                drawingHistory.forEach(obj => {
                    if (obj.type === 'eraser_path') return;
                    if (isRectIntersect(selRect, getObjectBounds(obj))) {
                        if (obj.group) { const fullGroup = drawingHistory.filter(h => h.group === obj.group); fullGroup.forEach(g => { if(!selectedGroup.includes(g)) selectedGroup.push(g); }); } else { selectedGroup.push(obj); }
                    }
                });
                if (selectedGroup.length > 0) { bindErasersToSelection(); if (!selectedGroup[0].group) { const newGroupId = crypto.randomUUID(); selectedGroup.forEach(o => o.group = newGroupId); } selectedObject = selectedGroup[0]; }
                redrawHistory();
            } else if (interactionMode === 'CONNECT') {
                createMindMapLink(connectionSource, e.offsetX, e.offsetY);
                connectionSource = null;
                connectionStart = null;
            }
            resizeSnapshot = [];
            skewInteractionData = null;
        }
        interactionMode = 'NONE'; isDrawing = false;
    });
    
    canvas.addEventListener('dblclick', (e) => { 
        if (currentTool === 'select') { 
            const x = e.offsetX; const y = e.offsetY;
            let clickedUI = null;
            for (let i = activeUIElements.length - 1; i >= 0; i--) { const ui = activeUIElements[i]; if (x >= ui.x && x <= ui.x + ui.size && y >= ui.y && y <= ui.y + ui.size) { clickedUI = ui; break; } }
            if (clickedUI && clickedUI.type === 'MOVE') { saveState(); selectedGroup.forEach(obj => { delete obj.group; }); selectedGroup = []; activeUIElements = []; redrawHistory(); return; }
            const obj = getObjectAt(x, y); 
            if (obj) {
                if (obj.type === 'text') { 
                    selectedObject = obj; textInputBox.value = obj.text; textInputBox.style.left = e.clientX + 'px'; textInputBox.style.top = e.clientY + 'px'; textInputBox.style.color = obj.color; textInputBox.style.fontSize = `${parseInt(obj.size) + 10}px`; textInputBox.style.display = 'block'; textInputBox.dataset.editingId = obj.id; setTimeout(() => textInputBox.focus(), 0); 
                } else if (obj.type === 'table') {
                    const metrics = calculateTableMetrics(ctx, obj); const { rowHeights, cellW, padding } = metrics;
                    const tx = Math.min(obj.x1, obj.x2); const ty = Math.min(obj.y1, obj.y2);
                    let currentY = ty; let row = -1;
                    for(let r=0; r<obj.rows; r++) { if (y >= currentY && y < currentY + rowHeights[r]) { row = r; break; } currentY += rowHeights[r]; }
                    const col = Math.floor((x - tx) / cellW);
                    if (col >= 0 && col < obj.cols && row >= 0 && row < obj.rows) {
                        const cellKey = `${row}-${col}`;
                        let currentText = "", currentColor = "black", currentSize = 16;
                        if (obj.cellData && obj.cellData[cellKey]) { if (typeof obj.cellData[cellKey] === 'object') { currentText = obj.cellData[cellKey].text; currentColor = obj.cellData[cellKey].color; currentSize = parseInt(obj.cellData[cellKey].size); } else { currentText = obj.cellData[cellKey]; } }
                        let cellY = ty; for(let r=0; r<row; r++) cellY += rowHeights[r];
                        textInputBox.value = currentText; textInputBox.style.left = (tx + col * cellW + padding) + 'px'; textInputBox.style.top = (cellY + padding) + 'px'; textInputBox.style.width = (cellW - padding*2) + 'px'; textInputBox.style.height = (rowHeights[row] - padding*2) + 'px'; textInputBox.style.color = currentColor; textInputBox.style.fontSize = `${currentSize}px`; textInputBox.style.display = 'block'; textInputBox.dataset.editingId = obj.id; textInputBox.dataset.tableCell = cellKey;
                        tableTextToolbar.style.display = 'flex'; tableTextToolbar.style.left = tx + 'px'; tableTextToolbar.style.top = (ty - 40) + 'px'; tableTextSizeSlider.value = currentSize; setTimeout(() => textInputBox.focus(), 0);
                    }
                }
            }
        } 
    });
"""

JS_FOOTER = """
    const keysPressed = new Set();
    window.addEventListener('keydown', (e) => { keysPressed.add(e.key.toLowerCase()); if (e.ctrlKey && keysPressed.has('h')) { e.preventDefault(); e.stopPropagation(); toggleDrawingInterface(); keysPressed.clear(); } }, true);
    window.addEventListener('keyup', (e) => { keysPressed.delete(e.key.toLowerCase()); }, true);
    
    document.addEventListener('keydown', (e) => { 
        if (window.checkShortcut(e, 'undo')) { 
            e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); 
            undoLastAction(); return; 
        }
        if (window.checkShortcut(e, 'redo')) { 
            e.preventDefault(); e.stopPropagation(); e.stopImmediatePropagation(); 
            redoLastAction(); return; 
        }
        
        if (document.activeElement.isContentEditable || e.target === textInputBox) return; 
        if (e.key === 'Shift') { isShiftDown = true; } 
        if (e.ctrlKey && !e.shiftKey && !e.altKey && e.key.toLowerCase() === 'c') { copySelection(); return; }
        if (e.ctrlKey && !e.shiftKey && !e.altKey && e.key.toLowerCase() === 'v') { pasteSelection(); return; }
        if (e.key === 'Delete' || e.key === 'Backspace') { if (selectedGroup.length > 0) { e.preventDefault(); saveState(); const idsToDelete = selectedGroup.map(o => o.id); drawingHistory = drawingHistory.filter(obj => !idsToDelete.includes(obj.id)); selectedGroup = []; selectedObject = null; redoStack = []; redrawHistory(); } } 
        
        let actionTriggered = false;
        if (window.checkShortcut(e, 'select')) { setTool('select'); actionTriggered = true; }
        else if (window.checkShortcut(e, 'pencil')) { setTool('pencil'); actionTriggered = true; }
        else if (window.checkShortcut(e, 'pencil2')) { setTool('pencil2'); actionTriggered = true; }
        else if (window.checkShortcut(e, 'spray')) { setTool('spray'); actionTriggered = true; }
        else if (window.checkShortcut(e, 'eraser')) { setTool('eraser'); actionTriggered = true; }
        else if (window.checkShortcut(e, 'bucket')) { setTool('bucket'); actionTriggered = true; }
        else if (window.checkShortcut(e, 'shapes')) { setTool('shapes'); actionTriggered = true; }
        else if (window.checkShortcut(e, 'text')) { setTool('text'); actionTriggered = true; }
        else if (window.checkShortcut(e, 'scissors')) { setTool('scissors'); actionTriggered = true; } 
        else if (window.checkShortcut(e, 'table')) { tableBtn.click(); actionTriggered = true; }
        else if (window.checkShortcut(e, 'icons')) { document.getElementById('iconsTool').click(); actionTriggered = true; }
        else if (window.checkShortcut(e, 'toggle3d')) { document.getElementById('tool-3d').click(); actionTriggered = true; }
        else if (window.checkShortcut(e, 'toggleBw')) { document.getElementById('tool-bw').click(); actionTriggered = true; }
        else if (window.checkShortcut(e, 'clear')) { clearBtn.click(); actionTriggered = true; }
        else if (window.checkShortcut(e, 'save')) { saveBtn.click(); actionTriggered = true; }
        if (actionTriggered) { e.preventDefault(); e.stopPropagation(); }
    }, true);
    document.addEventListener('keyup', (e) => { if (e.key === 'Shift') { isShiftDown = false; } });

    window.clearDrawingCanvas = (isNewCard, newCardId) => {
        isClearing = false;
        if (isNewCard) {
            window.currentCardId = newCardId;
            const shouldClear = window.generalConfig && window.generalConfig.autoClear;
            if (shouldClear) { drawingHistory = []; undoStack = []; redoStack = []; } else { drawingHistory = drawingHistory.filter(item => !item.fromSaved); }
            selectedGroup = []; selectedObject = null; redrawHistory();
        }
    };

    function loadDrawingFromSavedImage() {
        if (isClearing) return;
        const imgs = document.querySelectorAll('img.anki-drawing-image');
        let hasChanges = false;
        const activeCardId = window.currentCardId;
        imgs.forEach(img => {
            const field = img.closest('.editable-field');
            if (!field) return;
            if (activeCardId && field.dataset.cardId != activeCardId) return;
            if (img.dataset.drawingHistory && !img.dataset.loaded) {
                try {
                    window.updateDrawingContext(field.dataset.cardId, field.dataset.fieldName);
                    const historyJson = img.dataset.drawingHistory.replace(/&quot;/g, '"');
                    const data = JSON.parse(historyJson);
                    if (Array.isArray(data) && data.length > 0) {
                        const firstId = data[0].id;
                        const alreadyExists = drawingHistory.some(d => d.id === firstId);
                        if (!alreadyExists) { data.forEach(item => { item.fromSaved = true; item.boundToCardId = activeCardId; }); drawingHistory = drawingHistory.concat(data); hasChanges = true; }
                        img.dataset.loaded = "true"; 
                    }
                } catch (e) { console.error("Erro JSON:", e); }
            }
        });
        if (hasChanges) { redrawHistory(); }
        requestAnimationFrame(loadDrawingFromSavedImage);
    }

    if (!window.ankiDrawingObserver) { window.ankiDrawingObserver = new MutationObserver(() => { loadDrawingFromSavedImage(); }); window.ankiDrawingObserver.observe(document.body, { childList: true, subtree: true }); }
    let checkCount = 0;
    function checkLoop() { loadDrawingFromSavedImage(); checkCount++; if (checkCount < 50) { setTimeout(checkLoop, 50); } else { if (window.drawingLoop) clearInterval(window.drawingLoop); window.drawingLoop = setInterval(() => { loadDrawingFromSavedImage(); }, 500); } }
    checkLoop();

    (function applyRestoredStateToUI() {
        if (window.generalConfig) {
            if (window.generalConfig.colorBehavior === 'keep' && window.generalConfig.lastColor) { currentPencilColor = window.generalConfig.lastColor; window.persistentDrawingState.color = currentPencilColor; } 
            else if (window.generalConfig.colorBehavior === 'red') { currentPencilColor = 'red'; window.persistentDrawingState.color = 'red'; }
        }
        if (window.persistentDrawingState.tool === 'eraser') brushSizeSlider.value = window.persistentDrawingState.eraserSize;
        else if (window.persistentDrawingState.tool === 'shapes') brushSizeSlider.value = window.persistentDrawingState.shapeSize;
        else if (window.persistentDrawingState.tool === 'text') brushSizeSlider.value = window.persistentDrawingState.textSize;
        else brushSizeSlider.value = window.persistentDrawingState.pencilSize;
        eraserCursor.style.width = `${currentEraserSize}px`; eraserCursor.style.height = `${currentEraserSize}px`;
        document.querySelector('.color-swatch.active-color')?.classList.remove('active-color');
        document.querySelector(`.color-swatch[data-color="${currentPencilColor}"]`)?.classList.add('active-color');
        document.querySelector('#shapeOptions .shape-active')?.classList.remove('shape-active');
        document.querySelector(`.shape-btn[data-shape="${currentShape}"]`)?.classList.add('shape-active');
        fillToggleBtn.classList.toggle('tool-active', isShapeFilled);
        
        if (window.persistentDrawingState.opacity !== undefined) {
            currentOpacity = window.persistentDrawingState.opacity;
            const opSlider = document.getElementById('opacitySlider');
            const opVal = document.getElementById('opacityValue');
            if (opSlider) opSlider.value = currentOpacity;
            if (opVal) opVal.textContent = Math.round(currentOpacity * 100) + '%';
        }

        applyZoom(window.persistentDrawingState.zoomLevel);
        updateToolUI();
        loadDrawingFromSavedImage();
        
        document.querySelector(`.lang-flag[data-lang='${window.currentLanguage}']`)?.classList.add('active');
        positionLanguageSelector();
        
        if (window.generalConfig && window.generalConfig.autoSelectPencil) {
            setTool('pencil');
        }
    })();
}
"""

FULL_FEATURE_JS = (
    JS_HEADER + 
    JS_DIGITAR + 
    JS_LAPIS + 
    JS_LAPIS2 +
    JS_SELECIONAR + 
    JS_TEXTO + 
    JS_FORMAS + 
    JS_BORRACHA + 
    JS_TABELA + 
    JS_ICONES + 
    JS_SPRAY + 
    JS_3D +
    JS_PRETOBRANCO +
    JS_MAPA +
    JS_LIMPARTUDO + 
    JS_SALVAR + 
    JS_MOUSE_EVENTS + 
    JS_REDIMENSIONAR + 
    JS_TRANSPARENTE + 
    JS_CORES + 
    JS_BALDE + 
    JS_GIRAR + 
    JS_IMAGENS +
    JS_CORTE +
    JS_FOOTER
)

def prepare_card_for_editing(html: str, card: Card, kind: str) -> str:
    note = card.note()
    fields = sorted(note.items(), key=lambda item: len(item[1]), reverse=True)
    
    for field_name, field_content in fields:
        if field_name in ["MapID", "MapConfig"] or not field_content: continue
        
        has_drawing = 'anki-drawing-image' in field_content
        content_without_drawing = remove_only_drawing_html(field_content)
        
        if not content_without_drawing.strip() and not has_drawing: continue
        
        rendered_content = mw.prepare_card_text_for_display(content_without_drawing)
        escaped_content = re.escape(rendered_content)
        
        img_regex = r'\s*<img[^>]+class=["\']anki-drawing-image["\'][^>]*>'
        
        if not rendered_content.strip():
            full_pattern = f"({img_regex})"
        else:
            full_pattern = f"({escaped_content}(?:{img_regex})?)"

        try:
            pattern = re.compile(full_pattern, re.DOTALL)
            match = pattern.search(html)
        except re.error: match = None
        
        if not match and has_drawing:
            try:
                pattern = re.compile(f"({img_regex})", re.DOTALL)
                match = pattern.search(html)
            except re.error: match = None

        if not match: continue
        
        to_replace = match.group(0)
        encoded_original_content = base64.b64encode(field_content.encode('utf-8')).decode('utf-8')
        
        wrapper = f'<div class="editable-field" data-card-id="{card.id}" data-field-name="{field_name}" data-original-content="{encoded_original_content}">{to_replace}</div>'
        html = html.replace(to_replace, wrapper, 1)
        
    return html

def on_reviewer_show_question(card: Card):
    try:
        web = mw.reviewer.web
        if not web: return
        web.eval(f"if(window.clearDrawingCanvas) window.clearDrawingCanvas(true, {card.id});")
        QTimer.singleShot(10, lambda: inject_full_features(web, mw.reviewer))
    except: pass

def on_reviewer_show_answer(card: Card):
    try:
        web = mw.reviewer.web
        if not web: return
        QTimer.singleShot(10, lambda: inject_full_features(web, mw.reviewer))
    except: pass

def on_receive_js_message(handled, message, context):
    global g_editable_context_active
    
    if message == "context:editable_field":
        g_editable_context_active = True
        return (True, None)
    if message == "context:clear":
        g_editable_context_active = False
        return (True, None)
        
    if isinstance(message, str) and message.startswith("saveZoom:"):
        try: save_zoom_config(float(message.split(":")[1]))
        except: pass
        return (True, None)
        
    if isinstance(message, str) and message.startswith("saveColor:"):
        try:
            new_color = message.split(":")[1]
            config = load_general_config()
            config["lastColor"] = new_color
            save_general_config(config)
        except: pass
        return (True, None)
    
    if isinstance(message, str) and message.startswith("saveToolPosition:"):
        try:
            parts = message.split(":")
            top = parts[1]
            left = parts[2]
            save_ui_state({"top": top, "left": left})
        except: pass
        return (True, None)
    
    if isinstance(message, str) and message.startswith("saveToolState:"):
        handle_state_save(message)
        return (True, None)
        
    if isinstance(message, str) and message.startswith("saveDrawing:"):
        handle_save_message(message, context)
        return (True, None)
        
    if isinstance(message, str) and message.startswith("clearDrawing:"):
        handle_clear_message(message, context)
        return (True, None)
        
    if isinstance(message, str) and message.startswith("saveOpacity:"):
        handle_opacity_save(message)
        return (True, None)

    if isinstance(message, str) and message.startswith("saveLanguage:"):
        try:
            lang = message.split(":")[1]
            config = load_general_config()
            config["language"] = lang
            save_general_config(config)
            
            update_config_menu_text()
            
            new_translations = en_translations if lang == "en" else pt_translations
            return (True, json.dumps(new_translations))
        except:
            return (True, "{}")

    if message == "chooseFont":
        from .texto import handle_font_request
        font_data = handle_font_request()
        return (True, json.dumps(font_data) if font_data else "null")
    
    if isinstance(message, str) and (message == "requestIcons" or message == "addIcon" or message.startswith("deleteIcon:")):
        return (True, handle_icons_request(message))

    if isinstance(message, str) and message.startswith("editField:"):
        try:
            should_reset = message.startswith("editField:reset:")
            prefix = "editField:reset:" if should_reset else "editField:silent:"
            payload = message[len(prefix):]
            
            parts = payload.split("::तां::", 1)
            header_parts = parts[0].split(":", 1)
            card_id = int(header_parts[0])
            field_name = header_parts[1]
            new_html = parts[1]
            
            card = mw.col.get_card(card_id)
            if not card: return (True, None)
            
            note = card.note()
            if field_name in note:
                drawings = re.findall(r'<img class="anki-drawing-image"[^>]*>', note[field_name])
                clean_new_html = remove_only_drawing_html(new_html)
                note[field_name] = clean_new_html + "".join(drawings)
                
                mw.col.update_note(note)
                
                if mw.state == "review" and mw.reviewer.card and mw.reviewer.card.id == card_id:
                    mw.reviewer.card.load()
                
                if should_reset:
                    if isinstance(context, Editor): context.loadNote(focusTo=None)
                    elif isinstance(context, Browser): context.onRowChanged(None, None)
            return (True, None)
        except: return (True, None)
        
    return handled

def on_context_menu(webview: AnkiWebView, menu):
    global g_editable_context_active
    if not g_editable_context_active: return
    clipboard = QGuiApplication.clipboard()
    mime_data = clipboard.mimeData()
    content_to_paste = None
    if mime_data.hasImage():
        image = clipboard.image()
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        b64_data = base64.b64encode(buffer.data().data()).decode('utf-8')
        content_to_paste = f'<img src="data:image/png;base64,{b64_data}" />'
    elif mime_data.hasHtml(): content_to_paste = mime_data.html()
    elif mime_data.hasText(): content_to_paste = mime_data.text()
    if content_to_paste:
        js_safe_content = json.dumps(content_to_paste)
        action = QAction("Colar (Addon)", menu)
        action.triggered.connect(lambda _, w=webview, js=f"window.insertDataFromPython({js_safe_content});": w.eval(js))
        menu.addAction(action)
    g_editable_context_active = False

def image_to_base64(filename):
    addon_dir = os.path.dirname(__file__)
    filepath = os.path.join(addon_dir, filename)
    if not os.path.exists(filepath):
        return ""
    
    ext = filename.split('.')[-1].lower()
    mime_type = f"image/{'jpeg' if ext == 'jpg' else ext}"
    
    with open(filepath, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    return f"data:{mime_type};base64,{encoded_string}"

def inject_full_features(webview: AnkiWebView, context_object):
    if not webview: return
    saved_zoom = load_zoom_config()
    shortcut_config = load_shortcut_config()
    general_config = load_general_config()
    ui_state = load_ui_state()
    
    lang = general_config.get("language", "pt")
    translations = en_translations if lang == "en" else pt_translations
    
    flag_br_b64 = image_to_base64("br.jpg")
    flag_us_b64 = image_to_base64("us.jpg")
    
    webview.eval(f"window.initialZoomLevel = {saved_zoom};")
    webview.eval(f"window.userShortcuts = {json.dumps(shortcut_config)};")
    webview.eval(f"window.generalConfig = {json.dumps(general_config)};")
    webview.eval(f"window.initialToolPosition = {json.dumps(ui_state)};")
    webview.eval(f"window.translations = {json.dumps(translations)};")
    webview.eval(f"window.currentLanguage = '{lang}';")
    webview.eval(f"window.flag_br = '{flag_br_b64}';")
    webview.eval(f"window.flag_us = '{flag_us_b64}';")
    
    symbol_map = {}
    if hasattr(mw, 'ins_sym_manager'):
        try: symbol_map = {item[0]: item[1] for item in mw.ins_sym_manager.get_list()}
        except: pass
    webview.eval(f"window.revisorSymbolMap = {json.dumps(symbol_map)};")
    
    webview.set_bridge_command(lambda msg: on_receive_js_message(False, msg, context_object), webview)
    webview.eval(FULL_FEATURE_JS)

try:
    original_render_preview = Editor._render_preview
    def custom_render_preview(self: Editor, *args, **kwargs):
        original_render_preview(self, *args, **kwargs)
        if self.web:
            self.web.eval("if(window.clearDrawingCanvas) window.clearDrawingCanvas(true, 0);")
            inject_full_features(self.web, self)
    Editor._render_preview = custom_render_preview
except: pass

try:
    original_on_row_changed = Browser.onRowChanged
    def custom_on_row_changed(self: Browser, current, previous):
        original_on_row_changed(self, current, previous)
        preview_web = None
        if hasattr(self, "_previewer") and self._previewer:
            if hasattr(self._previewer, "web"): preview_web = self._previewer.web
            elif hasattr(self._previewer, "_web"): preview_web = self._previewer._web
        if preview_web:
            card_id = self.card.id if self.card else 0
            preview_web.eval(f"if(window.clearDrawingCanvas) window.clearDrawingCanvas(true, {card_id});")
            inject_full_features(preview_web, self)
    Browser.onRowChanged = custom_on_row_changed
except: pass

try:
    original_on_toggle_preview = Browser.onTogglePreview
    def custom_on_toggle_preview(self: Browser, *args, **kwargs):
        original_on_toggle_preview(self, *args, **kwargs)
        preview_web = None
        if hasattr(self, "_previewer") and self._previewer:
            if hasattr(self._previewer, "web"): preview_web = self._previewer.web
            elif hasattr(self._previewer, "_web"): preview_web = self._previewer._web
        if preview_web: inject_full_features(preview_web, self)
    Browser.onTogglePreview = custom_on_toggle_preview
except: pass

def on_main_window_init():
    """Adiciona o item de menu quando a janela principal do Anki estiver pronta."""
    add_config_menu_item()

gui_hooks.main_window_did_init.append(on_main_window_init)
hooks.field_filter.append(edit_field_filter)
gui_hooks.card_will_show.append(prepare_card_for_editing)
gui_hooks.webview_did_receive_js_message.append(on_receive_js_message)
gui_hooks.webview_will_show_context_menu.append(on_context_menu)
gui_hooks.reviewer_did_show_question.append(on_reviewer_show_question)
gui_hooks.reviewer_did_show_answer.append(on_reviewer_show_answer)
