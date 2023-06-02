# Manually check the P2FA alignment
# By Katrina Li (2022.11.22)
# Allow shoing the current file number (2022.12.20)
# Allow jump the rest of the loops (2023.2.27)

# Output
## Modified textgrid
### first generate the rhyme tier + syllable tier
### loop through the rhyme part, the modified boundaries will be marked in new word/syllable/rhyme tiers. 

# Buttons
## (Removed) PlayA/B: either play the one before the boundary, or play after the boundary 
### Update: now after moving the cursor, the PlayA/B plays the latest boundary. 
## Discard: If one sentence is seriously aligned wrong, click 'discard', then the rest of intervals will no longer be processed; 
##          the current interval will contain 'discard' in log.txt; and this interval will also be noted in discard.txt.

# Open the files (change for different langauge
################################
dir$ = "/Users/kechun/Documents/0_PhD_working_folder/Cantonese/workflow/"
sounddir$ = dir$ + "sound_original"
textgriddir$ = dir$ + "textgrid_original"
################################

# Specify the tiers
phonetier = 1
wordtier = 2
syllabletier = 3
rhymetier = 4
word_revisetier = 5
syllable_revisetier = 6
rhyme_revisetier = 7



textgridstrings = Create Strings as file list: "list", textgriddir$ + "/*.TextGrid"

# For each textgrid file, copy two new tiers
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

		# Check if there are two tiers
		numberOfTiers = Get number of tiers
		tier1name$ = Get tier name: phonetier
		tier2name$ = Get tier name: wordtier
		if numberOfTiers == 2
			Insert interval tier: rhymetier, "rhyme"
			Insert interval tier: syllabletier, "syllable"
			Insert interval tier: rhyme_revisetier, "rhyme2"
			Insert interval tier: word_revisetier, "word2"	
			Insert interval tier: syllable_revisetier, "syllable2"
		elif numberOfTiers != 2
			exitScript: "The number of tiers is not 2"
		elif tier1name$ != "phone"
			exitScript: "Tier 1 name is not 'phone'."
		elif tier2name$ != "word"
			exitScript: "Tier 2 name is not 'word'."
		endif

			
		# Combine with sound and open
		soundName$ = textgridName$ - ".TextGrid"
    	soundID = Read from file: sounddir$ + "/" + soundName$
		plus 'textgridID'
		View & Edit
		
		#prepare the logfile
		logfile$ = dir$ + "p2falog/" + soundName$ - ".wav" + "_log.txt"
		writeFileLine: logfile$, "TextgridName", tab$, "Interval", tab$, "Character", tab$, "Syllable", tab$, "Rhyme", tab$, "Note", tab$, "end_original", tab$, "end_new", tab$, "difference"

		# Generate the rime tier (This is not a universal function; the tier names are pre-written in the function)
		@generate_rime_tier

		numberOfRhyme = Get number of intervals: rhymetier
		interval = 1
		discard = 0 
		nextfile = 0

		# Allow stop the loop if discar changes t o1
		while interval < numberOfRhyme and discard != 1 and nextfile != 1
			skip = 0
			select 'textgridID'
			start = Get starting point: rhymetier, interval
  			end = Get end point: rhymetier, interval
			end_next = Get end point: rhymetier, interval+1
		    label$ = Get label of interval: rhymetier, interval
			syllable_label$ = Get label of interval: syllabletier, interval
			mid = (start + end)/2
			character_interval = Get interval at time: wordtier, mid
			character_label$ = Get label of interval: wordtier, character_interval
			# Calculate the end of character, to distinguish onset-rhyme boundary versus word boundaries
			character_end = Get end point: wordtier, character_interval
			# Zoom to character window, not rhyme window
			character_start = Get start point: wordtier, character_interval
			if interval + 1 != numberOfRhyme
				character_next_end= Get end point: wordtier, character_interval+1
			else
				character_next_end = Get end time
			endif
			
			# Zoom around editor
			editor TextGrid 'textgridName_current$'
				# Zoom into a two syllable window
				Zoom: character_start, character_next_end
				Move cursor to: end
			endeditor

			# Begin pause
			repeat
				beginPause("Check boundaries")
				comment("File 'textgridName_current$'(file number 'ifile' of 'numberOfFiles')")
				comment: "Note down any problem"
				text: "Note", ""
				clicked = endPause("NextFile", "Discard", "Reset", "Skip", "Align", 5)

				# If discard: jump to the next file, and note down in the file
				if clicked = 1
					nextfile = 1
				elif clicked = 2
					discard = 1
				elif clicked = 3
					editor TextGrid 'textgridName_current$'
						# Zoom into a two syllable window
						Zoom: character_start, character_next_end
						Move cursor to: end
					endeditor
				elif clicked = 4
					skip = 1
					appendInfoLine: "Inverval Skipped!"
				elif clicked = 5	 
					 editor TextGrid 'textgridName_current$'
						 newend = Get cursor
						 diff = newend - end
						 # If we move, then move to nearest zero crossing, but we won't move boundaries because of not at zero crossing.
						 Move cursor to nearest zero crossing
						 newend = Get cursor
					 endeditor
					 # Add boundaries at the two new tiers (if change the cursor, then use new; if not, then use the original)
					 if diff <> 0 and end == character_end
						@add_boundary: rhyme_revisetier, newend, label$
						@add_boundary: syllable_revisetier, newend, syllable_label$
						@add_boundary: word_revisetier, newend, character_label$
					 elif diff <> 0 and end != character_end
						@add_boundary: rhyme_revisetier, newend, label$
						@add_boundary: syllable_revisetier, newend, syllable_label$
					 elif diff == 0 and end == character_end
						@add_boundary: rhyme_revisetier, end, label$
						@add_boundary: syllable_revisetier, end, syllable_label$
						@add_boundary: word_revisetier, end, character_label$
					 elif diff == 0 and end != character_end
						@add_boundary: rhyme_revisetier, end, label$
						@add_boundary: syllable_revisetier, end, syllable_label$
					 endif
				endif
			until clicked = 1 or clicked = 2 or clicked = 4 or clicked = 5
			appendInfoLine: character_label$, tab$, label$, tab$, "finished."
			
			# if discard = 1, jump to the next file; if not, note the relevant info and save
			if discard = 1
				# Write to log files
				appendFileLine: logfile$, textgridName$, tab$, interval, tab$, character_label$, tab$, syllable_label$, tab$, label$, tab$, "Discarded!!!", tab$, end, tab$, newend, tab$, diff
				appendInfoLine: textgridName$, " needs realign!"
			elif nextfile = 1
				# Write to log files
				appendFileLine: logfile$, textgridName$, tab$, interval, tab$, character_label$, tab$, syllable_label$, tab$, label$, tab$, "Below not checked", tab$, end, tab$, newend, tab$, diff
				appendInfoLine: textgridName$, ": The rest are ignored!"
			elif skip =1
				# Note this interval has been deleted
				appendFileLine: logfile$, textgridName$, tab$, interval, tab$, character_label$, tab$, syllable_label$, tab$, label$, tab$, "Deleted", tab$, end, tab$, newend, tab$, diff
			else
				# Record the new and old boundary diff for each boudnary
				appendFileLine: logfile$, textgridName$, tab$, interval, tab$, character_label$, tab$, syllable_label$, tab$, label$, tab$, note$, tab$, end, tab$, newend, tab$, diff
			endif
			# for the next loop
			interval += 1
		endwhile
		# Upon finish, save the processed textgrid
		# Name for checked files
		textgridNewName$ =  textgridName$ - ".wav.TextGrid" + "_checked.TextGrid"
		Save as text file: dir$ + "textgrid_checked/" + textgridNewName$
		select 'soundID'
		plus 'textgridID'
		Remove
	endfor
