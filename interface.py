# Scanner 담당
scanner.scan(folder_path) -> list[FileInfo]


# Image Embedding 담당
image_encoder.encode(file_path) -> np.ndarray


# Text Embedding 담당
text_encoder.encode(query) -> np.ndarray


# FAISS 담당
vector_index.add(vector) -> int

vector_index.search(
    vector,
    top_k
) -> tuple[list[float], list[int]]


# DB 담당
repository.save(file_info) -> int

repository.find_by_path(path) -> FileInfo | None

repository.find_by_vector_id(vector_id) -> FileInfo | None