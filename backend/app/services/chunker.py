from typing import List, Dict


def chunk_document(
    text: str,
    document_id: int,
    filename: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Dict]:
    chunks = []
    words = text.split()
    current_chunk = []
    current_length = 0
    chunk_num = 1
    page_num = 1

    for word in words:
        if word.startswith("---") and "Página" in word:
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_number": chunk_num,
                    "page_number": page_num,
                    "text": chunk_text,
                })
                chunk_num += 1
                current_chunk = []
                current_length = 0
            try:
                page_num = int(word.split()[-2])
            except (ValueError, IndexError):
                pass
            continue

        if word.startswith("---") and "Diapositiva" in word:
            if current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_number": chunk_num,
                    "page_number": page_num,
                    "text": chunk_text,
                })
                chunk_num += 1
                current_chunk = []
                current_length = 0
            try:
                page_num = int(word.split()[-2])
            except (ValueError, IndexError):
                pass
            continue

        current_chunk.append(word)
        current_length += len(word) + 1

        if current_length >= chunk_size:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "document_id": document_id,
                "filename": filename,
                "chunk_number": chunk_num,
                "page_number": page_num,
                "text": chunk_text,
            })
            overlap_words = current_chunk[-chunk_overlap:] if chunk_overlap > 0 else []
            current_chunk = overlap_words
            current_length = sum(len(w) + 1 for w in overlap_words)
            chunk_num += 1

    if current_chunk:
        chunk_text = " ".join(current_chunk)
        chunks.append({
            "document_id": document_id,
            "filename": filename,
            "chunk_number": chunk_num,
            "page_number": page_num,
            "text": chunk_text,
        })

    return chunks
