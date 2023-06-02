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
####### Current language#######
current_lang = "Cantonese"
today = date.today()
today = today.strftime("%y%m%d")
# Read the excel
Template = pd.read_excel("Template.xlsx",header=0,sheet_name=current_lang)
Template = Template.drop("Original",axis=1)
Template["Case"] = Template["Case"].str.split(",")
Template["Sen_index"] = Template["Sen_index"].str.split(",")
# Compare if len(Trim) == len(Case) for each row (When you want to check the output)
print(Template["Trim"].str.len().compare(Template["Case"].str.len()))
print(Template["Trim"].str.len().compare(Template["Sen_index"].str.len()))
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
####################Change the current language#################3
current_directory = pathdict[current_lang]
directory_textgrid = current_directory + "/textgrid_pitch_batch/*.TextGrid" # Add /**/ if want to read subfolders as well
directory_sound = current_directory + "/sound_original/"
####################Specify the output file####################
output_tsv_name = "./extract_acoustics_results/" + today + str(current_lang) + "_data.tsv"
output_tsv = open(output_tsv_name,"w")
output_tsv.write("\t".join(["filename","enum","defaultf0floor","defaultf0ceiling","idx", "character", "case", "minTime", "maxTime", "rhyme", "rhyme_duration", "f0min", "f0max", "f0min_time", "f0max_time", "t1","t2","t3","t4","t5","t6","t7","t8","t9","t10"]) + "\n")
# "t11","t12","t13","t14","t15","t16","t17","t18","t19","t20"
output2_tsv_name = "./extract_acoustics_results/" + today + str(current_lang) + "_realf0_data.tsv"
output2_tsv = open(output2_tsv_name,"w")
output2_tsv.write("\t".join(["filename","enum", "defaultf0floor","defaultf0ceiling","idx", "character", "case", "minTime", "maxTime", "rhyme", "time","f0"]) + "\n")

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
    # Match the condition
    textgridname = file.split("/")[-1]
    condition = re.split("diaN?[1-2]?n?",textgridname.split("_")[0])[1]
    condition_focus = re.search("[1-5]a?",condition).group(0)
    # Check if the string matches
    ## If match, then directly transfer all the information - attention: use .copy()!
    template_char = template[condition][0]
    Case = template[condition][1].copy()
    Sen_index = template[condition][2].copy()

    # Special case correction:
    # if current_lang == "Cantonese":
    #     if textgridname == "S17dia2AT3_checked.TextGrid":
    #         template_char = template_char[4:]
    #         Case = Case[4:]
    #         Sen_index = Sen_index[4:]
    # Clean up condition 4
    # if condition_focus == "4": 
    #     char_manual = char_manual[:char_manual.index(template_char[-1])+1]
    #     mintime_char_manual = mintime_char_manual[:char_manual.index(template_char[-1])+1]
    #     maxtime_char_manual = maxtime_char_manual[:char_manual.index(template_char[-1])+1]
    # New version of using diff functions
    d = dl.SequenceMatcher(None, char_manual, template_char)
    info = d.get_opcodes()
    # Inherent the template sequence and then change
    case_manual = ["0"]*len(char_manual)
    sen_index_manual = ["0"]*len(char_manual)
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
    # Specify the SFP category
    if case_manual[-1] == "ADD" and case_manual[-2] != "ADD":
        case_manual[-1] = "SFP"
        if char_manual[-1] in SFP_dict:
            SFP_dict[char_manual[-1]] += 1
            ADD_dict[char_manual[-1]] -=1
        else: 
            SFP_dict[char_manual[-1]] = 1
            ADD_dict[char_manual[-1]] -=1
    # Print and see special
    # if "SFP" in case_manual:
    #     print(char_manual)
    #     print(case_manual)
    #     print(sen_index_manual)
    # Check if the length of list is equal
    assert len(char_manual) == len(mintime_char_manual) == len(maxtime_char_manual) == len(sen_index_manual) == len(case_manual)
    
    ## Incorporate the f0 infomation
    textgridname = file.split("/")[-1]
    soundname = directory_sound + textgridname.split("_")[0] + ".wav"
    sound = parselmouth.Sound(soundname)
    f0_tier = tg[6]
    ######################## Time parameters ######################################
    # Note that the table title needs to be changed accordingly
    # Normtime: The number of points extracted from each interval
    number_of_points = 10
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
    ## Ad-hoc modification (generate point process)
    # if current_lang == "Chengdu":
    #     if textgridname == "S2diaD2_checked.TextGrid":
    #         pointprocessname = current_directory + "/textgrid_pitch_batch/" + textgridname[:-9] + ".PointProcess"
    #         if not os.path.isfile(pointprocessname):
    #             pointprocess = call(sound, "To PointProcess (periodic, cc)", defaultf0floor, defaultf0ceiling)
    #             pointprocess.save(current_directory + "/textgrid_pitch_batch/" + textgridname[:-9] + ".PointProcess")
    # if current_lang == "Changsha":
    #     if textgridname == "S22diaN1F5_checked.TextGrid" or textgridname == "S22diaB5_checked.TextGrid":
    #         pointprocessname = current_directory + "/textgrid_pitch_batch/" + textgridname[:-9] + ".PointProcess"
    #         if not os.path.isfile(pointprocessname):
    #             pointprocess = call(sound, "To PointProcess (periodic, cc)", defaultf0floor, defaultf0ceiling)
    #             pointprocess.save(current_directory + "/textgrid_pitch_batch/" + textgridname[:-9] + ".PointProcess")
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
    for i in range(0, len(f0_tier)):
        rhyme_label = f0_tier[i].mark
        if rhyme_label != "":
            start = f0_tier[i].minTime
            end = f0_tier[i].maxTime
            
            # Get normtime f0
            duration = end-start
            f0_norm = []
            # It's better to start with 1, so excluding some purtabation period
            for x in range(1,number_of_points+1):
                normtime = start + duration*(x-1)/(number_of_points)
                f0_at_normtime = call(pitch2, "Get value at time", normtime, 'Hertz', 'Linear')
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
            # Consider mapping to the already built character tier
            mid = (start+end)/2
            # Compare
            index = 0
            # the last interval causes problem; filter it first
            while index < len(mintime_char_manual) and mid > mintime_char_manual[index]:
                index += 1
            # The actual index is actually one step back
            index = index-1
            # !This is the index in the original list, that can be used to map with the previous list!
            # check the tiem stamp in between two values
            assert mid < maxtime_char_manual[index]
            sen_index_rhyme.append(sen_index_manual[index])
            rhyme_info = [rhyme_label, str(duration), str(f0min_formatted), str(f0max_formatted),str(f0min_time),str(f0max_time)]
            f0_norm_string = map(str, f0_norm)
            rhyme_info.extend(f0_norm_string)
            rhyme_info_series.append(rhyme_info)
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
            rhyme_puref0 = [rhyme_label, f0_zipped]
            rhyme_puref0_series.append(rhyme_puref0)
            
    # print(rhyme_info_series)
    # Write lines to file
    for i in range(0,len(char_manual)):
        out = []
        out.append(textgridname.split("_")[0])
        out.append(str(i)) #as unique ID
        out.append(str(float("{:.0f}".format(defaultf0floor))))
        out.append(str(float("{:.0f}".format(defaultf0ceiling))))
        out.extend([str(sen_index_manual[i]), char_manual[i], case_manual[i], str(mintime_char_manual[i]), str(maxtime_char_manual[i])])
        if sen_index_manual[i] in sen_index_rhyme:
            # Print norm time rhyme info
            rhyme_index = sen_index_rhyme.index(sen_index_manual[i])
            out.extend(rhyme_info_series[rhyme_index])
            # Print real time rhyme info
            # rhyme_puref0_series[rhyme_index][1] is the zipped list
            for tup in rhyme_puref0_series[rhyme_index][1]:
                out2 = []
                out2.append(textgridname.split("_")[0])
                out2.append(str(i)) #as unique ID
                out2.append(str(float("{:.0f}".format(defaultf0floor))))
                out2.append(str(float("{:.0f}".format(defaultf0ceiling))))
                out2.extend([str(sen_index_manual[i]), char_manual[i], case_manual[i], str(mintime_char_manual[i]), str(maxtime_char_manual[i])])
                out2.append(rhyme_puref0_series[rhyme_index][0])
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