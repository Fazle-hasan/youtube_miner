Hi Gladiators,
 
You have made it so far…and its time to prove your mettle! This is an individual round, time to get your IC caps on. You have been provided access to Cursor for this challenge.
 
Rules:
1. Project Completion:
Participants are expected to complete their projects within the given time frame. The final submission by 5th Jan’26   should be fully functional and meet all outlined objectives.
 
2. Documentation:
A detailed technical design document is required, including:
A clear project overview including the track selected
System architecture diagrams (e.g., Flow Diagrams)
Setup and deployment instructions
Code explanations and assumptions
 
3. Demo Video:
Participants must provide a YouTube link to a demo video showcasing the project. The demo should highlight key features and demonstrate the user experience.
 
4. Submission Platform:
All code should be uploaded to GitHub. Participants will be provided with a specific repository and guidelines for version control.
 
5. Evaluation Criteria:
Projects will be evaluated based on:
Innovation and Creativity: Originality and uniqueness of the solution.
Technical Complexity: Depth and sophistication of AI models and algorithms.
Code Quality: Cleanliness, readability, and maintainability of the code.
Testing and Reliability: Coverage and effectiveness of unit tests.
Documentation: Clarity and completeness of the technical design document.
Demo Quality: Effectiveness and clarity of the demo video.
All projects must include comprehensive unit test cases to ensure robustness and reliability of the code.
If Hosted - Do share the link for the same.
 
If you miss any of the above, you are eliminated!
 
Your Mission if you chose to accept it!
 
* Task Name: "The YouTube Miner" (Data Pipeline)
 
The Task: Write a Python script that takes a YouTube URL (e.g., a specific podcast episode), and does three things automatically:
Downloads the audio.
Uses VAD (Voice Activity Detection) to chop it into clean 30-second chunks (removing silence/music).
Transcribes one chunk using a distinct Open Source model (like Whisper-Tiny) and compares it to the YouTube auto-captions.
The Constraint: No paid APIs. Use open-source libraries ( yt-dlp, pyannote, faster-whisper).


This is my idea of diagrams you can change if you want but build a system that passes this round

Youtube link
    |||
Download audio 
    |||
Convert to .wav form to provide to model
    |||
use silero vad to chop it into clean 30 seconds chunks (removing silence/music)
    |||
Transcribes one by one chunk using distinct opensource model (give me options for these models and you can search and also provide some new and good performing models)
1 - Whisper-Tiny
2 - whisper based
3 - ai4bharat/indic-seamless
4 - Faster-Whisper (Whisper-Tiny optimized)
etc if you get any better model
    |||
remove repetative words using ngrams
    |||
compares it to the youtube auto-captions with different techniques (use these techniques Word Error Rate (WER), Character Error Rate (CER), Compute semantic similarity (e.g., embedding cosine) at chunk level.) and always Normalization before comparison of the both 

Practical workflow for your use case

Normalize both transcripts identically.
Compute WER and CER between your model’s chunk and YouTube’s chunk.
Compute semantic similarity (e.g., embedding cosine) chunk level.
