import os
import sqlite3
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
import faiss

@dataclass
class FileInfo:
    file_path: str
    file_name: str
    file_extension: str
    file_size: int
    file_hash: str
    created_at: str
    file_id: Optional[int] = None

class Repository:
    def __init__(self, db_path: str = "image_metadata.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_metadata (
                file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_extension TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def save(self, file_info: FileInfo) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO image_metadata (file_path, file_name, file_extension, file_size, file_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            file_info.file_path,
            file_info.file_name,
            file_info.file_extension,
            file_info.file_size,
            file_info.file_hash,
            file_info.created_at
        ))
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return file_id

    def find_by_id(self, file_id: int) -> Optional[FileInfo]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_id, file_path, file_name, file_extension, file_size, file_hash, created_at
            FROM image_metadata
            WHERE file_id = ?
        """, (file_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return FileInfo(
                file_id=row[0],
                file_path=row[1],
                file_name=row[2],
                file_extension=row[3],
                file_size=row[4],
                file_hash=row[5],
                created_at=row[6]
            )
        return None

class VectorIndex:
    def __init__(self, embedding_dim: int = 512):
        self.embedding_dim = embedding_dim
        self.base_index = faiss.IndexFlatIP(self.embedding_dim)
        self.index = faiss.IndexIDMap2(self.base_index)

    def _normalize_vector(self, vec: np.ndarray) -> np.ndarray:
        vec = vec.astype(np.float32).reshape(1, -1)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def add(self, file_id: int, vector: np.ndarray) -> None:
        norm_vec = self._normalize_vector(vector)
        ids = np.array([file_id], dtype=np.int64)
        self.index.add_with_ids(norm_vec, ids)

    def search(self, query_vector: np.ndarray, top_k: int = 3) -> List[Tuple[int, float]]:
        if self.index.ntotal == 0:
            return []

        norm_query = self._normalize_vector(query_vector)
        distances, indices = self.index.search(norm_query, top_k)

        results = []
        for idx, score in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            results.append((int(idx), float(round(score, 4))))

        return results

    def save_index(self, index_file_path: str = "faiss_index.bin"):
        faiss.write_index(self.index, index_file_path)

    def load_index(self, index_file_path: str = "faiss_index.bin"):
        if os.path.exists(index_file_path):
            self.index = faiss.read_index(index_file_path)
