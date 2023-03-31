import glob
import textgrid
import pandas as pd
import re
import os
# Read the excel
Template = pd.read_excel("Template.xlsx",header=0,sheet_name="Cantonese")
Template = Template.drop("Original",axis=1)
Template["Case"] = Template["Case"].str.split(",")
Template["Sen_index"] = Template["Sen_index"].str.split(",")
# Compare if len(Trim) == len(Case) for each row
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
current_directory = pathdict["Cantonese"]
directory_textgrid = current_directory + "/textgrid_pitch_batch/**/*.TextGrid"

# Play with the actual annotation dataframe
textgrid_cantonese = glob.glob(directory_textgrid,recursive = True)
fulldata_char = pd.DataFrame()
for file in textgrid_cantonese:
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
    condition = re.split("dia[1-2]n?",textgridname.split("_")[0])[1]
    condition_focus = condition[-1]
    # Check if the string matches
    ## If match, then directly transfer all the information - attention: use .copy()!
    template_char = template[condition][0]
    Case = template[condition][1].copy()
    Sen_index = template[condition][2].copy()
    # Special case correction:
    if textgridname == "S17dia2AT3_checked.TextGrid":
        template_char = template_char[4:]
        Case = Case[4:]
        Sen_index = Sen_index[4:]
    # Clean up condition 4
    if condition_focus == "4": 
        char_manual = char_manual[:char_manual.index(template_char[-1])+1]
        mintime_char_manual = mintime_char_manual[:char_manual.index(template_char[-1])+1]
        maxtime_char_manual = maxtime_char_manual[:char_manual.index(template_char[-1])+1]
    # Start the overall loop
    if template_char == char_manual:
        case = Case
        sen_index = Sen_index
    else:
        ### Loop through individual case directly. 
        p,q = 0,0
        case = []
        sen_index = []
        note = []
        while p < len(char_manual):
            if q < len(template_char):
                if char_manual[p] == template_char[q]:
                    case.append(Case[q])
                    sen_index.append(Sen_index[q])
                    p,q = p+1, q+1
                    note.append("0")
                #### if an element is added
                elif p < len(char_manual)-1 and char_manual[p+1] == template_char[q]:
                    case.append("EXTRA")
                    sen_index.append(0)
                    p += 1
                    note.append("ADD")
                #### if an element is deleted
                elif q < len(char_manual)-1 and char_manual[p] == template_char[q+1]:
                    q +=1
                #### if an element is replaced
                elif q < len(char_manual)-1 and p < len(char_manual)-1 and char_manual[p+1] == template_char[q+1]:
                    case.append(Case[q])
                    sen_index.append(Sen_index[q])
                    note.append("Replace")
                    p,q = p+1,q+1
                else:
                    print("Problems: ", textgridname, "\n", char_manual, "\n", template_char, "\n", sen_index)
                    p += 1
                    print(p)
            else: 
                if char_manual[p] == '咯' or char_manual[p] == '啊':  
                    case.append("SFP")
                    sen_index.append(0)
                    note.append("SFP")
                    p +=1
                else:
                    case.append("Other final")
                    sen_index.append(0)
                    note.append("Other final stuff")
                    p +=1
    # Check if the length are equal
    assert len(char_manual) == len(mintime_char_manual) == len(maxtime_char_manual) == len(sen_index) == len(case)
    # if len(char_manual) != len(sen_index):
        # print("Unequal:", textgridname, "\n", char_manual, "\n", template_char,"\n", sen_index)
    data_char_manual = pd.DataFrame([sen_index, char_manual, case, mintime_char_manual, maxtime_char_manual])
    data_char_manual = data_char_manual.transpose()
    data_char_manual.columns = ["idx","character","case", "minTime","maxTime"]
    textgridname = file.split("/")[-1]
    data_char_manual['name'] = textgridname
    fulldata_char = pd.concat([fulldata_char,data_char_manual])
fulldata_char.to_csv("./results/Cantonese_char_dur_withcase.csv", index = False)