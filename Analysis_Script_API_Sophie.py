import datetime
import json
import os
import pdb
import requests
import statistics
import sys
import time
from matplotlib import pyplot
import tkinter as Tkinter
import tkinter.filedialog as tkFileDialog
import pandas as pd

#set to true to load data from pre-saved JSONs (22/11/2019) for testing
test=True


#Sets the title of the cmd window (checks if windows as gives warning on Linux)
if os.name.upper()=="NT":
    os.system("title Open Prescribing Data Analyser")

#Function to prompt the user to press enter to quit (was being used many times)
def close():
    input("Press Enter to Quit: ")
    sys.exit()
    
#make request link into JSON format
#Count increases each time (incase problem with API is due to rate limiting), after 10 attempts dies and informs user
def restrequest(rawrequest, COUNT=0):
    try:
        request = requests.get(rawrequest)
        json_string = request.text
        json_obj = json.loads(json_string)
        request.close()
    except:
        time.sleep(COUNT)
        COUNT+=1
        if COUNT>10:
            print("Too many attempts made, please try again later")
            close()
        restrequest(rawrequest, COUNT=COUNT)
    return json_obj

#function for displaying a dropdown list and then returning the selected value
def drop_select(OPTIONS,text,ALL=False):
    print(text)
    rootwindow = Tkinter.Tk()
    rootwindow.attributes("-topmost",True)
    #Adds choices to dropdown and selects first one as default, sorted by name
    if ALL==True:
        OPTIONS+=["_ALL_"]
    OPTIONS=sorted(OPTIONS)
    dropVars=Tkinter.StringVar(rootwindow)
    dropVars.set(OPTIONS[0])
    choices=Tkinter.OptionMenu(rootwindow,dropVars,*OPTIONS)
    choices.pack()
    #close dropdown after selection
    def select():
        rootwindow.quit()
    #closes dropdown and quits script after clicking cancel
    def cancel():
        rootwindow.quit()
        rootwindow.withdraw()
        close()
    button = Tkinter.Button(rootwindow, text="Select", command=select)
    button.pack()
    button2 = Tkinter.Button(rootwindow, text="Cancel", command=cancel)
    button2.pack()
    #sets title and size for the window
    rootwindow.title(text)
    rootwindow.geometry("300x100")
    #Runs the selection loop
    rootwindow.mainloop()
    #gets the selection name and stores it in variable 
    result=dropVars.get()
    #hides the rootwindow (selection window)
    rootwindow.withdraw()
    return result

#selects the ccg_id (if search term returns one item it uses that
#otherwise it displaces a selection dropdown)
def ccg_select():
    while True:
        ccg=input("Enter name of CCG to investigate: ")
        request="https://openprescribing.net/api/1.0/org_code/?format=json&org_type=CCG&q={}".format(ccg)
        json_obj=restrequest(request)
        if len(json_obj)==0:
            print("No Valid Items Found")
        elif len(json_obj)>1:
            OPTIONS=["{} ~ {}".format(entry["name"],entry["id"]) for entry in json_obj]
            ccg=drop_select(OPTIONS, "Select CCG")
            return ccg.split("~")[1].strip(), ccg.split("~")[0].strip()
        elif len(json_obj)==1:
            ccg_id=json_obj[0]["code"]
            ccg_name=json_obj[0]["name"]
            print("Found CCG ID of {}".format(ccg_id))
            return ccg_id, ccg_name
        
#selects the bng_id (if search term returns one item it uses that
#otherwise it displaces a selection dropdown)       
def drug_select():
    while True:
        drug=input("Enter Name of Drug Family: ")
        request="https://openprescribing.net/api/1.0/bnf_code/?format=json&q={}".format(drug)
        json_obj=restrequest(request)
        if len(json_obj)==0:
            print("No Valid Items Found")
        elif len(json_obj)==1:
            drug_id=json_obj[0]["id"]
            drug_name=json_obj[0]["name"]
            print("Found BNF ID of {}".format(drug_id))
            return drug_id,drug_name
        else:
            #Only allows items that are 'BNF Section' as future JSON search relies on this value
            OPTIONS=["{} ~ {}".format(entry["name"],entry["id"]) for entry in json_obj if entry["type"]=="BNF section"]
            if len(OPTIONS)==1:
                return OPTIONS[0].split("~")[1].strip(), OPTIONS[0].split("~")[0].strip()
            elif len(OPTIONS)==0:
                print("No Valid Items Found")
            else:
                drug=drop_select(OPTIONS,"Select BNF Name")
                return drug.split("~")[1].strip(), drug.split("~")[0].strip()

