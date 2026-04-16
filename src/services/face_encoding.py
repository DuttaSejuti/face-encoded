from typing import List
import httpx
from src.app.core.config import FACE_ENCODING_SERVICE_URL

class FaceEncodingServiceError(Exception):
    pass


class FaceEncodingClient:
    def __init__(self, base_url: str = FACE_ENCODING_SERVICE_URL):
        self.base_url = base_url.rstrip("/")

    async def get_encodings(
        self,
        image_content: bytes,
        filename: str,
        content_type: str,
    ) -> List[List[float]]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            files = {"file": (filename, image_content, content_type)}

            try:
                response = await client.post(f"{self.base_url}/v1/selfie", files=files)
            except httpx.HTTPError as exc:
                raise FaceEncodingServiceError("Face encoding service is unavailable.") from exc

        if response.status_code != 200:
            raise FaceEncodingServiceError("Face encoding service returned an error.")

        data = response.json()

        if isinstance(data, list):
            return data

        encodings = data.get("encodings")
        if isinstance(encodings, list):
            return encodings

        raise FaceEncodingServiceError("Face encoding service returned an unexpected response.")


def get_face_encoding_client() -> FaceEncodingClient:
    return FaceEncodingClient()
