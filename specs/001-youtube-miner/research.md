# Research: YouTube Miner

## Technology Choices

### 1. YouTube Download: yt-dlp

**Chosen**: yt-dlp  
**Alternatives Considered**: pytube, youtube-dl

| Library | Pros | Cons |
|---------|------|------|
| **yt-dlp** ✅ | Active maintenance, fast, reliable, caption support | Larger dependency |
| pytube | Lightweight | Less maintained, frequent breakage |
| youtube-dl | Original project | Slower updates, yt-dlp is a better fork |

**Decision**: yt-dlp is the industry standard, actively maintained, and supports caption extraction.

---

### 2. Audio Conversion: pydub + FFmpeg

**Chosen**: pydub with FFmpeg backend  
**Alternatives Considered**: librosa, soundfile, scipy.io.wavfile

| Library | Pros | Cons |
|---------|------|------|
| **pydub** ✅ | Simple API, format conversion, FFmpeg backend | Requires FFmpeg |
| librosa | Scientific audio processing | Overkill for conversion |
| soundfile | Fast WAV handling | Limited format support |

**Decision**: pydub provides the simplest API for format conversion with FFmpeg handling all codecs.

---

### 3. Voice Activity Detection: Silero VAD

**Chosen**: Silero VAD  
**Alternatives Considered**: pyannote, webrtcvad, py-webrtcvad

| Library | Pros | Cons |
|---------|------|------|
| **Silero VAD** ✅ | Accurate, fast, easy to use, PyTorch | Requires torch |
| pyannote.audio | Very accurate, speaker diarization | Heavy, complex setup, HuggingFace token |
| webrtcvad | Lightweight, fast | Lower accuracy, no Python 3.10+ wheels |

**Decision**: Silero VAD offers the best balance of accuracy and ease of use. It's pre-trained and works out of the box.

**Note**: The problem statement mentions pyannote, but Silero VAD is simpler to set up and sufficient for speech/non-speech detection. If speaker diarization is needed later, pyannote can be added.

---

### 4. Transcription Models

#### 4.1 Whisper-Tiny (OpenAI)

**Use Case**: Quick transcription, low resource usage  
**Model Size**: ~39M parameters  
**Memory**: ~1GB  
**Speed**: Fastest Whisper variant

```python
import whisper
model = whisper.load_model("tiny")
result = model.transcribe("audio.wav")
```

#### 4.2 Faster-Whisper

**Use Case**: Production transcription, optimized performance  
**Technology**: CTranslate2 optimization of Whisper  
**Speed**: 4x faster than original Whisper  
**Memory**: Reduced through quantization

```python
from faster_whisper import WhisperModel
model = WhisperModel("tiny", compute_type="int8")
segments, info = model.transcribe("audio.wav")
```

#### 4.3 ai4bharat/indic-seamless

**Use Case**: Multilingual transcription (especially Indic languages)  
**Technology**: SeamlessM4T based  
**Languages**: 100+ languages including Hindi, Tamil, etc.

```python
from transformers import AutoProcessor, SeamlessM4TModel
processor = AutoProcessor.from_pretrained("ai4bharat/indic-seamless")
model = SeamlessM4TModel.from_pretrained("ai4bharat/indic-seamless")
```

#### 4.4 Whisper-Large (Optional)

**Use Case**: Highest accuracy when resources allow  
**Model Size**: ~1.5B parameters  
**Memory**: ~6GB  
**Trade-off**: Much slower but most accurate

#### Model Comparison Matrix

| Model | Speed | Accuracy | Memory | Languages |
|-------|-------|----------|--------|-----------|
| Whisper-Tiny | ⭐⭐⭐⭐⭐ | ⭐⭐ | ~1GB | 99 |
| Faster-Whisper | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ~2GB | 99 |
| Indic-Seamless | ⭐⭐⭐ | ⭐⭐⭐⭐ | ~4GB | 100+ |
| Whisper-Large | ⭐⭐ | ⭐⭐⭐⭐⭐ | ~6GB | 99 |

---

### 5. N-gram Deduplication

**Approach**: Custom implementation using sliding window

**Algorithm**:
1. Tokenize text into words
2. Create n-grams (n=2,3,4)
3. Detect consecutive repeated n-grams
4. Remove duplicates while preserving meaning

```python
def remove_repeated_ngrams(text: str, n: int = 3) -> str:
    words = text.split()
    result = []
    i = 0
    while i < len(words):
        ngram = tuple(words[i:i+n])
        if i + n < len(words) and ngram == tuple(words[i+n:i+2*n]):
            # Skip duplicate
            i += n
        else:
            result.append(words[i])
            i += 1
    return ' '.join(result)
```

---

### 6. Comparison Metrics

#### 6.1 Word Error Rate (WER)

**Library**: jiwer  
**Formula**: (S + D + I) / N  
- S = Substitutions
- D = Deletions
- I = Insertions
- N = Total words in reference

```python
from jiwer import wer
error_rate = wer(reference, hypothesis)
```

#### 6.2 Character Error Rate (CER)

**Library**: jiwer  
**Formula**: Same as WER but at character level

```python
from jiwer import cer
error_rate = cer(reference, hypothesis)
```

#### 6.3 Semantic Similarity

**Library**: sentence-transformers  
**Model**: all-MiniLM-L6-v2 (fast, good quality)

```python
from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer('all-MiniLM-L6-v2')
emb1 = model.encode(text1)
emb2 = model.encode(text2)
similarity = util.cos_sim(emb1, emb2).item()
```

#### 6.4 Hybrid Metrics (SeMaScore)

Combines error rate with semantic similarity:
```
hybrid_score = (1 - wer) * alpha + semantic_similarity * (1 - alpha)
```
Where alpha is a tunable parameter (default: 0.5)

---

### 7. Text Normalization

**Operations** (applied to both transcripts before comparison):
1. Convert to lowercase
2. Remove punctuation
3. Collapse multiple spaces
4. Optionally: number to words conversion
5. Optionally: expand contractions

```python
import re
import string

def normalize(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'\s+', ' ', text).strip()
    return text
```

---

## Performance Considerations

### Memory Management for Long Videos

1. **Streaming download**: Don't load entire audio into memory
2. **Chunk processing**: Process one chunk at a time
3. **Model unloading**: Unload models when switching
4. **Temporary files**: Clean up intermediate files

### Processing Time Estimates (1-hour audio)

| Stage | Time (approx) |
|-------|---------------|
| Download | 2-5 min |
| Conversion | 1-2 min |
| VAD Chunking | 2-3 min |
| Transcription (Faster-Whisper) | 10-15 min |
| Caption Extraction | <1 min |
| Comparison | 2-3 min |
| **Total** | **~20-30 min** |

---

## Alternative Approaches Considered

### Real-time Processing
**Rejected**: Not required by spec, adds complexity

### GPU Acceleration
**Optional**: Faster-Whisper supports CUDA if available, but CPU works fine

### Distributed Processing
**Rejected**: Overkill for single-user CLI tool

---

## References

- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [Silero VAD](https://github.com/snakers4/silero-vad)
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper)
- [jiwer for WER/CER](https://github.com/jitsi/jiwer)
- [Sentence-Transformers](https://www.sbert.net/)
- [ai4bharat Seamless](https://huggingface.co/ai4bharat/indic-seamless)