#Prompts the user to select a GP Practice and makes a trend plot overtime
def trends():
    rootwindow.withdraw()
    rootwindow.quit()
    #Gets a sorted list of options for the dropdown showing practice name and code
    gps=["{} ~ {}".format(name,code) for name,code in practice_dict.items()]
    selected=drop_select(gps,"Select GP Practice", True)
    practice=selected.split("~")[0].strip()
    if selected=="_ALL_":
        gps.remove("_ALL_")
        for GP in sorted(gps):
            plot(GP.split("~")[0].strip())
    else:
        plot(practice)
    close()
    
def plot(practice):
    dates=["-".join(key.split("-")[:2]) for key in data_dict[practice].keys()]
    values=[value["Rate"] for value in data_dict[practice].values()]
    if values!=[]:
        pyplot.figure(figsize=(20,10))
        pyplot.title("{} (BNF - {}) Prescriptions per 100 patients for {} ({})".format(bnf_name, bnf_id, practice, practice_dict[practice]),fontsize=18)
        pyplot.ylabel("Number of Prescriptions per 100 patients")
        pyplot.xlabel("Date")
        pyplot.plot(dates, values)
        #rotates x-axis and otherwise text runs into each other
        pyplot.xticks(rotation=90)
        pyplot.savefig('{} ({}) - {} Trend'.format(practice,practice_dict[practice], bnf_name))
        pyplot.close()
        print("Graph saved as '{} ({}) - {} Trend.png'".format(practice,practice_dict[practice], bnf_name))
    else:
        print("Data not availible for {} ({})".format(practice,practice_dict[practice]))

def stats_date():
    #gets an array of all unique dates
    dates=[]
    for GP, dicts in data_dict.items():
        for date, values in data_dict[GP].items():
            if date not in dates:
                dates+=[date]
    #selects a date (if "_ALL_" all dates are used with the "_ALL_" removed from the list)
    selected_dates=[drop_select(dates,"Select Date",True)]
    if selected_dates==["_ALL_"]:
        selected_dates=dates
        selected_dates.remove("_ALL_")
    for selected_date in selected_dates:
        date_dict={}
        #Creates dict of GP:Rate for that date
        for GP, dicts in data_dict.items():
            for date, values in data_dict[GP].items():
                if date==selected_date:
                    date_dict[GP]=values["Rate"]
        #sorts are gets highest and lowest
        values=sorted(date_dict.items(), key=lambda kv:kv[1])    
        top_name, top=values[-1][0],values[-1][1]
        low_name, low=values[0][0],values[0][1]
        #gets average and stddev
        total=0
        for value in values:
            total+=value[1]
        stdev=statistics.stdev([value[1] for value in values])    
        average=total/len(values)
        lower_lim=average-stdev
        upper_lim=average+stdev
        #gets those above/below 1 stddev
        lowers=[]
        uppers=[]
        for value in values:
            if value[1]>upper_lim:
                uppers+=[value[0]]
            elif value[1]<lower_lim:
                lowers+=[value[0]]
        #writes info to text file
        with open("Stats for {} - {} ({}).txt".format(selected_date,bnf_name, bnf_id),"wt") as f:
            f.write("The Practice with the highest Prescription rate was {} ({}) with {} per 100 Patients \n".format(top_name,practice_dict[top_name],round(top,2)))
            f.write("The Practice with the lowest Prescription rate was {} ({}) with {} per 100 Patients \n".format(low_name,practice_dict[low_name],round(low,2)))
            f.write("The Average Presection rate was {} per 100 Patients".format(round(average,2)))
            if uppers!=[]:
                f.write("The Following Practices were 1 standard deviation above the average: \n")
                for upper in uppers:
                    f.write("{} ({})\n".format(upper,practice_dict[upper]))
            if lowers!=[]:
                f.write("The Following Practices were 1 standard deviation below the average: \n")
                for lower in lowers:
                    f.write("{} ({})\n".format(lower,practice_dict[lower]))    
        print("File saved as 'Stats for {} - {} ({}).txt'".format(selected_date,bnf_name, bnf_id))
    close()

