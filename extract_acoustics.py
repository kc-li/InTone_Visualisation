import glob
import textgrid
import pandas as pd
import re
import os
import parselmouth
from parselmouth.praat import call
import math
from datetime import date #add today's date
import difflib as dl
from bisect import bisect
####### Current language#######
current_lang = "Chengdu"
f0points = 10 #for Prosody Visualisation challenges, I plotted 20 points for each syllable for smoothier curve.
today = date.today()
today = today.strftime("%y%m%d")
# Read the excel
Template = pd.read_excel("Template.xlsx",header=0,sheet_name=current_lang)
Template = Template.drop("Original",axis=1)
Template["Case"] = Template["Case"].str.split(",")
Template["Sen_index"] = Template["Sen_index"].str.split(",")
# Compare if len(Trim) == len(Case) for each row (When you want to check the output)
# print(Template["Trim"].str.len().compare(Template["Case"].str.len()))
# print(Template["Trim"].str.len().compare(Template["Sen_index"].str.len()))
# Convert to dictionary 
template = Template.set_index("Label").T.to_dict("list")

## Read the directory from another files.
## Note: Users can directly specify the path. 
# Read the Directory.txt, and get the path
pathdict = {}
with open("Directory.txt") as f:
    for line in  f:
        (language,path) = line.strip().split(":")
        pathdict[language] = path
####################Change the current language################
current_directory = pathdict[current_lang]
directory_textgrid = current_directory + "/textgrid_pitch_batch/*.TextGrid" # Add /**/ if want to read subfolders as well
directory_sound = current_directory + "/sound_original/"
####################Specify the output file####################
output_tsv_name = "./extract_acoustics_results/" + today + str(current_lang) + "_data.tsv"
output_tsv = open(output_tsv_name,"w")
# specify the series based on number of points
step_list = ["step" + str(i+1) for i in range(0,f0points)]
t_list = ["t" + str(i+1) for i in range(0,f0points)]
output_tsv.write("\t".join(["filename","enum","defaultf0floor","defaultf0ceiling","idx", "character", "case", "minTime", "maxTime", "char_duration", "boundary", "syl_rhyme", "syl_rhyme_minTime", "syl_rhyme_maxTime", "syl_rhyme_duration", "rhyme", "rhyme_minTime", "rhyme_maxTime", "rhyme_duration", "f0min", "f0max", "f0min_time", "f0max_time"] + step_list + t_list) + "\n")
output2_tsv_name = "./extract_acoustics_results/" + today + str(current_lang) + "_realf0_data.tsv"
output2_tsv = open(output2_tsv_name,"w")
output2_tsv.write("\t".join(["filename","enum", "defaultf0floor","defaultf0ceiling","idx", "character", "case", "minTime", "maxTime", "boundary", "rhyme", "time","f0"]) + "\n")

# Play with the actual annotation dataframe
textgrid_files = glob.glob(directory_textgrid,recursive = True)
fulldata_char = pd.DataFrame()

# Report the list
SFP_dict = {}
ADD_dict = {}
REP_dict = {}

