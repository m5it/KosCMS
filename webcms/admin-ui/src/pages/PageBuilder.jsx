import React, { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import Button from '../components/Button';

function SortableBlock({ id, type, content, onRemove }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    padding: '1rem',
    marginBottom: '0.5rem',
    border: '1px solid var(--border-color)',
    borderRadius: '4px',
    background: 'var(--bg-color)',
    cursor: 'grab'
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <strong>{type}</strong>
        <Button variant="secondary" onClick={() => onRemove(id)}>Remove</Button>
      </div>
      <p>{content}</p>
    </div>
  );
}

function PageBuilder() {
  const [blocks, setBlocks] = useState([
    { id: '1', type: 'Hero', content: 'Welcome to our site' },
    { id: '2', type: 'Text', content: 'About our company' },
    { id: '3', type: 'Image', content: 'Team photo' }
  ]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates
    })
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over.id) {
      setBlocks((items) => {
        const oldIndex = items.findIndex((item) => item.id === active.id);
        const newIndex = items.findIndex((item) => item.id === over.id);
        return arrayMove(items, oldIndex, newIndex);
      });
    }
  };

  const addBlock = () => {
    const id = String(blocks.length + 1);
    setBlocks([...blocks, { id, type: 'Text', content: 'New block content' }]);
  };

  const removeBlock = (id) => {
    setBlocks(blocks.filter((block) => block.id !== id));
  };

  return (
    <div>
      <h1>Page Builder</h1>
      <Button onClick={addBlock}>Add Block</Button>
      <div className="drop-zone">
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={blocks.map((b) => b.id)} strategy={verticalListSortingStrategy}>
            {blocks.map((block) => (
              <SortableBlock
                key={block.id}
                id={block.id}
                type={block.type}
                content={block.content}
                onRemove={removeBlock}
              />
            ))}
          </SortableContext>
        </DndContext>
      </div>
    </div>
  );
}

export default PageBuilder;