def stats_GP():
    gps=["{} ~ {}".format(name,code) for name,code in practice_dict.items()]

    selected=drop_select(gps,"Select GP",True)
    if selected=="_ALL_":
        selected=[name for name in practice_dict.keys()]
    else:
        selected=[selected.split("~")[0].strip()]
    for selected_gp in selected:
        gp_dict={}
        for GP, dicts in data_dict.items():
            if GP==selected_gp:
                for date, values in data_dict[GP].items():
                    gp_dict[date]=values["Rate"]
        if gp_dict!={}:
            values=sorted(gp_dict.items(), key=lambda kv:kv[1])
            
            top_date, top=values[-1][0],values[-1][1]
            low_date, low=values[0][0], values[0][1]
            total=0
            for value in values:
                total+=value[1]
            stdev=statistics.stdev([value[1] for value in values])    
            average=total/len(values)
            lower_lim=average-stdev
            upper_lim=average+stdev
            lowers=[]
            uppers=[]
            for value in values:
                if value[1]>upper_lim:
                    uppers+=[value[0]]
                elif value[1]<lower_lim:
                    lowers+=[value[0]]
            with open("Stats for {} - {} ({}).txt".format(selected_gp,bnf_name, bnf_id),"wt") as f:
                f.write("The Month with the highest Prescription rate was {} with {} per 100 patients \n".format(top_date,round(top,2)))
                f.write("The Month with the lowest Prescription rate was {} with {} per 100 patients \n".format(low_date,round(low,2)))
                f.write("The Average Presection rate was {} per 100 Patients".format(round(average,2)))
                if uppers!=[]:
                    f.write("The Following Months were 1 standard deviation above the average for this Practice: \n")
                    for upper in uppers:
                        f.write("{}\n".format(upper))
                if lowers!=[]:
                    f.write("The Following Months were 1 standard deviation below the average for this Practice: \n")
                    for lower in lowers:
                        f.write("{}\n".format(lower))
            print("File saved as 'Stats for {} ({}) - {} ({}).txt'".format(selected_gp,practice_dict[selected_gp],bnf_name, bnf_id))
        else:
            print("No Data Availible for this Practice: {} ({})".format(selected_gp, practice_dict[selected_gp]))
    close()

def stats():
    globals()['rootwindow'].withdraw()
    globals()['rootwindow'].quit()
    rootwindow = Tkinter.Tk()
    rootwindow.title("Select Function")
    rootwindow.attributes("-topmost",True)
    print("Select Function")
    def GP():
        rootwindow.withdraw()
        rootwindow.quit()
        stats_GP()
    def date():
        rootwindow.withdraw()
        rootwindow.quit()
        stats_date()
    Tkinter.Label(rootwindow, text="Select Function").grid(column=0, row=0, columnspan=2, padx=10, pady=5)
    Tkinter.Button(rootwindow, text="Analyse by Date", width=15, command=date).grid(column=0, row=1, pady=10, padx=10)
    Tkinter.Button(rootwindow, text="Analyse by Practice", width=15, command=GP).grid(column=1, row=1, pady=10, padx=10)
    rootwindow.mainloop()

if test==False:
    #saves name and id (id for searching, name for dispalying/putting title on graph)
    ccg_id, ccg_name=ccg_select()
    bnf_id,bnf_name=drug_select()
    print("Collecting Data about {} (BNF - {}) in {}".format(bnf_name, bnf_id, ccg_name))
    #gets json of drug code for that ccg
    request="https://openprescribing.net/api/1.0/spending_by_practice/?format=json&code={}&org={}".format(bnf_id, ccg_id)
    json_obj=restrequest(request)
    
elif test==True:
    if not os.path.exists(os.path.join(os.getcwd(),"Test","Test_Data","Prescription_data.json")):
        print("Test data not found")
        print("Please place 'Prescription_data.json' in {}".format(os.path.join(os.getcwd(),"Test","Test_Data")))
        close()
    else:
        print("Loading test data 'Prescription_data.json'")
        with open(os.path.join(os.getcwd(),"Test", "Test_Data","Prescription_data.json"), "rt") as jsonf:
            json_obj=json.load(jsonf)
        ccg_id="14L"
        ccg_name="Manchester"
        bnf_id="5.1"
        bnf_name="Antibacterial Drugs"
