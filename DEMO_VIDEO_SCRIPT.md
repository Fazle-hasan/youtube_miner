# 🎬 YouTube Miner - Demo Video Script

**Estimated Duration:** 4-5 minutes  
**Format:** Screen recording with voiceover  
**Tools Needed:** OBS/Screen recorder, Web browser, Terminal

---

## 📍 Scene 1: Introduction (0:00 - 0:30)

### Visual
- Show the GitHub repo / README with architecture diagram
- Zoom into the project title

### Narration
> "Hey everyone! Today I'm excited to demo **YouTube Miner** - an end-to-end pipeline that compares YouTube auto-captions against AI-generated transcriptions.
>
> This tool helps answer a critical question: **How accurate are YouTube's auto-captions?** And which transcription model gives us the best results?
>
> Let's dive in and see it in action!"

---

## 📍 Scene 2: Problem Statement (0:30 - 0:50)

### Visual
- Show a YouTube video with auto-captions enabled
- Highlight some caption errors (if visible)

### Narration
> "YouTube's auto-captions are great, but they're not perfect. They can miss words, mishear phrases, or struggle with accents and multilingual content.
>
> YouTube Miner solves this by downloading any video, transcribing it using state-of-the-art AI models, and then comparing the results using multiple accuracy metrics."

---

## 📍 Scene 3: Architecture Overview (0:50 - 1:20)

### Visual
- Show the architecture diagram (`docs/architecture.png`)
- Point to each stage as you explain

### Narration
> "Here's how the pipeline works:
>
> 1. **Stage 1-2:** We download the audio and captions from YouTube
> 2. **Stage 3:** Audio is converted to 16kHz mono WAV format
> 3. **Stage 4:** Voice Activity Detection segments the audio into chunks
> 4. **Stage 5:** Each chunk is transcribed using your chosen AI model
> 5. **Stage 6:** Captions are aligned with our chunks for comparison
> 6. **Stage 7:** We compute accuracy metrics - WER, CER, Semantic Similarity, and our Hybrid Score
> 7. **Stage 8:** Everything is compiled into a detailed JSON report
> 8. **Stage 9:** You can download results as JSON, SRT subtitles, or plain text"

---

## 📍 Scene 4: Available Models (1:20 - 1:50)

### Visual
- Show the model comparison table from README
- Highlight each model briefly

### Narration
> "YouTube Miner supports **four transcription models**:
>
> - **Whisper Tiny** - Super fast, around 70% accuracy. Great for quick tests.
> - **Faster Whisper** - Our recommended default! 80-90% accuracy with optimized speed.
> - **Indic Seamless** - Perfect for Hindi and Indian languages. Built by AI4Bharat.
> - **Whisper Large** - Highest accuracy but requires a powerful GPU.
>
> Each model has its strengths depending on your use case."

---

## 📍 Scene 5: Live Demo - Web Interface (1:50 - 3:30)

### Visual
- Open browser to `http://localhost:5050`
- Show the clean web interface

### Narration & Actions

#### Step 1: Starting the Server
```bash
youtube-miner web start
```
> "Let me start the web server. You can also use the CLI, but the web interface gives us a beautiful visual experience."

#### Step 2: Enter a YouTube URL
> "I'll paste a YouTube video URL here. Let's try this English video first."

*Paste URL, select `faster-whisper` model, select language*

#### Step 3: Processing
> "Watch the real-time progress! The pipeline shows each stage:
> - Downloading audio... done!
> - Extracting captions from YouTube...
> - Converting audio format...
> - Running Voice Activity Detection to find speech segments...
> - Now transcribing each chunk with Faster Whisper..."

*Show progress bar and status updates*

#### Step 4: Results
> "And we're done! Look at these results:
> - **Hybrid Score: 83%** - That's excellent!
> - **WER: 20%** - Only 1 in 5 words differs
> - **Semantic Similarity: 87%** - The meaning is well preserved
>
> We can expand each chunk to see the side-by-side comparison between YouTube captions and our AI transcription."

