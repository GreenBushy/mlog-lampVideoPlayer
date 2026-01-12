# mlog-lampVideoPlayer
Scheme and tool to play video in mlog-lampVideoPlayer


---
    The first thing you need to do is launch Mindustry.
    Go to Mods.
    Navigate to the mods directory.
    Navigate to the Mindustry directory.
 
  <img width="219" height="42" alt="image" src="https://github.com/user-attachments/assets/2261fbbe-79ba-42a2-b6f0-393006914a04" />
    
    Create a directory named mlog-data-blocks there.
    
  <img width="634" height="332" alt="image" src="https://github.com/user-attachments/assets/4be5bbb2-19c5-4f98-8359-02a889291bf9" />
    
    Create a file named video-blocks-path.txt inside it.
    
   <img width="634" height="183" alt="image" src="https://github.com/user-attachments/assets/9764cfb2-4c94-4004-a478-af2fdc4f8688" />


---

**Download the Python script**  
*(After installing Python, ffmpeg, ffprobe, and other script dependencies)*  
Create a dedicated directory for script (recommended but optional).  

Run it like this:  
```bash
python path/to/script/video-to-mlog-video-blocks.py path/to/video.any_extension --regen-id
```  

The script will automatically generate a config file containing various settings,  
such as output frame dimensions and FPS.  

After the script completes successfully:  
1. Navigate to the `out` directory (created by the script)  
2. Copy the **full path** to this `out` directory  
3. Paste it into `video-blocks-path.txt` (located in `Mindustry/mlog-data-blocks/`)  

You only need to insert the path to the out directory once.
This step is not required for subsequent generations.
---
---

**After generation, launch Mindustry**  
→ Load any **sandbox map** (*recommended: create a dedicated test map as a precaution*)  
→ Copy the **JavaScript script from build-video-blocks.js**
→ Open the **Mindustry console** (press <kbd>F8</kbd> by default)  
→ Paste the script and press <kbd>Enter</kbd>  

**Then paste this command into the console and execute:**  
```javascript
buildVideoBlocks(100, 50, 70, Vars.player.unit())
```  

### Parameter Explanation:
- `100, 50` = **Starting coordinates (x, y)** where logic processor placement begins  
- `70` = **X-axis boundary limit**  
  - If placement exceeds this X-coordinate:  
    → Y-coordinate increments by **+1**  
    → X resets to the **starting X value** (`100`)  

---


**After executing the command, logic processors will be placed.**  
They store video data **as strings**:  
→ 1 string = 1 data channel  
→ 3 channels = 1 video frame  
→ 1 logic processor holds **up to 16 frames** at **52×39 resolution** (player display size)
→ Each corlor channel contains **92 data values** (i mean symbols more then 92 in single string. We are support 92 symbols)

You may then:  
- Copy them as a **logic schematic**, *or*  
- Leave them directly on the map.  

This creates a **"video file"** for the player.  

---


**Next, you need the video player:**  
1. Download the **schematic file** from the repository  
2. Place/build it on your map  

**Follow the in-game instructions provided by the schematic itself.**  

Once complete, you can watch the video on the player’s display built from **Illuminators**.  