data_dict={}
practice_dict={}
#stores in dict of {"PRACTICE1":{"DATE1":{"Items_Prescribed":"Number1"}, "DATE2:{"Items_Prescribed":"Number2"}....}, "PRACTICE2":{"DATE1":{"Items_Prescribed":"Number1"}, "DATE2:{"Items_Prescribed":"Number2"}....}....}
#ZEROS DO NOT APPEAR IN THE JSON DATA
for entry in json_obj:
    if entry["row_name"] not in practice_dict.keys():
        practice_dict[entry["row_name"]]=entry["row_id"]
    if entry["row_name"] not in data_dict.keys():
        data_dict[entry["row_name"]]={}
    if entry["date"] not in data_dict[entry["row_name"]]:
        data_dict[entry["row_name"]][entry["date"]]={}
    data_dict[entry["row_name"]][entry["date"]]["Items_Prescribed"]=entry["items"]

#gets population data NOTE - Population is total, not Star-pu adjusted as Star-pu is stored in way that will be very tricky
#to get correct values (as this script will be general for all drugs could pick wrong star-pu so total pop is safer
#Adds population data and calculates Prescription per 100 patients and adds it to {"PRACTICE1":{"DATE1":...}} entry so now it's
#{"PRACTICE1":{"DATE1":{"Items_Prescribed":Number1", "Population":"Pop Number", "Rate":"Rate Number"}....}}
if test==False:
    request="https://openprescribing.net/api/1.0/org_details/?format=json&org_type=practice&org={}&keys=total_list_size".format(ccg_id)
    json_obj=restrequest(request)
if test==True:
    if not os.path.exists(os.path.join(os.getcwd(),"Test", "Test_Data","Size_data.json")):
        print("Test data not found")
        print("Please place 'Size_data.json' in {}".format(os.path.join(os.getcwd(),"Test", "Test_Data")))
        close()
    else:
        print("Loading test data 'Size_data.json'")
        with open(os.path.join(os.getcwd(),"Test", "Test_Data","Size_data.json"), "rt") as jsonf:
            json_obj=json.load(jsonf)
zero_values={}
for entry in json_obj:
    try:
        data_dict[entry["row_name"]][entry["date"]]["Population"]=entry["total_list_size"]
        data_dict[entry["row_name"]][entry["date"]]["Rate"]=(data_dict[entry["row_name"]][entry["date"]]["Items_Prescribed"]/data_dict[entry["row_name"]][entry["date"]]["Population"])*100
    #There are 10 entires (for Manchester Antibacterials) with 0 prescriptions (so not in API and so not in dict
    #but populations Currently these get ignored and added to text file, ?should the presecriptions be added as 0
    except KeyError:
        if entry["row_name"] not in zero_values.keys():
            zero_values[entry["row_name"]]=[]
        zero_values[entry["row_name"]]+=[entry["date"]]     
if len(zero_values.keys())!=0:
    zero_text=open("Zero_Prescriptions.txt","wt")
    zero_text.write("The Following Practices had 0 Prescriptions reported but had population data and so were excluded\n")
    for key, value in zero_values.items():
        zero_text.write("{}\n".format(key))
        for date in value:
           zero_text.write("{}\n".format(date)) 
    zero_text.close()

zero_pop={}
to_del={}
#removes data that is not complete and writes the GP/date to a file (seperate to_del dict used as can't delete
#items within the loop as it gives error as loop object size is changed during iteration)
for GP, dicts in data_dict.items():
    for date, values in data_dict[GP].items():
        if len(values)!=3:
            if GP not in zero_pop.keys():
                zero_pop[GP]=[]
            zero_pop[GP]+=[date]
            if GP not in to_del.keys():
                to_del[GP]=[]
            to_del[GP]+=[date]
    
for GP,dates in to_del.items():
    for date in dates:
        del(data_dict[GP][date])
    
if len(zero_pop.keys())!=0:
    zero_text=open("Zero_Population.txt","wt")
    zero_text.write("The Following Practices had 0 reported population but had prescription data and so were excluded\n")
    for key, value in zero_pop.items():
        zero_text.write("{}\n".format(key))
        for date in value:
           zero_text.write("{}\n".format(date)) 
    zero_text.close()  


#Button selector to run either the stats or trends function
rootwindow = Tkinter.Tk()
rootwindow.title("Select Function")
rootwindow.attributes("-topmost",True)
print("Select Function")
Tkinter.Label(rootwindow, text="Select Function").grid(column=0, row=0, columnspan=2, padx=10, pady=5)
Tkinter.Button(rootwindow, text="Trend Analysis", width=15, command=trends).grid(column=0, row=1, pady=10, padx=10)
Tkinter.Button(rootwindow, text="Statistical Analysis", width=15, command=stats).grid(column=1, row=1, pady=10, padx=10)
rootwindow.mainloop()

