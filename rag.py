# rag.py
# Lightweight TF-IDF retriever for Nyay Buddy (no heavy models)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class Retriever:
    """Simple TF-IDF retriever + rule-based multilingual answer generator."""

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
        """Generate a concise multilingual answer using retrieved contexts."""
        if not contexts:
            return "No relevant information found. PLEASE CONSULT THE LAWYER."

        # Pick the most relevant snippet
        top = contexts[0]
        law_ref = top.get("law_reference", "Relevant Law")
        snippet = top.get("text", "No details available.")

        # Language-specific templates
        if lang == "hi":
            answer = (
                f"संक्षिप्त उत्तर ({law_ref} के आधार पर):\n"
                f"{snippet}\n\nकदम:\n"
                "1. सभी साक्ष्य और दस्तावेज़ एकत्र करें।\n"
                "2. उचित विभाग या हेल्पलाइन से संपर्क करें।\n"
                "3. आवश्यक हो तो वकील या निःशुल्क कानूनी सहायता लें।"
            )
        elif lang == "pa":
            answer = (
                f"ਛੋਟਾ ਜਵਾਬ ({law_ref} ਅਧਾਰ ਤੇ):\n"
                f"{snippet}\n\nਕਦਮ:\n"
                "1. ਸਾਰੇ ਸਬੂਤ ਤੇ ਦਸਤਾਵੇਜ਼ ਇਕੱਠੇ ਕਰੋ।\n"
                "2. ਸੰਬੰਧਿਤ ਵਿਭਾਗ ਜਾਂ ਹੈਲਪਲਾਈਨ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।\n"
                "3. ਜਰੂਰਤ ਪੈਣ ਤੇ ਵਕੀਲ ਜਾਂ ਕਾਨੂੰਨੀ ਸਹਾਇਤਾ ਲਵੋ।"
            )
        else:  # English default
            answer = (
                f"Short answer (based on {law_ref}):\n"
                f"{snippet}\n\nSteps:\n"
                "1. Collect all documents and proof.\n"
                "2. Contact the relevant authority or helpline.\n"
                "3. If unresolved, consult a lawyer or legal aid centre."
            )
        return answer
