
from pathlib import Path

import numpy as np
import open_clip
import torch
from PIL import Image, ImageOps


class ImageEncoder:
    """로컬 이미지를 OpenCLIP으로 512차원 벡터로 변환하는 클래스"""

    # 지원하는 이미지 파일 확장자
    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

    def __init__(
        self,
        model_name="ViT-B-32",
        pretrained="laion2b_s34b_b79k",
        device=None,
        batch_size=8
    ):
        # Batch 크기 유효성 검사
        if batch_size < 1:
            raise ValueError("batch_size는 1 이상이어야 합니다.")

        # GPU 사용이 가능하면 CUDA, 아니면 CPU 사용
        self.device = torch.device(
            device or ("cuda" if torch.cuda.is_available() else "cpu")
        )

        self.model_name = model_name
        self.pretrained = pretrained
        self.batch_size = batch_size

        # OpenCLIP 모델과 이미지 전처리 함수 불러오기
        self.model, _, self.preprocess = (
            open_clip.create_model_and_transforms(
                model_name,
                pretrained=pretrained,
                device=self.device
            )
        )

        # 학습이 아닌 추론 모드로 설정
        self.model.eval()

        # 모델의 이미지 임베딩 출력 차원 확인
        self.embedding_dim = self.model.visual.output_dim

        if self.embedding_dim != 512:
            raise ValueError(
                f"512차원 모델이 필요합니다. "
                f"현재 모델: {self.embedding_dim}차원"
            )

    def _load_image(self, image_path):
        """이미지를 불러와 OpenCLIP 입력 Tensor로 전처리"""

        path = Path(image_path)

        # 파일 존재 여부 및 확장자 확인
        if not path.is_file():
            raise FileNotFoundError(
                f"파일을 찾을 수 없습니다: {path}"
            )

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"지원하지 않는 이미지 형식: {path.suffix}"
            )

        try:
            with Image.open(path) as image:
                # EXIF 회전 정보 적용 후 RGB 3채널로 변환
                image = ImageOps.exif_transpose(image)
                image = image.convert("RGB")

                # Resize, Crop, Tensor 변환, 픽셀 정규화
                return self.preprocess(image)

        except (OSError, ValueError) as error:
            raise ValueError(
                f"이미지를 처리할 수 없습니다: {path}"
            ) from error

    def encode(self, image_path):
        """
        단일 이미지 임베딩 생성

        반환: NumPy 배열 (512,), float32
        """

        # 이미지 로딩 및 전처리: [3, 224, 224]
        image_tensor = self._load_image(image_path)

        # Batch 차원 추가: [1, 3, 224, 224]
        image_tensor = image_tensor.unsqueeze(0).to(self.device)

        # Vision Encoder로 512차원 임베딩 생성 및 L2 정규화
        with torch.inference_mode():
            embedding = self.model.encode_image(
                image_tensor,
                normalize=True
            )

        # Tensor를 NumPy float32 배열로 변환: [512]
        vector = (
            embedding.squeeze(0)
            .cpu()
            .numpy()
            .astype(np.float32)
        )

        return vector

    def encode_batch(self, image_paths):
        """
        여러 이미지를 Batch 단위로 임베딩

        반환:
            vectors: (N, 512) NumPy 배열
            valid_paths: 정상 처리된 이미지 경로
            errors: 처리 실패한 이미지 정보
        """

        image_paths = list(image_paths)

        vectors = []
        valid_paths = []
        errors = []

        # 전체 이미지를 batch_size 단위로 나누어 처리
        for start in range(0, len(image_paths), self.batch_size):

            batch_paths = image_paths[
                start:start + self.batch_size
            ]

            batch_tensors = []
            batch_valid_paths = []

            # 각 이미지 로딩 및 전처리
            for path in batch_paths:
                try:
                    tensor = self._load_image(path)
                    batch_tensors.append(tensor)
                    batch_valid_paths.append(str(path))

                except (OSError, ValueError) as error:
                    # 오류가 발생한 파일은 기록하고 나머지 파일 처리
                    errors.append({
                        "path": str(path),
                        "error": str(error)
                    })

            if not batch_tensors:
                continue

            # 여러 이미지 Tensor를 하나로 결합: [B, 3, 224, 224]
            batch = torch.stack(batch_tensors).to(self.device)

            # Batch 단위 임베딩 생성: [B, 512]
            with torch.inference_mode():
                embeddings = self.model.encode_image(
                    batch,
                    normalize=True
                )

            # NumPy float32 배열로 변환
            batch_vectors = (
                embeddings.cpu()
                .numpy()
                .astype(np.float32)
            )

            vectors.append(batch_vectors)
            valid_paths.extend(batch_valid_paths)

        # Batch별 임베딩을 하나의 배열로 결합
        if vectors:
            result = np.concatenate(vectors, axis=0)
        else:
            result = np.empty((0, 512), dtype=np.float32)

        return result, valid_paths, errors

# if __name__ == "__main__":
#     encoder = ImageEncoder()

#     # 실제 이미지 경로로 변경
#     image_path = r"C:\Users\hyuns\OneDrive\Desktop\CapStone\IMG\Test.jpg"

#     vector = encoder.encode(image_path)

#     print("임베딩 크기:", vector.shape)
#     print("데이터 타입:", vector.dtype)
#     print("L2 정규화:", np.linalg.norm(vector))
#     print("벡터 일부:", vector[:10])