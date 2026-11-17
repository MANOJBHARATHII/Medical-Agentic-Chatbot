import argparse
import hashlib
from pathlib import Path

import pymupdf

from app.knowledge import embed, ensure_index


def chunks(text, size=1100, overlap=180):
    text = ' '.join(text.split())
    step = size - overlap
    if step <= 0:
        step = size
    return [text[i:i + size] for i in range(0, len(text), step) if len(text[i:i + size]) > 80]


def find_default_pdf():
    candidates = [
        Path('data', 'Medical_book (1).pdf'),
        Path('data', 'medical_book.pdf'),
        Path('data', 'medical-book.pdf'),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate

    data_dir = Path('data')
    if data_dir.exists():
        pdfs = sorted(data_dir.glob('*.pdf'))
        if pdfs:
            return pdfs[0]

    return candidates[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', default=None)
    args = parser.parse_args()

    pdf = Path(args.pdf) if args.pdf else find_default_pdf()
    if not pdf.exists():
        raise SystemExit(f'PDF not found: {pdf}')

    try:
        index = ensure_index()
        with pymupdf.open(pdf) as doc:
            batch = []
            for page_number, page in enumerate(doc, start=1):
                for part, content in enumerate(chunks(page.get_text()), start=1):
                    key = hashlib.sha256(f'{pdf.name}:{page_number}:{part}:{content}'.encode()).hexdigest()
                    batch.append((key, content, {'page': page_number, 'text': content, 'file': pdf.name}))
                    if len(batch) >= 50:
                        vectors = embed([b[1] for b in batch])
                        index.upsert(vectors=[{'id': b[0], 'values': v, 'metadata': b[2]} for b, v in zip(batch, vectors)])
                        batch = []
                if page_number % 50 == 0:
                    print(f'Indexed pages: {page_number}/{len(doc)}', flush=True)
            if batch:
                vectors = embed([b[1] for b in batch])
                index.upsert(vectors=[{'id': b[0], 'values': v, 'metadata': b[2]} for b, v in zip(batch, vectors)])

        print('Ingestion complete')
    except RuntimeError as exc:
        print(f'Ingestion skipped: {exc}')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
