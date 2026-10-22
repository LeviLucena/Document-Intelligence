import io
import json

import numpy as np
from botocore.response import StreamingBody
from botocore.stub import Stubber
import boto3

from app.ingest import chunk_pages, extract_pages
from app.providers.base import Passage
from app.providers.bedrock import BedrockProvider
from app.providers.local import LocalProvider
from app.rag import estimate_cost
from app.store import VectorStore


def test_extract_pages_keeps_page_numbers(pdf_bytes):
    pages = extract_pages(pdf_bytes)
    assert len(pages) == 2
    assert "America Latina" in pages[0] and "segundo trimestre" in pages[1]


def test_chunking_respects_size_and_page():
    text = "palavra " * 400
    chunks = chunk_pages(["", text], size=300, overlap=50)
    assert chunks and all(c.page == 2 for c in chunks)
    assert all(len(c.text) <= 300 for c in chunks)


def test_store_search_and_remove(tmp_path):
    p = LocalProvider()
    store = VectorStore(tmp_path)
    texts = ["gatos dormem no sofa", "receita do trimestre cresceu muito"]
    store.add("a.pdf", [(1, texts[0]), (2, texts[1])], p.embed(texts))
    hit = store.search(p.embed(["receita trimestre"])[0], 1)[0][1]
    assert hit["page"] == 2
    assert VectorStore(tmp_path).documents()[0]["chunks"] == 2  # persistiu
    assert store.remove("a.pdf") and not store.items


def test_local_answer_cites_sources():
    gen = LocalProvider().generate(
        "qual a receita?", [Passage(1, "a.pdf", 2, "A receita projetada e de dois milhoes de reais.")]
    )
    assert "[1]" in gen.text


def test_bedrock_converse_and_embed_with_stubber():
    client = boto3.client("bedrock-runtime", region_name="us-east-1",
                          aws_access_key_id="x", aws_secret_access_key="x")
    stub = Stubber(client)
    stub.add_response(
        "converse",
        {
            "output": {"message": {"role": "assistant", "content": [{"text": "Resposta [1]"}]}},
            "stopReason": "end_turn",
            "usage": {"inputTokens": 120, "outputTokens": 30, "totalTokens": 150},
            "metrics": {"latencyMs": 10},
        },
    )
    raw = json.dumps({"embedding": [0.6, 0.8]}).encode()
    stub.add_response(
        "invoke_model",
        {"body": StreamingBody(io.BytesIO(raw), len(raw)), "contentType": "application/json"},
    )
    with stub:
        prov = BedrockProvider(client)
        gen = prov.generate("pergunta?", [Passage(1, "a.pdf", 1, "trecho")])
        vec = prov.embed(["texto"])
    assert (gen.text, gen.input_tokens, gen.output_tokens) == ("Resposta [1]", 120, 30)
    assert np.allclose(vec, [[0.6, 0.8]])


def test_estimate_cost():
    assert estimate_cost(1000, 1000) > 0
