"""Provider Amazon Bedrock: embeddings Titan v2 + geração via Converse API."""
import json

import boto3
import numpy as np

from ..config import settings
from .base import SYSTEM_PROMPT, Generation, Passage, build_user_prompt


class BedrockProvider:
    name = "bedrock"

    def __init__(self, client=None):
        # `client` injetável para testes (botocore Stubber).
        self.client = client or boto3.client("bedrock-runtime", region_name=settings.aws_region)

    def embed(self, texts: list[str]) -> np.ndarray:
        vecs = []
        for t in texts:
            resp = self.client.invoke_model(
                modelId=settings.bedrock_embed_model_id,
                body=json.dumps({"inputText": t, "normalize": True}),
                contentType="application/json",
                accept="application/json",
            )
            vecs.append(json.loads(resp["body"].read())["embedding"])
        return np.array(vecs, dtype=np.float32)

    def generate(self, question: str, passages: list[Passage]) -> Generation:
        resp = self.client.converse(
            modelId=settings.bedrock_model_id,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[{"role": "user", "content": [{"text": build_user_prompt(question, passages)}]}],
            inferenceConfig={"maxTokens": 700, "temperature": 0.1},
        )
        text = resp["output"]["message"]["content"][0]["text"]
        usage = resp.get("usage", {})
        return Generation(text, usage.get("inputTokens", 0), usage.get("outputTokens", 0))
