# 🎬 YouTube Miner - Demo Video Script

**Estimated Duration:** 4-5 minutes  
**Format:** Screen recording with voiceover 
**Tools Needed:** OBS/Loom/QuickTime, Web browser, Terminal

---

## 📍 Scene 1: Introduction (0:00 - 0:25)

### Visual
- Show README with title and architecture diagram
- Quick zoom on "100% Open Source • No Paid APIs"

### Narration
> "Hey everyone! Today I'm demoing **YouTube Miner** - an end-to-end pipeline that compares YouTube's auto-captions against AI-generated transcriptions.
>
<!-- > This tool answers a critical question: **How accurate are YouTube's captions?** And which AI model gives us the best results? -->
>
> Let's see it in action!"

---

## 📍 Scene 2: Architecture (0:25 - 0:55)

### Visual
- Show `docs/architecture.png` full screen
- Point to each stage as you explain

### Narration
> "Here's the 9-stage pipeline:
>
> **Stages 1-2:** Download audio from YouTube using yt-dlp
>
> **Stage 3:** Convert to 16kHz WAV format
>
> **Stage 4:** Voice Activity Detection splits audio into ~30 second speech chunks
>
> **Stages 5-6:** Transcribe with AI models AND extract YouTube captions in parallel
>
> **Stages 7-8:** Compare using WER, CER, Semantic Similarity, and our Hybrid Score
>
> **Stage 9:** Download results as JSON, SRT subtitles, or plain text"

---

## 📍 Scene 3: Quick Installation (0:55 - 1:15)

### Visual
- Terminal window

### Narration & Actions
> "Installation is simple. First, make sure you have FFmpeg and Python 3.10+."

```bash
# Install FFmpeg (macOS)
brew install ffmpeg

# Clone and setup
git clone <repository-url>
cd youtube_miner
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

> "That's it! Now let's start the web interface."

---

## 📍 Scene 4: Live Demo - Web Interface (1:15 - 3:00)

### Visual
- Terminal → Browser at `http://127.0.0.1:5000`

### Narration & Actions

#### Step 1: Start Server
```bash
youtube-miner web start
```
> "One command starts the web server."

*Open browser to `http://127.0.0.1:5000`*

> "Here's the clean web interface - paste any YouTube URL."

#### Step 2: Process a Video
> "Let me paste this NVIDIA CEO interview - it's a 63-minute video. I'll select **faster-whisper** as our model and **English** as the language."

*Paste: `https://www.youtube.com/watch?v=7ARBJQn6QkM`*
*Select: `faster-whisper`, `English`*
*Click Process*

#### Step 3: Watch Progress
> "Watch the real-time progress:
> - Downloading audio... ✓
> - Converting to WAV... ✓  
> - Running Voice Activity Detection... ✓
> - Transcribing 96 chunks with Faster Whisper...
>
> This takes about 5 minutes for an hour-long video."

*Show progress bar updating*

#### Step 4: View Results
> "Done! Let's look at the results:
>
> - **Hybrid Score: 83.4%** - That's excellent quality!
> - **WER: 19.7%** - Great word accuracy
> - **Semantic Similarity: 86.6%** - Meaning is well preserved
>
> I can expand any chunk to see side-by-side comparison."

*Click to expand Chunk 0, show the text comparison*

> "Look - the transcript and caption are almost identical! Only minor differences."

#### Step 5: Download Options
> "Now the best part - I can download results in three formats:"

*Click each download button*

> "**JSON Report** - Full analysis with all metrics
> **SRT File** - Timed subtitles for video editors  
> **TXT File** - Plain text transcription"

---

## 📍 Scene 5: Hindi Demo (3:00 - 3:40)

### Visual
- New video processing with `indic-seamless`

### Narration
> "Now let's try something different - a **Hindi video** using the **Indic Seamless** model.
>
> This model is built by AI4Bharat specifically for Indian languages."

*Paste Hindi video URL*
*Select: `indic-seamless`, `Hindi`*

> "Processing takes longer for this larger multilingual model...
>
> Here are the results:
> - **Hybrid Score: 67.8%** - Acceptable for multilingual content
> - **WER: 53.9%** - Higher because of code-switching between Hindi and English
> - **But Semantic Similarity: 89.4%!** The meaning is excellently preserved.
>
> That's the power of our Hybrid Score - it captures real-world quality even when exact words differ."

