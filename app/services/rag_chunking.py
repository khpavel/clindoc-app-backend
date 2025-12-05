from typing import List
import re


def chunk_text(
    text: str,
    max_chunk_size: int = 1000,
    min_chunk_size: int = 300,
) -> List[str]:
    """
    Split input text into reasonably sized chunks for simple RAG.

    Strategy:
    - Split by double newlines into paragraphs.
    - Accumulate paragraphs until max_chunk_size is reached.
    - Ensure that chunks are at least min_chunk_size where possible.
    """
    # Split text by double newlines into paragraphs
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    
    for paragraph in paragraphs:
        # Strip whitespace from paragraph
        paragraph = paragraph.strip()
        
        # Skip empty paragraphs
        if not paragraph:
            continue
        
        # Check if adding this paragraph would exceed max_chunk_size
        # Calculate the size of current chunk with this new paragraph
        test_chunk = current_chunk + [paragraph]
        test_chunk_text = '\n\n'.join(test_chunk)
        
        if current_chunk and len(test_chunk_text) > max_chunk_size:
            # Current chunk is full, finalize it
            chunk_text = '\n\n'.join(current_chunk)
            chunk_text = _clean_whitespace(chunk_text)
            if chunk_text:
                chunks.append(chunk_text)
            
            # Start new chunk with this paragraph
            current_chunk = [paragraph]
        else:
            # Add paragraph to current chunk
            current_chunk.append(paragraph)
    
    # Add the last chunk if it exists
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        chunk_text = _clean_whitespace(chunk_text)
        if chunk_text:
            chunks.append(chunk_text)
    
    # Post-process to try to meet min_chunk_size where possible
    # Merge small chunks with previous chunks if they're below min_chunk_size
    if min_chunk_size > 0:
        merged_chunks = []
        for chunk in chunks:
            if merged_chunks and len(chunk) < min_chunk_size:
                # Try to merge with previous chunk if total size doesn't exceed max_chunk_size
                prev_chunk = merged_chunks[-1]
                combined_size = len(prev_chunk) + len(chunk) + 2
                if combined_size <= max_chunk_size:
                    merged_chunks[-1] = _clean_whitespace(prev_chunk + '\n\n' + chunk)
                else:
                    merged_chunks.append(chunk)
            else:
                merged_chunks.append(chunk)
        chunks = merged_chunks
    
    return chunks


def _clean_whitespace(text: str) -> str:
    """
    Strip excessive whitespace from text.
    - Replace multiple consecutive newlines with double newline
    - Strip leading/trailing whitespace
    - Replace multiple spaces with single space (but preserve newlines)
    """
    # Replace multiple newlines (3+) with double newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace multiple spaces with single space (but not newlines)
    lines = text.split('\n')
    cleaned_lines = [re.sub(r' +', ' ', line.strip()) for line in lines]
    
    # Join lines and strip overall whitespace
    cleaned_text = '\n'.join(cleaned_lines).strip()
    
    return cleaned_text

