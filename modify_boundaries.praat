# Facilitate the double check of the boundaries
# It opens the "_checked.TextGrid" and extract tier 4-7 to display with sound
# It allow you to free modify, and when finished, saved with the P2FA tiers, and save the new file to folder
# By Katrina Li 21/2/2023

# Future implementation: Allow only open selected
# target$ = "A3"

# Open the files 
################################
dir$ = "/Users/kechun/Documents/0_PhD_working_folder/Changsha/workflow/"
sounddir$ = dir$ + "sound_original"
textgriddir$ = dir$ + "textgrid_pitch_batch/modify"
#textgriddir$ = dir$ + "textgrid_checked/processed"
################################

# Loop thorugh all the files in a folder
textgridstrings = Create Strings as file list: "list", textgriddir$ + "/*.TextGrid"
if textgridstrings
  	numberOfFiles = Get number of strings
	n = 0
  	writeInfoLine: "There are ", numberOfFiles, " Files."
    for ifile to numberOfFiles
        selectObject: textgridstrings
    	textgridName$ = Get string: ifile
		textgridID = Read from file: textgriddir$ + "/" + textgridName$
        textgridName_current$ = selected$("TextGrid")
		appendInfoLine: "Current file is ", textgridName$
        ## Read only the last few textgrid, to avoid bias, but still save to the original ones when finish
        # Set up a copy textgrid, keep tiers 1,2,3,4
        select 'textgridID'
        textgridID_old = Copy: textgridName_current$ + "_old"
        Remove tier: 7
        Remove tier: 6
        Remove tier: 5
        # Set up a copy textgrid, Only keep tiers 5,6,7
        select 'textgridID'
        textgridID_check = Copy: textgridName_current$ 
        # When remove a series of tiers, it's important to do this from the bottom to top (for the tier number will change!)
        Remove tier: 4
        Remove tier: 3
        Remove tier: 2
        Remove tier: 1


        # Combine with sound and open
		soundName$ = textgridName$ - "_checked.TextGrid" + ".wav"
    	soundID = Read from file: sounddir$ + "/" + soundName$
        select 'textgridID_check'
		plus 'soundID'
		View & Edit
        
        # Get the default f0 values, which can influence display anyway
        @find_default_f0values
        f0floor = defaultf0floor
        f0ceiling = defaultf0ceiling
        # Adjust the window setting
        editor TextGrid 'textgridName_current$'
		    Pitch settings: f0floor, f0ceiling, "Hertz", "autocorrelation", "automatic"
	    endeditor
        #Begin pause: allow the user to freely change
        # Begin pause
		repeat
			beginPause("Check boundaries")
            real("Newfloor", f0floor)
            real("Newceiling", f0ceiling)
            comment("File 'textgridName_current$'(file number 'ifile' of 'numberOfFiles')")
            clicked = endPause("Skip","Draw","Save",1)
            if clicked = 1
                appendInfoLine: textgridName$, " skipped!"
            # Generate f0 figure if there are missing values
            elif clicked = 2
                editor TextGrid 'textgridName_current$'
                    current_start = Get start of selection
                    current_end = Get end of selection
                endeditor
                select 'soundID'
                To Pitch: 0, f0floor, f0ceiling
                pitchID = selected("Pitch")
				# Draw contour with ten points
                @draw_pitch_contour: pitchID, current_start, current_end, f0floor, f0ceiling, 10
            elif clicked = 3
                select 'textgridID_old'
                plus 'textgridID_check'
                newtextgridID = Merge
                Rename: textgridName_current$
                Save as text file: textgriddir$ + "/" + textgridName$
            endif
        until clicked = 1 or clicked = 3

        # Keep the new files, but delete the rest
        select 'textgridID'
        plus 'textgridID_old'
        plus 'textgridID_check'
        Remove
    endfor
endif


procedure find_default_f0values
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
endproc

procedure draw_pitch_contour: pitchobject, draw_start, draw_end, draw_min, draw_max, number_of_points
	Erase all
	# Draw1: the orignial pitch contour
	select 'pitchobject'
	Draw: draw_start, draw_end, draw_min, draw_max,1 

	# Plot normalised values on the real values
	Create TableOfReal...  "table" 10 2
	tableID = selected("TableOfReal")
	duration = draw_end - draw_start
	# extract normalised f0 - also write to tableOfReal
	f0s# = zero#(number_of_points)
	for x from 1 to number_of_points
		normtime = draw_start + duration*(x-1)/(number_of_points-1)
		select 'pitchobject'
		f0s#[x] = Get value at time... normtime "Hertz" linear
		select 'tableID'
		Set value: x, 1, normtime
		Set value: x, 2, f0s#[x]
	endfor

	# Draw2: the normlaised time pitch contour
	select 'tableID'
	Draw scatter plot... 1 2 0 0 draw_start draw_end draw_min draw_max 11 0 "+" 1

	# select 'tableID'
	# Remove
endproc