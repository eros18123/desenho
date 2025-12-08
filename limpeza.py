# -*- coding: utf-8 -*-
from aqt import mw
from aqt.utils import askUser, showInfo
from bs4 import BeautifulSoup

# A importação de 'atalhos' foi removida do topo

def on_wipe_data():
    # Importação movida para dentro da função para quebrar o ciclo
    from .atalhos import get_config_translations
    t = get_config_translations()

    # 1. Confirmação de Segurança
    if not askUser(
        f"{t['wipe_warning_header']}\n\n{t['wipe_warning_body']}",
        title=t['wipe_warning_title']
    ):
        return

    # 2. Inicia o processo
    mw.checkpoint(t['wipe_warning_title'])
    mw.progress.start(label=t['wiping_collection'], immediate=True)
    
    try:
        notes = mw.col.find_notes("")
        total = len(notes)
        modified_count = 0
        
        for idx, nid in enumerate(notes):
            if idx % 100 == 0:
                mw.progress.update(value=idx, max=total)
            
            note = mw.col.get_note(nid)
            changed = False
            
            for f_name, f_val in note.items():
                if "anki-drawing-image" in f_val or "editable-field" in f_val:
                    soup = BeautifulSoup(f_val, "html.parser")
                    has_mod = False

                    for img in soup.find_all("img", class_="anki-drawing-image"):
                        img.decompose()
                        has_mod = True
                        
                    for div in soup.find_all("div", class_="editable-field"):
                        div.unwrap()
                        has_mod = True
                    
                    if has_mod:
                        note[f_name] = str(soup)
                        changed = True
            
            if changed:
                mw.col.update_note(note)
                modified_count += 1
        
        mw.progress.finish()
        mw.reset()
        showInfo(t['wipe_complete'].format(count=modified_count))
        
    except Exception as e:
        mw.progress.finish()
        showInfo(t['wipe_error'].format(error=str(e)))