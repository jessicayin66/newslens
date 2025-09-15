# ai_summary.py
import nltk
nltk.download("punkt_tab")

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer

def summarize_article(text: str, sentence_count: int = 3) -> str:
    """
    Returns an extractive summary of the article.
    sentence_count: number of sentences to include in summary
    """
    if not text or len(text.strip()) == 0:
        return ""
    
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LexRankSummarizer()
    summary_sentences = summarizer(parser.document, sentence_count)
    
    # Combine sentences into a single string
    return " ".join(str(sentence) for sentence in summary_sentences)
