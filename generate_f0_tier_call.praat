# Praat script to call other scripts
strings = Read Strings from raw text file: "TargetFiles.txt"
# a set of scripts
numberOfFiles = Get number of strings
for ifile to numberOfFiles
	select 'strings'
	textgridName$ = Get string: ifile
    f0min = 0 
    f0max = 0
    runScript: "generate_f0_tier.praat", textgridName$, f0min, f0max
endfor