# Count the files
nfile = 0
for file in textgrid_files:
    nfile += 1
    ## Propcess the Textgrid for duration information
    tg = textgrid.TextGrid.fromFile(file)
    char_tier_manual = tg[4]
    char_manual = [char_tier_manual[i].mark for i in range(0, len(char_tier_manual))]
    mintime_char_manual = [char_tier_manual[i].minTime for i in range(0,len(char_tier_manual))]
    maxtime_char_manual = [char_tier_manual[i].maxTime for i in range(0,len(char_tier_manual))]
    # Remove the empty element - use zip to move the relevant position in time data as well
    # for ele1, ele2,ele3 in zip(char_manual,mintime_char_manual,maxtime_char_manual):
    #     if ele1 != "" and ele1 != "sp": --- this method needs a new list, but I want to directly modify existing list.
    mintime_char_manual[:] = [ele2 for ele1, ele2 in zip(char_manual,mintime_char_manual) if ele1 != "" and ele1 != "sp"]
    maxtime_char_manual[:] = [ele2 for ele1, ele2 in zip(char_manual,maxtime_char_manual) if ele1 != "" and ele1 != "sp"]   
    char_manual = list(filter(None,char_manual))
    char_manual = list(filter(lambda a: a != 'sp', char_manual))
    assert len(char_manual) == len(mintime_char_manual) == len(maxtime_char_manual)
    # Match the condition
    textgridname = file.split("/")[-1]
    condition = re.split("diaN?[1-2]?n?",textgridname.split("_")[0])[1]
    condition_focus = re.search("[1-5]a?",condition).group(0)
    # Check if the string matches
    ## If match, then directly transfer all the information - attention: use .copy()!
    template_char = template[condition][0]
    Case = template[condition][1].copy()
    Sen_index = template[condition][2].copy()
    # Using using diff functions
    d = dl.SequenceMatcher(None, char_manual, template_char)
    info = d.get_opcodes()
    # Inherent the template sequence and then change
    case_manual = ["0.1"]*len(char_manual)
    sen_index_manual = ["0.1"]*len(char_manual)
    for tag, i1, i2, j1, j2 in info:
        # eqaul
        if tag == "equal": # string b
            case_manual[i1:i2] = Case[j1:j2]
            sen_index_manual[i1:i2] = Sen_index[j1:j2]
        # replace
        if tag == "replace": # string b
            case_manual[i1:i2] = ["REP"] * (i2-i1)
            # Add to REP dictionary
            for i in range(i1,i2):
                if char_manual[i] in REP_dict:
                    REP_dict[char_manual[i]] += 1
                else: REP_dict[char_manual[i]] = 1
        # insert: string b missing a element, ignore
        # delete: 
        elif tag == "delete": 
            case_manual[i1:i2] = ["ADD"] * (i2-i1)
            for i in range(i1,i2):
                if char_manual[i] in ADD_dict:
                    ADD_dict[char_manual[i]] += 1
                else: ADD_dict[char_manual[i]] = 1
    ########################## Specify the SFP category: language dependent #####################
    # # find the value of sen_index, and locate
    critical_index = sen_index_manual.index(max(sen_index_manual)) + 1
    # it should be either the last token in the sentence (the order of two conditions are important; to prevent 'out of range' problem')
    if critical_index + 1 == len(char_manual) and case_manual[critical_index] == "ADD":
        case_manual[-1] = "SFP"
        if char_manual[-1] in SFP_dict:
            SFP_dict[char_manual[-1]] += 1
            ADD_dict[char_manual[-1]] -=1
        else: 
            SFP_dict[char_manual[-1]] = 1
            ADD_dict[char_manual[-1]] -=1      
    # Check if the length of list is equal
    assert len(char_manual) == len(mintime_char_manual) == len(maxtime_char_manual) == len(sen_index_manual) == len(case_manual)


    ## Incorporate the f0 infomation
    textgridname = file.split("/")[-1]
    soundname = directory_sound + textgridname.split("_")[0] + ".wav"
    sound = parselmouth.Sound(soundname)
    f0_tier = tg[6]
    syl_tier = tg[5]

    # Get syl_tier info
    syl_label = [syl_tier[i].mark for i in range(0, len(syl_tier))]
    mintime_syl = [syl_tier[i].minTime for i in range(0,len(syl_tier))]
    maxtime_syl = [syl_tier[i].maxTime for i in range(0,len(syl_tier))]

    # Get f0 tier info
    f0_label = [f0_tier[i].mark for i in range(0, len(f0_tier))]
    mintime_f0 = [f0_tier[i].minTime for i in range(0,len(f0_tier))]
    maxtime_f0 = [f0_tier[i].maxTime for i in range(0,len(f0_tier))]

    ######################## Time parameters ######################################
    # Note that the table title needs to be changed accordingly
    # Normtime: The number of points extracted from each interval
    number_of_points = f0points
    # Time: Sampling rate
    time_step = 0.01
    ##############################################################################
    ## Calculate the best f0 range based on Hirst (2001)
    # The first pass
    pitch1 = call(sound, "To Pitch", 0.0, 50, 800)
    min1 = call(pitch1, "Get minimum", 0, 0, "Hertz", "None")
    max1 = call(pitch1, "Get maximum", 0, 0, "Hertz", "None")
    q1 = call(pitch1, "Get quantile", 0, 0, 0.25, "Hertz")
    q3 = call(pitch1, "Get quantile", 0, 0, 0.75, "Hertz")
    q1 = math.floor(q1)
    q3 = math.ceil(q3)
    # The second pass
    defaultf0floor = math.floor((0.7 * q1)/ 10) * 10
    defaultf0ceiling = math.ceil((2.5 * q3)/ 10) * 10

    # Check if pointprocess file exist
    pointprocessname = current_directory + "/textgrid_pitch_batch/" + textgridname.split("_")[0] + ".PointProcess"
    pitchname = current_directory + "/textgrid_pitch_batch/" + textgridname.split("_")[0] + ".Pitch"
    if os.path.isfile(pitchname):
        pitch2 = parselmouth.read(pitchname)
        # print(pitchname)
    elif os.path.isfile(pointprocessname):
        pointprocess = parselmouth.read(pointprocessname)
        pitchtier = call(pointprocess, "To PitchTier", 0.02)
        pitch2 = call(pitchtier, "To Pitch", 0.02, defaultf0floor, defaultf0ceiling)
    else:
        pitch2 = call(sound, "To Pitch", 0.0, defaultf0floor, defaultf0ceiling)
    
    rhyme_info_series = []
    rhyme_puref0_series = []
    sen_index_rhyme = []
    index_tuple_series = []

    for i in range(0, len(f0_tier)):
        rhyme_label = f0_tier[i].mark
        if rhyme_label != "":
            start = f0_tier[i].minTime
            end = f0_tier[i].maxTime
            duration = end-start
            duration_formatted = float("{:.5f}".format(duration))

            # Get normtime f0
            f0_norm = []
            normtime_series = []
            # It's better to start with 1, so excluding some purtabation period
            for x in range(1,number_of_points+1):
                current_normtime = start + duration*(x-1)/(number_of_points)
                current_normtime_formatted = float("{:.5f}".format(current_normtime))
                normtime_series.append(current_normtime_formatted)
                f0_at_normtime = call(pitch2, "Get value at time", current_normtime, 'Hertz', 'Linear')
                f0_at_normtime_formatted = float("{:.3f}".format(f0_at_normtime))
                f0_norm.append(f0_at_normtime_formatted)
                # print(normtime, "\t", f0_at_normtime_formatted)
            assert len(f0_norm) == number_of_points

            # Get f0 statistics
            f0min = call(pitch2, "Get minimum", start, end, "Hertz", "None")
            f0min_formatted = float("{:.3f}".format(f0min))
            f0max = call(pitch2, "Get maximum", start, end, "Hertz", "None")
            f0max_formatted = float("{:.3f}".format(f0max))
            f0min_time = call(pitch2, "Get time of minimum", start, end, "Hertz", "Parabolic")
            f0max_time = call(pitch2, "Get time of maximum", start, end, "Hertz", "Parabolic")
            #print(label, "\t", f0min_time, "\t",f0max_time)
            ## Compare the number stamp, to map the rhyme tier to the processed character tier

            # Consider mapping to the already built character tier and syllable tier
            mid = (start+end)/2
            cor_index_char = bisect(mintime_char_manual, mid)-1
            cor_index_syl = bisect(mintime_syl, mid)-1
            # test: Print if error emerges. One possible error is accidental space. Go back to file and correct this.
            # print(textgridname)
            # print(syl_label[cor_index_syl])
            # print(rhyme_label)
            assert syl_label[cor_index_syl] == rhyme_label
            # Save the correlated index
            index_tuple = (cor_index_char,cor_index_syl,i)
            index_tuple_series.append(index_tuple)

            # Save rhyme_info
            rhyme_info = [rhyme_label, str(start), str(end), str(duration_formatted), str(f0min_formatted), str(f0max_formatted),str(f0min_time),str(f0max_time)]
            rhyme_info.extend(map(str, normtime_series))
            rhyme_info.extend(map(str, f0_norm))
            rhyme_info_zip = (i, rhyme_info)
            rhyme_info_series.append(rhyme_info_zip)
            # print(rhyme_info)

            # Get unnormalised f0
            f0 = []
            time_series = []
            time = start
            while time < end:
                f0_at_time = call(pitch2, "Get value at time", time, 'Hertz', 'Linear')
                f0_at_time_formatted = float("{:.3f}".format(f0_at_time))
                time_formatted = float("{:.3f}".format(time))
                time_series.append(time_formatted)
                f0.append(f0_at_time_formatted)
                time += time_step
            assert len(time_series) == len(f0)
            f0_zipped = list(zip(map(str,time_series), map(str,f0)))
            rhyme_puref0 = (i, rhyme_label, f0_zipped)
            rhyme_puref0_series.append(rhyme_puref0)     
    
    # flatten the tuple list
    index_tuple_series = list(zip(*index_tuple_series))
    rhyme_info_series = list(zip(*rhyme_info_series))
    rhyme_puref0_series = list(zip(*rhyme_puref0_series))
    # print(char_manual)
    # print(rhyme_puref0_series)
    # print(rhyme_info_series)
    # print(index_tuple_series)

    # Write lines to file
    for i in range(0,len(char_manual)):
        out = []
        out.append(textgridname.split("_")[0])
        out.append(str(i)) #as unique ID
        out.append(str(float("{:.0f}".format(defaultf0floor))))
        out.append(str(float("{:.0f}".format(defaultf0ceiling))))
        # char_duration
        char_duration = maxtime_char_manual[i] - mintime_char_manual[i]
        char_duration_formatted = float("{:.5f}".format(char_duration))
        out.extend([str(sen_index_manual[i]), char_manual[i], case_manual[i], str(mintime_char_manual[i]), str(maxtime_char_manual[i]), str(char_duration_formatted)])
        
        # append if boundary
        if sen_index_manual[i] == max(sen_index_manual):
            out.append("1")
        else:
            out.append("0")

        # if the current index is in the tuple list
        if i in index_tuple_series[0]:
            cor_index = index_tuple_series[0].index(i)
            syl_index = index_tuple_series[1][cor_index]
            rhyme_index = index_tuple_series[2][cor_index]

            # export duration from syllable tier
            out.append(syl_label[syl_index])
            # if maxtime_syl[syl_index] > maxtime_char_manual[i]:
            #     print(textgridname.split("_")[0])
            #     print(char_manual[i])
            assert mintime_syl[syl_index] >= mintime_char_manual[i]
            # if maxtime_syl[syl_index] > maxtime_char_manual[i]:
            #     print(textgridname.split("_")[0])
            #     print(char_manual[i])
            #     print(syl_label[syl_index])
            assert maxtime_syl[syl_index] <= maxtime_char_manual[i]
            syllable_rhyme_duration = maxtime_syl[syl_index]-mintime_syl[syl_index]
            syllable_rhyme_duration_formatted = float("{:.5f}".format(syllable_rhyme_duration))

            out.append(str(mintime_syl[syl_index]))
            out.append(str(maxtime_syl[syl_index]))
            out.append(str(syllable_rhyme_duration_formatted))
            # Access rhyme information
            rhyme_info_index = rhyme_info_series[0].index(rhyme_index)
            out.extend(rhyme_info_series[1][rhyme_info_index])
            # print(out)
    
            for tup in rhyme_puref0_series[2][rhyme_info_index]:
                out2 = []
                out2.append(textgridname.split("_")[0])
                out2.append(str(i)) #as unique ID
                out2.append(str(float("{:.0f}".format(defaultf0floor))))
                out2.append(str(float("{:.0f}".format(defaultf0ceiling))))
                out2.extend([str(sen_index_manual[i]), char_manual[i], case_manual[i], str(mintime_char_manual[i]), str(maxtime_char_manual[i])])
                if sen_index_manual[i] == max(sen_index_manual):
                    out2.append("1")
                else:
                    out2.append("0")
                # rhyme_label
                out2.append(rhyme_puref0_series[1][rhyme_info_index])
                # time - f0
                out2.extend(list(tup))
                # print(out2)
                output2_tsv.write("\t".join(out2) + "\n")
        output_tsv.write("\t".join(out) + "\n")

# Report the number of files
print("Number of files processed: ", str(nfile))
# Print some information to make sure it looks right
print("REP dictionary")
for k, v in sorted(REP_dict.items(),key=lambda x: x[1], reverse=True):
    print("\t".join([str(k), str(v)]))
print("ADD dictionary")
for k, v in sorted(ADD_dict.items(),key=lambda x: x[1], reverse=True):
    print("\t".join([str(k), str(v)]))
print("SFP dictionary")
for k, v in sorted(SFP_dict.items(),key=lambda x: x[1], reverse=True):
    print("\t".join([str(k), str(v)]))