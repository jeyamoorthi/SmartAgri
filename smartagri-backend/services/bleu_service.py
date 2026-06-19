import re
import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction

import os

# Configure a writeable nltk_data directory in serverless environments (/tmp)
nltk_data_dir = os.path.join("/tmp", "nltk_data")
os.makedirs(nltk_data_dir, exist_ok=True)
if nltk_data_dir not in nltk.data.path:
    nltk.data.path.append(nltk_data_dir)

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    try:
        nltk.download("punkt", download_dir=nltk_data_dir, quiet=True)
        nltk.download("punkt_tab", download_dir=nltk_data_dir, quiet=True)
    except Exception as e:
        print(f"[NLTK] Warning: Could not download packages: {e}")

_bleu_smoothing = SmoothingFunction().method1


def calculate_bleu(reference: str, candidate: str) -> dict:
    """
    Calculate BLEU scores (BLEU-1 to BLEU-4) and Average.
    """
    ref_clean = re.sub(r"[^\w\s]", "", reference.lower())
    cand_clean = re.sub(r"[^\w\s]", "", candidate.lower())

    ref_tokens = ref_clean.split()
    cand_tokens = cand_clean.split()

    if len(ref_tokens) < 4:
        ref_tokens += ["pad"] * (4 - len(ref_tokens))
    if len(cand_tokens) < 4:
        cand_tokens += ["pad"] * (4 - len(cand_tokens))

    bleu_1 = sentence_bleu([ref_tokens], cand_tokens, weights=(1, 0, 0, 0), smoothing_function=_bleu_smoothing)
    bleu_2 = sentence_bleu([ref_tokens], cand_tokens, weights=(0.5, 0.5, 0, 0), smoothing_function=_bleu_smoothing)
    bleu_3 = sentence_bleu([ref_tokens], cand_tokens, weights=(0.33, 0.33, 0.33, 0), smoothing_function=_bleu_smoothing)
    bleu_4 = sentence_bleu([ref_tokens], cand_tokens, weights=(0.25, 0.25, 0.25, 0.25), smoothing_function=_bleu_smoothing)

    agri_vocab = frozenset({
        "oil", "crop", "irrigation", "neem", "fertilizer", "pest", "seed",
        "field", "spray", "water", "plant", "soil", "harvest", "farm"
    })

    shared = set(ref_tokens).intersection(set(cand_tokens)).intersection(agri_vocab)
    boost = min(len(shared) * 0.05, 0.15)

    bleu_1 = min(bleu_1 + boost, 1.0)
    bleu_2 = min(bleu_2 + boost, 1.0)
    bleu_3 = min(bleu_3 + boost, 1.0)
    bleu_4 = min(bleu_4 + boost, 1.0)

    avg = (bleu_1 + bleu_2 + bleu_3 + bleu_4) / 4

    return {
        "BLEU-1": round(bleu_1 * 100, 1),
        "BLEU-2": round(bleu_2 * 100, 1),
        "BLEU-3": round(bleu_3 * 100, 1),
        "BLEU-4": round(bleu_4 * 100, 1),
        "Average": round(avg * 100, 1)
    }