---

## 📍 Scene 6: CLI Demo (3:40 - 4:00)

### Visual
- Terminal window

### Narration
> "For automation, there's a powerful CLI:"

```bash
# Full pipeline
youtube-miner run "URL" --model faster-whisper --output ./results

# Individual commands
youtube-miner download "URL" -o ./audio
youtube-miner transcribe chunk.wav -m faster-whisper
youtube-miner compare "reference" "hypothesis"
```

> "You can integrate this into your own workflows!"

---

## 📍 Scene 7: Model Comparison (4:00 - 4:30)

### Visual
- Show the model comparison table from README

### Narration
> "Quick recap of our 4 supported models:
>
> | Model | Speed | Best For |
> |-------|-------|----------|
> | **whisper-tiny** | ⚡⚡⚡⚡⚡ | Quick tests |
> | **faster-whisper** | ⚡⚡⚡⚡⚡ | **Production default** |
> | **indic-seamless** | ⚡⚡⚡ | Hindi & Indian languages |
> | **whisper-large** | ⚡ | Maximum accuracy |
>
> From our real-world tests:"

*Show results summary table*

> "| Content | Model | Hybrid Score |
> |---------|-------|--------------|
> | English Long | faster-whisper | **83.4%** |
> | English Short | faster-whisper | **89.4%** |
> | Hindi Long | indic-seamless | **67.8%** |
>
> **Recommendation:** Use faster-whisper for English, indic-seamless for Hindi!"

---

## 📍 Scene 8: Conclusion (4:30 - 5:00)

### Visual
- README page with technical documentation link
- Architecture diagram

### Narration
> "That's YouTube Miner!
>
> ✅ **End-to-end pipeline** - Download → Transcribe → Compare → Report
> ✅ **4 AI models** - From fast to accurate to multilingual
> ✅ **Beautiful web UI** - Real-time progress, downloadable results
> ✅ **Comprehensive metrics** - WER, CER, Semantic Similarity, Hybrid Score
>
> Check out the Technical Design Document for deep architectural details and 100+ unit tests.
>
> Thanks for watching! Happy transcribing!"

---

## 🎬 Recording Checklist

### Before Recording
- [ ] FFmpeg installed and working
- [ ] Virtual environment activated
- [ ] Clean browser (no personal bookmarks)
- [ ] Terminal with readable font (14-16pt)
- [ ] Close unnecessary applications
- [ ] Stable internet connection
- [ ] Test videos ready to paste:
  - English: `https://www.youtube.com/watch?v=7ARBJQn6QkM`
  - Hindi: `https://www.youtube.com/watch?v=oHry5RRI4KU`

### Server Commands
```bash
# Start
cd youtube_miner
source venv/bin/activate
youtube-miner web start

# Stop when done
youtube-miner web stop
```

---

## 🎨 Editing Tips

1. **Zoom effects** - Highlight UI elements when explaining
2. **Text overlays** - Show key metrics as callouts
3. **Chapter markers** - Add for YouTube navigation:
   - 0:00 Introduction
   - 0:25 Architecture
   - 0:55 Installation
   - 1:15 Web Demo
   - 3:00 Hindi Demo
   - 3:40 CLI
   - 4:00 Model Comparison
   - 4:30 Conclusion
4. **Background music** - Low volume, royalty-free
5. **Speed up** - 2x during long processing waits

---

## 📝 Key Points to Emphasize

| # | Point | When to Show |
|---|-------|--------------|
| 1 | **100% Open Source, No Paid APIs** | Introduction |
| 2 | **9-Stage Pipeline** | Architecture diagram |
| 3 | **Real-time Progress** | During processing |
| 4 | **Hybrid Score balances WER + Semantic** | Results view |
| 5 | **3 Download Formats** | After processing |
| 6 | **Multilingual Support** | Hindi demo |
| 7 | **Technical Documentation** | Conclusion |

---

## 🛠️ Recommended Tools

| Purpose | Tool | Cost |
|---------|------|------|
| Screen Recording | OBS Studio | Free |
| Quick Recording | Loom | Free tier |
| Mac Recording | QuickTime | Built-in |
| Video Editing | DaVinci Resolve | Free |
| Thumbnail | Canva | Free |