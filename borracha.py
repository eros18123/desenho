# -*- coding: utf-8 -*-

JS_BORRACHA = """
    eraserBtn.addEventListener('click', () => setTool('eraser'));
    eraserBtn.addEventListener('dblclick', (e) => { e.preventDefault(); e.stopPropagation(); setTool('none'); });

    function bindNewEraserToObjects(eraserStroke) {
        const eraserBounds = getObjectBounds(eraserStroke);
        const groupsHit = new Set();
        const ungroupedObjectsHit = [];

        for (let i = drawingHistory.length - 2; i >= 0; i--) { 
            const obj = drawingHistory[i];
            if (obj.type === 'eraser_path') continue; 
            
            if (isRectIntersect(eraserBounds, getObjectBounds(obj))) {
                if (obj.group) {
                    groupsHit.add(obj.group);
                } else {
                    ungroupedObjectsHit.push(obj);
                }
            }
        }

        ungroupedObjectsHit.forEach(obj => {
            const newGroupId = crypto.randomUUID();
            obj.group = newGroupId;
            groupsHit.add(newGroupId);
        });

        const uniqueGroups = Array.from(groupsHit);

        if (uniqueGroups.length === 0) {
            return;
        }

        eraserStroke.group = uniqueGroups[0];

        for (let i = 1; i < uniqueGroups.length; i++) {
            const groupId = uniqueGroups[i];
            const eraserClone = JSON.parse(JSON.stringify(eraserStroke));
            eraserClone.id = crypto.randomUUID(); 
            eraserClone.group = groupId;          
            drawingHistory.push(eraserClone);
        }
    }

    function bindErasersToSelection() {
        const shapes = selectedGroup.filter(o => o.type !== 'eraser_path');
        shapes.forEach(shape => {
            const shapeBounds = getObjectBounds(shape);
            drawingHistory.forEach(h => {
                if (h.type === 'eraser_path' && !selectedGroup.includes(h)) {
                    if (isRectIntersect(shapeBounds, getObjectBounds(h))) {
                        if (!h.group || (shape.group && h.group === shape.group)) {
                            selectedGroup.push(h);
                        }
                    }
                }
            });
        });
    }
"""