endif

# Generate file, note the file processed, extract all the notes and files that need to realgin


procedure generate_rime_tier
	select 'textgridID'
	numberOfIntervals = Get number of intervals: wordtier
	# the loop is from beginnign to end, for it is not always ending with 'sp'
	for i from 1 to numberOfIntervals
		zero_onset = 0
 		#label_char$ = Get label of interval: wordtier, i
 		start_char = Get start time of interval: wordtier, i
  		end_char = Get end time of interval: wordtier, i
  		# check if it is the start of the file (it will not be recognised as an interval boundary)
  		isstart = Get interval boundary from time: wordtier, start_char
        # check if there is already an boudnary (e.g.zero onset syllables)
  		isboundary = Get interval boundary from time: rhymetier, start_char
  		if isstart != 0 & isboundary = 0
  			Insert boundary: rhymetier, start_char
			Insert boundary: syllabletier, start_char
  		endif

  		# Find the onset ending time, and add the boundary
  		onset_interval = Get high interval at time: phonetier, start_char
  		onset_label$ = Get label of interval: phonetier, onset_interval
  		#############Specify the sonorant list here: they will considered as part of rhyme!##############
  		if onset_label$ == "o" or onset_label$ == "u"
			#consider it as zero onset
			zero_onset = 1
			onset_end = Get start time of interval: phonetier, onset_interval
 		else
			#consider the first interval as onset
			onset_end = Get end time of interval: phonetier, onset_interval
  		endif

  		# check if it is the end of the file (it will not be recognised as an interval boundary)
  		isend = Get interval boundary from time: phonetier, onset_end
  		if isend != 0
			# Determine the rhyme text
  			rhyme_interval_start = Get high interval at time: phonetier, onset_end
  			rhyme_interval_end = Get low interval at time: phonetier, end_char
			# If it is a single vowel rhyme
  			if rhyme_interval_start == rhyme_interval_end + 1
				rhyme_label$ = Get label of interval: phonetier, rhyme_interval_end
			else
				rhyme_label$ = ""
  				for m from rhyme_interval_start to rhyme_interval_end
					label_seg$ = Get label of interval: phonetier, m
					rhyme_label$ = rhyme_label$ + label_seg$
  				endfor
			endif

			# check if there is already an boudnary (e.g.zero onset syllables)
			isboundary = Get interval boundary from time: rhymetier, onset_end
			if isboundary = 0
  				Insert boundary: rhymetier, onset_end
				Insert boundary: syllabletier, onset_end
    		endif

			# The method of setting interval text: get the interval index of tier 3 based on end_char time
			# If the label is sp, then discard
			if rhyme_label$ != "sp"
				# set rhyme text
				interval_count = Get low interval at time: rhymetier, end_char
				Set interval text: rhymetier, interval_count, rhyme_label$		
				Set interval text: syllabletier, interval_count, rhyme_label$	
			endif
			# set syllable onset text	
			if zero_onset = 0
				interval_onset_count = Get high interval at time: syllabletier, start_char
				Set interval text: syllabletier, interval_onset_count, onset_label$
			endif
  		endif
	endfor
endproc

procedure add_boundary: tier, point, text$
	select 'textgridID'
	Insert boundary: tier, point
	reviseinterval = Get low interval at time: tier, point
	Set interval text: tier, reviseinterval, text$
endproc