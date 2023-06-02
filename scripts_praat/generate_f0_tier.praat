# Praat script for modifying rhyme tiers (generate a new tier and delete the old) so that f0 values are non-empty
# The current script works for a single file, but is called upon in 'Wordbook_ICPhS.ipynb'.

form
    word textgridName S3dia1A1_checked
    sentence textgriddir /Users/kechun/Documents/0_PhD_working_folder/Cantonese/workflow/textgrid_checked/
    sentence sounddir	/Users/kechun/Documents/0_PhD_working_folder/Cantonese/workflow/sound_original/
	integer f0min 0
    integer f0max 0
    comment 0 means default
endform

rhyme_tier = 7
f0_tier = 8

# Read the files
textgridfile$ = textgriddir$ + "/" + textgridName$ + ".TextGrid"
soundName$ = textgridName$ - "_checked" + ".wav"
soundfile$ = sounddir$ + "/" + soundName$
if fileReadable(textgridfile$)
    textgridID = Read from file: textgridfile$
    soundID = Read from file: soundfile$
else
    exitScript: textgridfile$, " or ", soundfile$, " does not exist."
endif

# Check the tiers number; Insert f0 tier
select 'textgridID'
tiers = Get number of tiers
if tiers = 7
    Insert interval tier: f0_tier, "f0"
else
    existScript: "Check the number of tiers "
endif

select 'soundID'
To Pitch: 0, f0min, f0max
pitchID = selected("Pitch")
## By default, this is the object we will draw values from

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
            # Add interval label 
            current_interval = Get low interval at time: f0_tier, end
            Set interval text: f0_tier, current_interval, label$
        ### Otherwise, open the textgrid and manually specify
        else 
            # I want the script to be run in the background only, therefore not usin 'beginPause' function
            select 'textgridID'
            nocheck Insert boundary: f0_tier, interval_start
            nocheck Insert boundary: f0_tier, interval_end
            # Add interval label
            current_interval = Get low interval at time: f0_tier, interval_end
            Set interval text: f0_tier, current_interval, label$
        endif
    endif
endfor

select 'textgridID'
Remove tier: rhyme_tier
Save as text file: sounddir$ - "sound_original" + "textgrid_pitch_batch/" + textgridName$ + ".TextGrid"
# Remove unnecessary files
select 'pitchID'
Remove

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


