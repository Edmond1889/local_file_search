import sqlite3
import os
import hashlib
import time
import numpy as np
import faiss
from typing import List, Dict, Any, Optional

class ImageMetadataDBManager:
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}

    def __init__(self, db_path: str = "image_metadata.db", embedding_dim: int = 512):
        self.db_path = db_path
        self.embedding_dim = embedding_dim
        self._init_db()
        self.index = faiss.IndexFlatIP(self.embedding_dim)

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_metadata (
                faiss_id INTEGER PRIMARY KEY,
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

    def _get_next_faiss_id(self) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(faiss_id) FROM image_metadata")
        row = cursor.fetchone()
        conn.close()
        return 0 if row[0] is None else row[0] + 1

    def _normalize_vector(self, vec: np.ndarray) -> np.ndarray:
        vec = vec.astype(np.float32).reshape(1, -1)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def insert_image_metadata(self, file_path: str, embedding: np.ndarray) -> Optional[int]:
        file_path = os.path.abspath(file_path)
        file_name = os.path.basename(file_path)
        _, ext = os.path.splitext(file_name)
        ext = ext.lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            print(f"[경고] 지원하지 않는 확장자: {file_path}")
            return None

        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        file_hash = ""
        if os.path.exists(file_path):
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                hasher.update(f.read(4096))
            file_hash = hasher.hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            next_id = self._get_next_faiss_id()
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("""
                INSERT INTO image_metadata (faiss_id, file_path, file_name, file_extension, file_size, file_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (next_id, file_path, file_name, ext, file_size, file_hash, current_time))
            
            conn.commit()

            norm_embedding = self._normalize_vector(embedding)
            self.index.add(norm_embedding)
            return next_id

        except sqlite3.IntegrityError:
            print(f"[중복] 이미 존재함: {file_path}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def search_top_k(self, query_embedding: np.ndarray, top_k: int = 3) -> List[Dict[str, Any]]:
        if self.index.ntotal == 0:
            return []

        norm_query = self._normalize_vector(query_embedding)
        distances, indices = self.index.search(norm_query, top_k)

        results = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for idx, score in zip(indices[0], distances[0]):
            if idx == -1:
                continue

            faiss_id = int(idx)
            cursor.execute("""
                SELECT faiss_id, file_path, file_name, file_extension, file_size, created_at
                FROM image_metadata
                WHERE faiss_id = ?
            """, (faiss_id,))
            
            row = cursor.fetchone()
            if row:
                results.append({
                    "faiss_id": row[0],
                    "file_path": row[1],
                    "file_name": row[2],
                    "file_extension": row[3],
                    "file_size_bytes": row[4],
                    "created_at": row[5],
                    "similarity_score": round(float(score), 4)
                })

        conn.close()
        return results

    def save_index_and_db(self, index_file_path: str = "faiss_index.bin"):
        faiss.write_index(self.index, index_file_path)
        print(f"FAISS 인덱스 저장 완료 -> {index_file_path}")
        print(f"SQLite DB 저장 완료 -> {self.db_path}")

    def load_index_and_db(self, index_file_path: str = "faiss_index.bin"):
        if os.path.exists(index_file_path):
            self.index = faiss.read_index(index_file_path)
            print(f"FAISS 인덱스 로드 완료 (총 {self.index.ntotal}개 항목)")
        if os.path.exists(self.db_path):
            print(f"SQLite DB 로드 완료")


if __name__ == "__main__":
    TEST_DB_NAME = "dummy_image_metadata.db"
    TEST_INDEX_NAME = "dummy_faiss_index.bin"
    EMBEDDING_DIM = 512

    db_manager = ImageMetadataDBManager(db_path=TEST_DB_NAME, embedding_dim=EMBEDDING_DIM)

    # 테스트용 가상 임베딩
    dummy_images = [
        {"path": "./sample_folder/매실_사진1.jpg", "vector": np.random.rand(EMBEDDING_DIM)},
        {"path": "./sample_folder/매실_나무.png", "vector": np.random.rand(EMBEDDING_DIM)},
        {"path": "./sample_folder/고양이.jpeg", "vector": np.random.rand(EMBEDDING_DIM)},
        {"path": "./sample_folder/풍경_매실밭.webp", "vector": np.random.rand(EMBEDDING_DIM)},
    ]

    print("\n--- 1. 메타데이터 및 벡터 저장 ---")
    for item in dummy_images:
        db_manager.insert_image_metadata(file_path=item["path"], embedding=item["vector"])

    print("\n--- 2. FAISS 및 DB 저장 ---")
    db_manager.save_index_and_db(index_file_path=TEST_INDEX_NAME)

    print("\n--- 3. 저장된 데이터 불러오기 ---")
    new_db_manager = ImageMetadataDBManager(db_path=TEST_DB_NAME, embedding_dim=EMBEDDING_DIM)
    new_db_manager.load_index_and_db(index_file_path=TEST_INDEX_NAME)

    print("\n--- 4. 코사인 유사도 기반 검색 (Top 3) ---")
    dummy_query_vector = dummy_images[0]["vector"] + np.random.normal(0, 0.1, EMBEDDING_DIM)
    search_results = new_db_manager.search_top_k(query_embedding=dummy_query_vector, top_k=3)

    for rank, res in enumerate(search_results, 1):
        print(f"Rank {rank}: {res['file_name']} | 유사도: {res['similarity_score']} | 경로: {res['file_path']}")
