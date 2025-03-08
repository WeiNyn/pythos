"""
State persistence and checkpoint system
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
import json
import sqlite3
import shutil
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Checkpoint:
    """Represents a task state checkpoint"""
    id: str  # Unique identifier
    timestamp: datetime
    task_id: str
    description: str
    state: Dict[str, Any]
    parent_id: Optional[str] = None  # Previous checkpoint ID

class StateStorage(ABC):
    """Abstract base class for state storage implementations"""
    
    @abstractmethod
    def save_state(self, task_id: str, state: Dict[str, Any]) -> None:
        """Save task state"""
        pass
        
    @abstractmethod
    def load_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task state"""
        pass
        
    @abstractmethod
    def create_checkpoint(self, task_id: str, description: str) -> Checkpoint:
        """Create a checkpoint of current state"""
        pass
        
    @abstractmethod
    def restore_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Restore state from checkpoint"""
        pass
        
    @abstractmethod
    def list_checkpoints(self, task_id: str) -> List[Checkpoint]:
        """List checkpoints for task"""
        pass

class JsonStateStorage(StateStorage):
    """JSON file-based state storage"""
    
    def __init__(self, base_path: Path):
        """Initialize with base storage path"""
        self.base_path = base_path
        self.state_path = base_path / "states"
        self.checkpoint_path = base_path / "checkpoints"
        
        # Create directories
        self.state_path.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.mkdir(parents=True, exist_ok=True)
        
    def save_state(self, task_id: str, state: Dict[str, Any]) -> None:
        """Save task state to JSON file"""
        path = self.state_path / f"{task_id}.json"
        with open(path, "w") as f:
            json.dump(state, f, indent=2)
            
    def load_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task state from JSON file"""
        path = self.state_path / f"{task_id}.json"
        if not path.exists():
            return None
            
        with open(path) as f:
            return json.load(f)
            
    def create_checkpoint(self, task_id: str, description: str) -> Checkpoint:
        """Create state checkpoint"""
        state = self.load_state(task_id)
        if not state:
            raise ValueError(f"No state found for task {task_id}")
            
        # Find parent checkpoint
        checkpoints = self.list_checkpoints(task_id)
        parent_id = checkpoints[-1].id if checkpoints else None
            
        # Create checkpoint
        checkpoint = Checkpoint(
            id=f"{task_id}_{len(checkpoints) + 1}",
            timestamp=datetime.utcnow(),
            task_id=task_id,
            description=description,
            state=state,
            parent_id=parent_id
        )
        
        # Save checkpoint
        path = self.checkpoint_path / f"{checkpoint.id}.json"
        with open(path, "w") as f:
            json.dump({
                "id": checkpoint.id,
                "timestamp": checkpoint.timestamp.isoformat(),
                "task_id": checkpoint.task_id,
                "description": checkpoint.description,
                "state": checkpoint.state,
                "parent_id": checkpoint.parent_id
            }, f, indent=2)
            
        return checkpoint
        
    def restore_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Restore state from checkpoint"""
        path = self.checkpoint_path / f"{checkpoint_id}.json"
        if not path.exists():
            raise ValueError(f"Checkpoint {checkpoint_id} not found")
            
        with open(path) as f:
            data = json.load(f)
            self.save_state(data["task_id"], data["state"])
            return data["state"]
            
    def list_checkpoints(self, task_id: str) -> List[Checkpoint]:
        """List checkpoints for task"""
        checkpoints = []
        for path in self.checkpoint_path.glob(f"{task_id}_*.json"):
            with open(path) as f:
                data = json.load(f)
                checkpoints.append(Checkpoint(
                    id=data["id"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    task_id=data["task_id"],
                    description=data["description"],
                    state=data["state"],
                    parent_id=data["parent_id"]
                ))
                
        return sorted(checkpoints, key=lambda x: x.timestamp)

class SqliteStateStorage(StateStorage):
    """SQLite-based state storage"""
    
    def __init__(self, db_path: Path):
        """Initialize database connection"""
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self) -> None:
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS states (
                    task_id TEXT PRIMARY KEY,
                    state TEXT,
                    updated_at TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    task_id TEXT,
                    timestamp TIMESTAMP,
                    description TEXT,
                    state TEXT,
                    parent_id TEXT,
                    FOREIGN KEY (task_id) REFERENCES states(task_id)
                )
            """)
            conn.commit()
            
    def save_state(self, task_id: str, state: Dict[str, Any]) -> None:
        """Save task state to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO states (task_id, state, updated_at)
                VALUES (?, ?, ?)
            """, (task_id, json.dumps(state), datetime.utcnow().isoformat()))
            conn.commit()
            
    def load_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task state from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT state FROM states WHERE task_id = ?",
                (task_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            return json.loads(row[0])
            
    def create_checkpoint(self, task_id: str, description: str) -> Checkpoint:
        """Create state checkpoint in database"""
        state = self.load_state(task_id)
        if not state:
            raise ValueError(f"No state found for task {task_id}")
            
        # Find parent checkpoint
        checkpoints = self.list_checkpoints(task_id)
        parent_id = checkpoints[-1].id if checkpoints else None
        
        # Create checkpoint
        checkpoint = Checkpoint(
            id=f"{task_id}_{len(checkpoints) + 1}",
            timestamp=datetime.utcnow(),
            task_id=task_id,
            description=description,
            state=state,
            parent_id=parent_id
        )
        
        # Save checkpoint
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO checkpoints 
                (id, task_id, timestamp, description, state, parent_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                checkpoint.id,
                checkpoint.task_id,
                checkpoint.timestamp.isoformat(),
                checkpoint.description,
                json.dumps(checkpoint.state),
                checkpoint.parent_id
            ))
            conn.commit()
            
        return checkpoint
        
    def restore_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Restore state from checkpoint"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT task_id, state 
                FROM checkpoints 
                WHERE id = ?
            """, (checkpoint_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Checkpoint {checkpoint_id} not found")
                
            task_id, state = row
            state_dict = json.loads(state)
            self.save_state(task_id, state_dict)
            return state_dict
            
    def list_checkpoints(self, task_id: str) -> List[Checkpoint]:
        """List checkpoints for task"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, timestamp, description, state, parent_id
                FROM checkpoints
                WHERE task_id = ?
                ORDER BY timestamp
            """, (task_id,))
            
            return [
                Checkpoint(
                    id=row[0],
                    timestamp=datetime.fromisoformat(row[1]),
                    task_id=task_id,
                    description=row[2],
                    state=json.loads(row[3]),
                    parent_id=row[4]
                )
                for row in cursor.fetchall()
            ]
