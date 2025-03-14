"""
State persistence and checkpoint system
"""

import json
import sqlite3
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..json_utils import DateTimeJSONEncoder, json_decoder_hook


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

    @abstractmethod
    def get_related_tasks(self, task_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get related tasks by similarity"""
        pass

    @abstractmethod
    def search_task_history(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Search task history with relevance scores"""
        pass


class JsonStateStorage(StateStorage):
    """JSON file-based state storage"""

    def __init__(self, base_path: Path):
        """Initialize with base storage path"""
        self.base_path = base_path
        self.state_path = base_path / "states"
        self.checkpoint_path = base_path / "checkpoints"
        self.context_path = base_path / "context"

        # Create directories
        self.state_path.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.mkdir(parents=True, exist_ok=True)
        self.context_path.mkdir(parents=True, exist_ok=True)

    def save_state(self, task_id: str, state: Dict[str, Any]) -> None:
        """Save task state to JSON file"""
        path = self.state_path / f"{task_id}.json"
        with open(path, "w") as f:
            json.dump(state, f, indent=2, cls=DateTimeJSONEncoder)

        # Save messages separately to maintain searchability
        messages_path = self.state_path / f"{task_id}_messages.json"
        with open(messages_path, "w") as f:
            json.dump(
                {"messages": state.get("messages", [])},
                f,
                indent=2,
                cls=DateTimeJSONEncoder,
            )

        # Save context
        context_path = self.context_path / f"{task_id}_context.json"
        with open(context_path, "w") as f:
            json.dump(
                {"context": state.get("context", {})},
                f,
                indent=2,
                cls=DateTimeJSONEncoder,
            )

    def load_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task state from JSON file"""
        path = self.state_path / f"{task_id}.json"
        if not path.exists():
            return None

        state = {}
        # Load main state
        with open(path) as f:
            state = json.load(f, object_hook=json_decoder_hook)

        # Load messages if they exist
        messages_path = self.state_path / f"{task_id}_messages.json"
        if messages_path.exists():
            with open(messages_path) as f:
                messages_data = json.load(f, object_hook=json_decoder_hook)
                state["messages"] = messages_data.get("messages", [])

        # Load context if it exists
        context_path = self.context_path / f"{task_id}_context.json"
        if context_path.exists():
            with open(context_path) as f:
                context_data = json.load(f, object_hook=json_decoder_hook)
                state["context"] = context_data.get("context", {})

        return state

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
            parent_id=parent_id,
        )

        # Save checkpoint
        path = self.checkpoint_path / f"{checkpoint.id}.json"
        with open(path, "w") as f:
            checkpoint_data = {
                "id": checkpoint.id,
                "timestamp": checkpoint.timestamp.isoformat(),
                "task_id": checkpoint.task_id,
                "description": checkpoint.description,
                "state": checkpoint.state,
                "parent_id": checkpoint.parent_id,
            }
            json.dump(checkpoint_data, f, indent=2, cls=DateTimeJSONEncoder)

        return checkpoint

    def restore_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """Restore state from checkpoint"""
        path = self.checkpoint_path / f"{checkpoint_id}.json"
        if not path.exists():
            raise ValueError(f"Checkpoint {checkpoint_id} not found")

        with open(path) as f:
            data = json.load(f, object_hook=json_decoder_hook)
            self.save_state(data["task_id"], data["state"])
            return data["state"]

    def list_checkpoints(self, task_id: str) -> List[Checkpoint]:
        """List checkpoints for task"""
        checkpoints = []
        for path in self.checkpoint_path.glob(f"{task_id}_*.json"):
            with open(path) as f:
                data = json.load(f)
                checkpoints.append(
                    Checkpoint(
                        id=data["id"],
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        task_id=data["task_id"],
                        description=data["description"],
                        state=data["state"],
                        parent_id=data["parent_id"],
                    )
                )

        return sorted(checkpoints, key=lambda x: x.timestamp)

    def get_related_tasks(self, task_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get related tasks by checking context and content similarity"""
        current_state = self.load_state(task_id)
        if not current_state:
            return []

        related = []
        # Get all task states
        for path in self.state_path.glob("*.json"):
            if not path.name.endswith("_messages.json") and not path.name.endswith("_context.json"):
                other_id = path.stem
                if other_id != task_id:
                    other_state = self.load_state(other_id)
                    if other_state:
                        # Compare contexts
                        context_similarity = self._compute_context_similarity(
                            current_state.get("context", {}),
                            other_state.get("context", {}),
                        )
                        if context_similarity > 0:
                            related.append(
                                {
                                    "task_id": other_id,
                                    "task": other_state.get("task", ""),
                                    "similarity": context_similarity,
                                    "completed": other_state.get("is_complete", False),
                                }
                            )

        # Sort by similarity and return top matches
        related.sort(key=lambda x: x["similarity"], reverse=True)
        return related[:limit]

    def search_task_history(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Search task history with relevance scores"""
        results = []

        # Search through all message files
        for path in self.state_path.glob("*_messages.json"):
            task_id = path.name.replace("_messages.json", "")
            with open(path) as f:
                messages = json.load(f).get("messages", [])

            # Simple relevance scoring based on term frequency
            score = sum(1 for msg in messages if query.lower() in msg.get("content", "").lower())

            if score > 0:
                results.append((task_id, score))

        # Sort by relevance score
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def _compute_context_similarity(self, ctx1: Dict[str, Any], ctx2: Dict[str, Any]) -> float:
        """Compute similarity score between two contexts"""
        # Simple implementation - count shared keys and values
        shared_keys = set(ctx1.keys()) & set(ctx2.keys())
        if not shared_keys:
            return 0.0

        # Count exact value matches
        matching_values = sum(1 for k in shared_keys if ctx1[k] == ctx2[k])

        # Compute similarity score
        return matching_values / max(len(ctx1), len(ctx2))


class SqliteStateStorage(StateStorage):
    """SQLite-based state storage"""

    def __init__(self, db_path: Path):
        """Initialize database connection"""
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Base state table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS states (
                    task_id TEXT PRIMARY KEY,
                    state TEXT,
                    updated_at TIMESTAMP
                )
            """)

            # Checkpoints table
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

            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP,
                    metadata TEXT,
                    FOREIGN KEY (task_id) REFERENCES states(task_id)
                )
            """)

            # Context table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context (
                    task_id TEXT,
                    key TEXT,
                    value TEXT,
                    timestamp TIMESTAMP,
                    PRIMARY KEY (task_id, key),
                    FOREIGN KEY (task_id) REFERENCES states(task_id)
                )
            """)

            # Task relationships table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_relationships (
                    task_id TEXT,
                    related_task_id TEXT,
                    relevance_score FLOAT,
                    timestamp TIMESTAMP,
                    PRIMARY KEY (task_id, related_task_id),
                    FOREIGN KEY (task_id) REFERENCES states(task_id),
                    FOREIGN KEY (related_task_id) REFERENCES states(task_id)
                )
            """)

            conn.commit()

    def save_state(self, task_id: str, state: Dict[str, Any]) -> None:
        """Save task state to database"""
        with sqlite3.connect(self.db_path) as conn:
            # Save main state
            state_json = json.dumps(state, cls=DateTimeJSONEncoder)
            conn.execute(
                """
                INSERT OR REPLACE INTO states (task_id, state, updated_at)
                VALUES (?, ?, ?)
            """,
                (task_id, state_json, datetime.utcnow().isoformat()),
            )

            # Save messages
            if "messages" in state:
                for msg in state["messages"]:
                    conn.execute(
                        """
                        INSERT INTO messages
                        (task_id, role, content, timestamp, metadata)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            task_id,
                            msg["role"],
                            msg["content"],
                            msg["timestamp"].isoformat(),
                            json.dumps(msg.get("metadata", {})),
                        ),
                    )

            # Save context
            if "context" in state:
                for key, value in state["context"].items():
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO context
                        (task_id, key, value, timestamp)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            task_id,
                            key,
                            json.dumps(value, cls=DateTimeJSONEncoder),
                            datetime.utcnow().isoformat(),
                        ),
                    )

            conn.commit()

    def load_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task state from database"""
        with sqlite3.connect(self.db_path) as conn:
            # Load main state
            cursor = conn.execute("SELECT state FROM states WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            if not row:
                return None

            state = json.loads(row[0], object_hook=json_decoder_hook)

            # Load messages
            cursor = conn.execute(
                """
                SELECT role, content, timestamp, metadata
                FROM messages
                WHERE task_id = ?
                ORDER BY timestamp
            """,
                (task_id,),
            )

            state["messages"] = [
                {
                    "role": row[0],
                    "content": row[1],
                    "timestamp": datetime.fromisoformat(row[2]),
                    "metadata": json.loads(row[3]),
                }
                for row in cursor.fetchall()
            ]

            # Load context
            cursor = conn.execute(
                """
                SELECT key, value
                FROM context
                WHERE task_id = ?
            """,
                (task_id,),
            )

            state["context"] = {row[0]: json.loads(row[1], object_hook=json_decoder_hook) for row in cursor.fetchall()}

            return state

    def get_related_tasks(self, task_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get related tasks by checking context and relationships"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT related_task_id, relevance_score
                FROM task_relationships
                WHERE task_id = ?
                ORDER BY relevance_score DESC
                LIMIT ?
            """,
                (task_id, limit),
            )

            related = []
            for row in cursor.fetchall():
                related_id = row[0]
                # Load basic task info
                task_cursor = conn.execute(
                    """
                    SELECT state
                    FROM states
                    WHERE task_id = ?
                """,
                    (related_id,),
                )

                state_row = task_cursor.fetchone()
                if state_row:
                    state = json.loads(state_row[0])
                    related.append(
                        {
                            "task_id": related_id,
                            "task": state.get("task", ""),
                            "similarity": row[1],
                            "completed": state.get("is_complete", False),
                        }
                    )

            return related

    def search_task_history(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """Search task history with relevance scores"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT DISTINCT m.task_id, COUNT(*) as relevance
                FROM messages m
                WHERE m.content LIKE ?
                GROUP BY m.task_id
                ORDER BY relevance DESC
                LIMIT ?
            """,
                (f"%{query}%", limit),
            )

            return [(row[0], row[1]) for row in cursor.fetchall()]
