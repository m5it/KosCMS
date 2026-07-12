"""
Operational Transformation (OT) for collaborative editing

Ensures consistency when multiple users edit the same document simultaneously.
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Operation:
    """Single edit operation."""
    type: str  # 'insert', 'delete', 'retain'
    position: int
    content: str = ""
    length: int = 0  # for delete/retain
    
    def to_dict(self) -> Dict:
        return {
            "type": self.type,
            "position": self.position,
            "content": self.content,
            "length": self.length
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Operation":
        return cls(
            type=data["type"],
            position=data["position"],
            content=data.get("content", ""),
            length=data.get("length", 0)
        )


class OperationalTransformation:
    """
    Operational Transformation algorithm for collaborative text editing.
    
    Transforms operations so they can be applied in different orders
    while maintaining document consistency.
    """
    
    @staticmethod
    def transform(op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """
        Transform two operations against each other.
        
        Returns transformed operations that can be applied in sequence.
        """
        # Handle different operation type combinations
        if op1.type == "insert" and op2.type == "insert":
            return OperationalTransformation._transform_insert_insert(op1, op2)
        elif op1.type == "insert" and op2.type == "delete":
            return OperationalTransformation._transform_insert_delete(op1, op2)
        elif op1.type == "delete" and op2.type == "insert":
            op2_t, op1_t = OperationalTransformation._transform_insert_delete(op2, op1)
            return op1_t, op2_t
        elif op1.type == "delete" and op2.type == "delete":
            return OperationalTransformation._transform_delete_delete(op1, op2)
        elif op1.type == "retain" or op2.type == "retain":
            return op1, op2
        
        return op1, op2
    
    @staticmethod
    def _transform_insert_insert(op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform two insert operations."""
        if op1.position < op2.position:
            # op1 comes first, op2 shifts right
            op2_t = Operation("insert", op2.position + len(op1.content), op2.content)
            return op1, op2_t
        elif op1.position > op2.position:
            # op2 comes first, op1 shifts right
            op1_t = Operation("insert", op1.position + len(op2.content), op1.content)
            return op1_t, op2
        else:
            # Same position - use tiebreaker (user ID or timestamp)
            # Here we keep op1 first
            op2_t = Operation("insert", op2.position + len(op1.content), op2.content)
            return op1, op2_t
    
    @staticmethod
    def _transform_insert_delete(op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform insert against delete."""
        if op1.position <= op2.position:
            # Insert before delete - delete shifts right
            op2_t = Operation("delete", op2.position + len(op1.content), length=op2.length)
            return op1, op2_t
        elif op1.position >= op2.position + op2.length:
            # Insert after delete - insert shifts left
            op1_t = Operation("insert", op1.position - op2.length, op1.content)
            return op1_t, op2
        else:
            # Insert inside deleted range - split delete
            before_len = op1.position - op2.position
            after_len = op2.length - before_len
            op2_t = Operation("delete", op2.position, length=before_len)
            op1_t = Operation("insert", op2.position, op1.content)
            return op1_t, op2_t
    
    @staticmethod
    def _transform_delete_delete(op1: Operation, op2: Operation) -> Tuple[Operation, Operation]:
        """Transform two delete operations."""
        # Simplified: if ranges overlap, adjust
        if op1.position + op1.length <= op2.position:
            # op1 before op2
            op2_t = Operation("delete", op2.position - op1.length, length=op2.length)
            return op1, op2_t
        elif op2.position + op2.length <= op1.position:
            # op2 before op1
            op1_t = Operation("delete", op1.position - op2.length, length=op1.length)
            return op1_t, op2
        else:
            # Overlapping - complex case, simplified here
            return op1, op2
    
    @staticmethod
    def compose(ops: List[Operation]) -> List[Operation]:
        """
        Compose multiple operations into a single operation.
        Reduces network traffic.
        """
        if not ops:
            return []
        
        composed = [ops[0]]
        
        for op in ops[1:]:
            last = composed[-1]
            
            # Merge adjacent inserts
            if last.type == "insert" and op.type == "insert":
                if last.position + len(last.content) == op.position:
                    last.content += op.content
                    continue
            
            # Merge adjacent deletes
            if last.type == "delete" and op.type == "delete":
                if last.position + last.length == op.position:
                    last.length += op.length
                    continue
            
            composed.append(op)
        
        return composed
    
    @staticmethod
    def apply_operations(text: str, operations: List[Operation]) -> str:
        """Apply operations to text."""
        # Sort by position in reverse to avoid position shifts
        sorted_ops = sorted(operations, key=lambda o: o.position, reverse=True)
        
        result = text
        for op in sorted_ops:
            if op.type == "insert":
                result = result[:op.position] + op.content + result[op.position:]
            elif op.type == "delete":
                result = result[:op.position] + result[op.position + op.length:]
        
        return result