*Click to expand a few chunks, show the comparison*

#### Step 5: Download Options
> "And here's a great feature - you can download the results in three formats:
> - **JSON Report** - Full detailed analysis
> - **SRT File** - Standard subtitle format for video editors
> - **TXT File** - Plain text transcription"

*Click each download button*

---

## 📍 Scene 6: Hindi/Multilingual Demo (3:30 - 4:10)

### Visual
- Process a Hindi video using `indic-seamless`

### Narration
> "Now let's try something interesting - a **Hindi video** with the Indic Seamless model.
>
> This model is specifically trained for Indian languages by AI4Bharat."

*Paste Hindi video URL, select `indic-seamless`, select Hindi*

> "Notice the processing takes a bit longer - that's because this is a larger multilingual model.
>
> And here are the results! The WER is higher at around 54% - but that's expected because Hindi has code-switching between Hindi and English.
>
> **But look at the Semantic Similarity - 89%!** The meaning is excellently preserved even when exact words differ."

---

## 📍 Scene 7: CLI Demo (Quick) (4:10 - 4:30)

### Visual
- Terminal window

### Narration
> "For automation and scripting, there's also a powerful CLI:"

```bash
# Process a video
youtube-miner process "https://youtube.com/watch?v=VIDEO_ID" --model faster-whisper

# Just download audio
youtube-miner download "VIDEO_URL" --output ./audio

# Generate comparison report
youtube-miner compare ./output/folder
```

> "You can integrate this into your own pipelines!"

---

## 📍 Scene 8: Results Summary (4:30 - 4:50)

### Visual
- Show the comparison table from README
- Show sample JSON report structure

### Narration
> "Here's what we found from our tests:
>
> | Content | Model | Hybrid Score |
> |---------|-------|--------------|
> | English Long (63 min) | faster-whisper | **83%** |
> | English Short (5 min) | faster-whisper | **89%** |
> | Hindi Long (67 min) | indic-seamless | **68%** |
>
> The takeaway? **Faster Whisper is excellent for English**, and **Indic Seamless handles Hindi well** while preserving semantic meaning."

---

## 📍 Scene 9: Conclusion (4:50 - 5:00)

### Visual
- GitHub repo page
- Star button highlight 😉

### Narration
> "That's YouTube Miner! An end-to-end solution for analyzing caption accuracy with multiple AI models.
>
> The code is fully documented with architecture diagrams, technical design docs, and comprehensive tests.
>
> Thanks for watching! If you found this useful, check out the GitHub repo. Happy transcribing!"

---

## 🎬 Video Tips

### Recording Checklist
- [ ] Clean browser (no personal bookmarks visible)
- [ ] Terminal with clear, readable font (14-16pt)
- [ ] Close unnecessary applications
- [ ] Stable internet connection for YouTube downloads
- [ ] Pre-load the web interface at localhost:5050

### Editing Tips
- Add subtle zoom effects when highlighting features
- Use text overlays for key statistics
- Add background music (low volume, royalty-free)
- Include chapter markers for YouTube

### Recommended Tools
- **Screen Recording:** OBS Studio (free), Loom, or QuickTime (Mac)
- **Editing:** DaVinci Resolve (free), iMovie, or Premiere
- **Thumbnail:** Canva with the architecture diagram

---

## 📝 Key Points to Emphasize

1. ✅ **End-to-end pipeline** - Download → Process → Compare → Report
2. ✅ **Multiple AI models** - Choose based on language and speed needs
3. ✅ **Real metrics** - WER, CER, Semantic Similarity, Hybrid Score
4. ✅ **Beautiful web UI** - Real-time progress, expandable results
5. ✅ **Download options** - JSON, SRT, TXT formats
6. ✅ **Multilingual support** - English, Hindi, and more
7. ✅ **Well documented** - Architecture diagrams, technical docs, tests

