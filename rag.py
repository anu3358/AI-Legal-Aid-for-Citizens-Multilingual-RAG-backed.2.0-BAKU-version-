# rag.py
# Lightweight TF-IDF retriever with optional small LLM for answer generation

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from pathlib import Path
import numpy as np
import json

# Try to load Flan-T5 (optional)
try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
    _tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
    _llm = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")
except Exception:
    _tokenizer = None
    _llm = None


class Retriever:
    """Simple TF-IDF retriever + optional LLM answer generator."""

    def __init__(self, kb_list):
        self.kb = kb_list
        texts = [item.get("text") or item.get("question") or "" for item in kb_list]
        self.vectorizer = TfidfVectorizer(max_features=6000, ngram_range=(1, 2))
        self.tfidf = self.vectorizer.fit_transform(texts)
        self.texts = texts

    # ----------------------------------------------------------------------
    def retrieve(self, query, top_k=5):
        """Retrieve top_k relevant passages from knowledge base."""
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.tfidf)[0]
        idxs = np.argsort(-sims)[:top_k]
        results = []
        for i in idxs:
            item = dict(self.kb[i])
            item["score"] = float(sims[i])
            results.append(item)
        return results

    # ----------------------------------------------------------------------
    def generate_answer(self, query, contexts, lang="en"):
        """Generate short multilingual answer using contexts."""
        ctx_text = "\n\n".join(
            [f"[{c.get('law_reference', '')}] {c.get('text', '')}" for c in contexts]
        )

        prompt = (
            f"Answer the question in language code {lang}. "
            f"Use the contexts below and cite the relevant law. "
            f"Give a short direct answer followed by 3 crisp, non-repeating steps.\n\n"
            f"CONTEXTS:\n{ctx_text}\n\nQUESTION: {query}\n\nAnswer:"
        )

        # If LLM is available, use it
        if _llm is not None and _tokenizer is not None:
            inputs = _tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024)
            outputs = _llm.generate(**inputs, max_new_tokens=220)
            answer = _tokenizer.decode(outputs[0], skip_special_tokens=True)
            return answer

        # Fallback lightweight answer
        refs = [c.get("law_reference") for c in contexts if c.get("law_reference")]
        primary_ref = refs[0] if refs else "N/A"

        answer_en = f"Short answer (based on {primary_ref}):\n"
        if contexts and contexts[0].get("text"):
            snippet = contexts[0]["text"][:350]
            answer_en += snippet + "\n\nSteps:\n1. Collect documents and proof.\n2. Contact relevant authority or helpline.\n3. If unresolved, approach a lawyer or legal aid."
        else:
            answer_en += "No relevant data found. PLEASE CONSULT THE LAWYER."

        return answer_en
