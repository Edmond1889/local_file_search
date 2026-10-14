"""팀원 인코더의 함수 이름과 출력 배열을 서비스 규격에 맞춘다."""
import numpy as np


def as_vector(value, dimension):
    # 잘못된 차원/NaN은 DB에 파일 정보를 저장하기 전에 발견한다.
    vector = np.asarray(value, dtype=np.float32)
    if vector.shape != (dimension,) or not np.isfinite(vector).all():
        raise ValueError(f"인코더는 유한한 숫자 {dimension}개의 1차원 벡터를 반환해야 합니다.")
    if np.linalg.norm(vector) == 0:
        raise ValueError("인코더가 영벡터를 반환했습니다.")
    return np.ascontiguousarray(vector)


class ImageEncoderAdapter:
    def __init__(self, encoder, dimension=512):
        self.encoder, self.dimension = encoder, dimension

    def encode(self, image):
        # 현재 팀원 규격은 PIL 입력이다. 경로를 다시 읽지 않는다.
        return as_vector(self.encoder.encode(image), self.dimension)


class TextEncoderAdapter:
    def __init__(self, encoder, dimension=512):
        self.encoder, self.dimension = encoder, dimension

    def encode(self, query):
        # 서비스 encode() → 팀원 encode_text(). 문장을 그대로 전달한다.
        return as_vector(self.encoder.encode_text(query), self.dimension)
