# Praat script for extract f0 data for a simple file
# Loop thorugh the rime tier, and modify the boundary to where
form
    word textgridName
    integer f0min 0
    interger f0max 0
    comment "0 means default"
endform

rhyme_tier = 7
f0_tier = 8
# Read the files
sounddir$ = "/Users/kechun/Documents/0_PhD_working_folder/Cantonese/workflow/sound_original"
textgriddir$ = "/Users/kechun/Documents/0_PhD_working_folder/Cantonese/workflow/textgrid_checked"
textgrdifile$ = textgriddir$ + "/" + textgridName$
soundName$ = textgridName$ - "_checked.TextGrid" + ".wav"
soundfile$ = sounddir$ + "/" + soundName$
if fileReadable(textgrdifile$)
    textgridID = Read from file: textgrdifile$
    soundID = Read from file: soundfile$
else
    exitScript: textgridfile$, " or ", soundfile$, " does not exist."
endif 

# Check the tiers number; Insert f0 tier
tiers = Get number of tiers 
if tiers = 7
    Insert interval tier: f0_tier, "f0"
    modify = 0
elsif tiers =8
    # This indicates the f0 boundary has alreayd been set, and now we only want to extract
    modify = 1
else
    existScript: "Check the number of tiers "
endif

# Calculate the optimized f0 range
if f0min ==0 and f0max ==0
    select 'soundID'
    To Pitch: 0, 50, 800
    pitchID = selected("Pitch")
    min1 = Get minimum: 0, 0, "Hertz", "None"
    max1 = Get maximum: 0, 0, "Hertz", "None"
    q1 = Get quantile: 0, 0, 0.25, "Hertz"
    q1 = floor(q1)
    q3 = Get quantile: 0, 0, 0.75, "Hertz"
    q3 = ceiling(q3)
    ## The optimal value is calculated based on Hirst (2009)
    defaultf0floor = floor((0.7 * q1)/ 10) * 10
    defaultf0ceiling = ceiling((2.5 * q3)/ 10) * 10
    #f0ceiling2 = ceiling((1.5 * q3)/ 10) * 10
    select 'pitchID'
    Remove
else 
    defaultf0floor = f0min
    defaultf0ceiling = f0max
endif
select 'soundID'
To Pitch: 0, defaultf0floor, defaultf0ceiling
pitchID = selected("Pitch")
## By default, this is the object we will draw values from

# Calculate intensity based on this default setting
select 'soundID'
Scale peak... 0.99
To Intensity... defaultf0ceiling 0.01 1
intensityID = selected("Intensity")

# If modify = 0, then we first deliminit the range that contain f0 values
if modify = 0
    select 'textgridID'
    numberOfIntervals = Get number of intervals: rhyme_tier
    for interval from 1 to numberOfIntervals
        select 'textgridID'
        label$ = Get label of interval: rhyme_tier, interval
        if label$ <> ""
            interval_start = Get start time of interval: rhyme_tier, interval
            interval_end = Get end time of interval: rhyme_tier, interval
            @initialise_f0start: pitchID, interval_start
            @initialise_f0end: pitchID, interval_end
            ### If this is valid duration, then we can add the boundary markers
            if start < end
                select 'textgridID'
                nocheck Insert boundary: f0_tier, start
                nocheck Insert boundary: f0_tier, end
            ### Otherwise, open the textgrid and manually specify
            else 
                beginPause("Adjust f0 extraction period in textgrid")
                    editor TextGrid 'textgridName_current$'
                        # Zoom into the position editor
                        Select: start, end
                        Zoom: start, end
                        start = Get start of selection
                        end = Get end of selection
                    endeditor
                clicked = endPause: "Continue",1
                nocheck Insert boundary: f0_tier, start
                nocheck Insert boundary: f0_tier, end
            endif
        endif
    endfor
# Otherwise, we directly get f0 and duration information  
else
# Loop over the boundary at 'f0' tier
select 'textgridID'
numberOfIntervals = Get number of intervals: f0_tier
### Get 

### Get rhyme duration - later from tier 8
    
    interval_mid = (interval_start + interval_end)/2
    rhyme_dur = interval_end-interval_start
endfor

procedure initialise_f0start: pitchobject, start
    select 'pitchobject'
    endoffile = Get end time
    f0start = Get value at time... start "Hertz" linear
    if f0start = undefined
        repeat
            start += 0.01
            f0start = Get value at time... start "Hertz" linear
            # if close to the end of file, then stop and allow cursor to move to that point
            checkstart = start + 0.01
        until f0start > 0 or checkstart > endoffile
    endif
endproc
        
procedure initialise_f0end: pitchobject, end
    select 'pitchobject'
        endoffile = Get end time
    f0end = Get value at time... end "Hertz" linear
    if f0end = undefined
        repeat
            end += -0.01
            f0end = Get value at time... end "Hertz" linear
            # if close to the end of file, then stop and allow cursor to move to that point
            checkstart = start + 0.01
        until f0end > 0 or checkstart > endoffile
    endif
endproc
################## Later on##############
## Add trimming algorhithm
## Octave kill
