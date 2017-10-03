import sqlite3
import sys
import codecs
import csv
import io
import re
import operator
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from Tkinter import *
from Tkinter import Tk
import tkMessageBox
import tkFileDialog
from tkFileDialog import askopenfilename

# Set default encoding from ASCII to UTF-8. This is hacky and should probably be avoided. 
reload(sys)
sys.setdefaultencoding('utf8')


############# DEFINING AUXILIARY FUNCTIONS FOR USE IN USER INTERACTIVE FUNCTIONS #################


# Function for fuzzy matching English input
# Implements Levenshtein distance formula via Python fuzzywuzzy library
def en_fuzzy_match(orig_input):
    #t = (language,)
    c.execute('SELECT en FROM Glossary')
    comp_output = c.fetchall()
    fuzz_match_list = []
    for i in comp_output:
        fuzz_match_list.append(i[0])
    ratio_values = []
    for i in comp_output:
        ratio = fuzz.ratio(orig_input, i[0])
        ratio_values.append(ratio)
    fuzz_match_ratio = dict(zip(fuzz_match_list, ratio_values))
    output = max(fuzz_match_ratio.iteritems(), key=operator.itemgetter(1))[0]
    return output

# Function for fuzzy matching Japanese input
# Implements Levenshtein distance formula via Python fuzzywuzzy library
def jp_fuzzy_match(orig_input):
    c.execute('SELECT ja FROM Glossary')
    comp_output = c.fetchall()
    fuzz_match_list = []
    for i in comp_output:
        fuzz_match_list.append(i[0])
    ratio_values = []
    for i in comp_output:
        ratio = fuzz.ratio(orig_input, i[0])
        ratio_values.append(ratio)
    fuzz_match_ratio = dict(zip(fuzz_match_list, ratio_values))
    output = max(fuzz_match_ratio.iteritems(), key=operator.itemgetter(1))[0]
    return output

############# DEFINING PRIMARY USER INTERACTIVE FUNCTIONS #################

# Define function for looking up Japanese term from English input
def lookup_jp(inp):
    if ".sqlite" not in currentfile:
        tkMessageBox.showwarning("File Not Found (.sqlite)", "Please select 'File' and 'Open' an existing .sqlite dictionary or 'Create' a new one.")
    while True:
        t_base = (inp.decode("utf8"),)
        if len(t_base[0]) < 1:
            break
        c.execute('SELECT ja FROM Glossary WHERE en=?', t_base)
        output = c.fetchone()
        if output is not None:
            ja_input = output[0]
            entryWidget_ja.delete(0,END)
            entryWidget_ja.insert(0, ja_input)
        else:
            try:
                output = en_fuzzy_match(t_base[0])
                if output is not None:
                    en_input = output
                    entryWidget_en.delete(0, END)
                    entryWidget_en.insert(0, en_input)
                t_base = (output,)
                c.execute('SELECT ja FROM Glossary WHERE en=?', t_base)
                ja_output = c.fetchone()
                if ja_output is not None:
                    ja_input = ja_output[0]
                    entryWidget_ja.delete(0, END)
                    entryWidget_ja.insert(0, ja_input)
                    break
            except:
                tkMessageBox.showinfo("Not Found","Term not found in City Dictionary.")
                break

# Define function for looking up English term with Japanese input
def lookup_en(inp):
    if ".sqlite" not in currentfile:
        tkMessageBox.showwarning("File Not Found (.sqlite)", "Please select 'File' and 'Open' an existing .sqlite dictionary or 'Create' a new one.")
    while True:
        t_base = (inp.decode("utf8"),)
        if len(t_base[0]) < 1:
            break
        c.execute('SELECT en FROM Glossary WHERE ja=?', t_base)
        output = c.fetchone()
        if output is not None:
            en_input = output[0]
            entryWidget_en.delete(0, END)
            entryWidget_en.insert(0, en_input)
        else:
            try:
                output = jp_fuzzy_match(t_base[0])
                if output is not None:
                    ja_input = output
                    entryWidget_ja.delete(0,END)
                    entryWidget_ja.insert(0, ja_input)
                t_base = (output,)
                c.execute('SELECT en FROM Glossary WHERE ja=?',t_base )
                en_output = c.fetchone()
                if en_output is not None:
                    en_input = en_output[0]
                    entryWidget_en.delete(0, END )
                    entryWidget_en.insert(0, en_input )
                    break
            except:
                tkMessageBox.showinfo("Not Found","Term not found in City Dictionary.")
                break

# Define function for adding new English and Japanese terms.
def add(ja_input, en_input):
    while True:
        if ".sqlite" not in currentfile:
            tkMessageBox.showwarning("File Not Found (.sqlite)", "Please select 'File' and 'Open' an existing .sqlite dictionary or 'Create' a new one.")
            break
        if len(ja_input) < 1 or len(en_input) < 1:
            tkMessageBox.showwarning("Sorry!", "No blank terms allowed.")
            break
        jpn = (ja_input.strip(),)
        eng = (en_input.strip(),)
        try:
            c.execute('''SELECT EXISTS(SELECT ja FROM Glossary WHERE ja=?)''', jpn)
        except:
            tkMessageBox.showwarning("File not found","Please open a '.sqlite' file from the file menu.")
            break
        if c.fetchone()[0] == 0:
            c.execute('''SELECT EXISTS(SELECT en FROM Glossary WHERE en=?)''', eng)
            if c.fetchone()[0] == 0:
                if tkMessageBox.askokcancel("Add term?","Are you sure about adding this term?"):
                    c.execute('''INSERT OR IGNORE INTO Glossary (ja, en)
                    VALUES ( ?, ? )''', ( ja_input.strip(), en_input.strip() ) )
                    conn.commit()
                    break
                else:
                    break
            else:
                tkMessageBox.showwarning("Duplicate","English term already in City Dictionary. Select 'update' to alter current terms.")
                break
        else:
            tkMessageBox.showwarning("Duplicate","Japanese term already in City Dictionary. Select 'update' to alter current terms.")
            break

# Define function for deleting Japanese and English term simultaneously.
def delete(ja_input,en_input):
    while True:
        if ".sqlite" not in currentfile:
            tkMessageBox.showwarning("File Not Found (.sqlite)", "Please select 'File' and 'Open' an existing .sqlite dictionary or 'Create' a new one.")
            break
        if len(ja_input) < 1 or len(en_input) < 1:
            tkMessageBox.showwarning("Sorry!", "No blank terms to delete")
            break
        jpn = (ja_input,)
        eng = (en_input,)
        c.execute('''SELECT EXISTS(SELECT ja FROM Glossary WHERE ja=?)''', jpn)
        if c.fetchone()[0] == 1:
            c.execute('''SELECT EXISTS(SELECT en FROM Glossary WHERE en=?)''', eng)
            if c.fetchone()[0] == 1:
                if tkMessageBox.askokcancel("Delete term?","Are you sure about deleting this term?"):
                    c.execute('''DELETE FROM Glossary WHERE ja=? AND en=?''', ( ja_input, en_input ) )
                    conn.commit()
                    break
                else:
                    break
            else:
                tkMessageBox.showwarning("Not found","English term not found in City Dictionary")
                break
        else:
            tkMessageBox.showwarning("Not found","Japanese term not found in City Dictionary")
            break


# Define function for viewing all terms.
def view():
    if ".sqlite" not in currentfile:
        tkMessageBox.showwarning("File Not Found (.sqlite)", "Please select 'File' and 'Open' an existing .sqlite dictionary or 'Create' a new one.")
    newwindow = Toplevel(master=root)
    img = PhotoImage(file='fukuicity.gif')
    newwindow.tk.call('wm', 'iconphoto', newwindow._w, img)
    newwindow.geometry("750x500")
    newwindow["padx"] = 30
    newwindow["pady"] = 20
    t = Listbox(newwindow, width=350, height=250)
    scrollbar = Scrollbar(newwindow)
    scrollbar.pack(side=RIGHT, fill=Y)
    c.execute('''SELECT * FROM Glossary''')
    id = 1
    for row in c:
        t.insert(END, " " + str(id) + " " + row[0] + " = " + row[1])
        id += 1
    t.pack()
    t.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=t.yview)
    newwindow.mainloop()

# Define function for opening update window.
def rename_window():
    r_window = Toplevel(master=root)
    img = PhotoImage(file='fukuicity.gif')
    r_window.tk.call('wm', 'iconphoto', r_window._w, img)
    r_window.geometry("500x170")
    r_window["padx"] = 30
    r_window["pady"] = 20

    cur_ja = StringVar()
    cur_en = StringVar()
    rev_ja = StringVar()
    rev_en = StringVar()

    curJa_Label = Label(r_window)
    curJa_Label["text"] = "Current Japanese term:"
    curJa_Label.grid(row=1,sticky=E,padx=5,column= 1)

    curJa_Entry = Entry(r_window, textvariable =cur_ja)
    curJa_Entry["width"] = 40
    curJa_Entry.grid(row=1, column= 2, columnspan=5 )

    curEn_Label = Label(r_window)
    curEn_Label["text"] = "Current English term:"
    curEn_Label.grid(row=3,sticky=E,padx=5,pady=(10, 0),column= 1)

    curEn_Entry = Entry(r_window, textvariable =cur_en)
    curEn_Entry["width"] = 40
    curEn_Entry.grid(row=3, column= 2, columnspan=5)

    revJa_Label = Label(r_window)
    revJa_Label["text"] = "Revised Japanese term:"
    revJa_Label.grid(row=2,sticky=E,padx=5,column= 1)

    revJa_Entry = Entry(r_window, textvariable =rev_ja)
    revJa_Entry["width"] = 40
    revJa_Entry.grid(row=2, column= 2, columnspan=5 )

    revEn_Label = Label(r_window)
    revEn_Label["text"] = "Revised English term:"
    revEn_Label.grid(row=4,sticky=E,padx=5,column= 1)

    revEn_Entry = Entry(r_window, textvariable =rev_en)
    revEn_Entry["width"] = 40
    revEn_Entry.grid(row=4, column= 2, columnspan=5)

    revise_ja = Button(r_window, text="Revise JP", command=lambda: update_ja(cur_ja.get(), rev_ja.get()))
    revise_ja.grid(row=5, pady=10, column= 1)

    revise_en = Button(r_window, text="Revise EN", command=lambda: update_en(cur_en.get(), rev_en.get()))
    revise_en.grid(row=5, pady=10, column= 2)
    r_window.mainloop()


# Functions for updating terms
def update_ja(cur_ja,rev_ja):
    while True:
        if ".sqlite" not in currentfile:
            tkMessageBox.showwarning("File Not Found (.sqlite)", "Please select 'File' and 'Open' an existing .sqlite dictionary or 'Create' a new one.")
            break
        if len(cur_ja) < 1 or len(rev_ja) < 1:
            tkMessageBox.showwarning("Empty term", "Sorry! No blank terms allowed.")
            break
        curja = (cur_ja,)
        c.execute('''SELECT EXISTS(SELECT ja FROM Glossary WHERE ja=?)''',curja)
        if c.fetchone()[0] == 0:
            tkMessageBox.showwarning("Not Found","Current term not found in dictionary. Please select 'Add Term' to add new terms.")
            break
        revja = (rev_ja,)
        c.execute('''SELECT EXISTS(SELECT ja FROM Glossary WHERE ja=?)''',revja)
        if c.fetchone()[0] != 0:
            tkMessageBox.showwarning("Duplicate","Revised term already in City Dictionary")
            break
        if tkMessageBox.askokcancel("Revise term?","Are you sure about revising this Japanese term?"):
            c.execute('''UPDATE Glossary SET ja=? WHERE ja=? ''', (rev_ja,cur_ja))
            conn.commit()
            break
        else:
            break


def update_en(cur_en,rev_en):
    while True:
        if ".sqlite" not in currentfile:
            tkMessageBox.showwarning("File Not Found (.sqlite)", "Please select 'File' and 'Open' an existing .sqlite dictionary or 'Create' a new one.")
            break
        if len(cur_en) < 1 or len(rev_en) < 1:
            tkMessageBox.showwarning("Empty term","Sorry! No blank terms allowed.")
            break
        curen = (cur_en,)
        c.execute('''SELECT EXISTS(SELECT en FROM Glossary WHERE en=?)''',curen)
        if c.fetchone()[0] == 0:
            tkMessageBox.showwarning("Not Found","Current term not found in dictionary. Please select 'Add Term' to add new terms.")
            break
        reven = (rev_en,)
        c.execute('''SELECT EXISTS(SELECT en FROM Glossary WHERE en=?)''',reven)
        if c.fetchone()[0] != 0:
            tkMessageBox.showwarning("Duplicate","Revised term already in City Dictionary")
            break
        if tkMessageBox.askokcancel("Revise term?","Are you sure about revising this English term?"):
            try:
                c.execute('''UPDATE Glossary SET en =? WHERE en =?''',( rev_en,cur_en ))
                conn.commit()
                break
            except:
                tkMessageBox.showwarning("File not found","Please open a '.sqlite' file from the file menu.")
                break
        else:
            break



################### SETTING UP THE MAIN GUI ######################################

row_offset = 1
root = Tk()
img = PhotoImage(file='fukuicity.gif')
root.tk.call('wm', 'iconphoto', root._w, img)
root.title("City Dictionary")
root.geometry("500x130")
root["padx"] = 30
root["pady"] = 10

ja_input = StringVar()
en_input = StringVar()

entryLabel = Label(root)
entryLabel["text"] = "Japanese term:"
entryLabel.grid(row=row_offset,sticky=E,padx=5,column= 1)

entryWidget_ja = Entry(root, textvariable =ja_input)
entryWidget_ja["width"] = 40
entryWidget_ja.grid(row=row_offset, column= 2, columnspan=5 )

entryLabel = Label(root)
entryLabel["text"] = "English term:"
entryLabel.grid(row=row_offset+1,sticky=E,padx=5,column=  1)

entryWidget_en = Entry(root, textvariable =en_input)
entryWidget_en["width"] = 40
entryWidget_en.grid(row=row_offset+1, column= 2, columnspan=5)

# Search JP
search_jp = Button(root, text="JP→EN", command=lambda: lookup_en(ja_input.get()))
search_jp.grid(row=row_offset+3,column= 1, pady=10, sticky=E)

# Search EN
search_en = Button(root, text="EN→JP", command=lambda: lookup_jp(en_input.get()))
search_en.grid(row=row_offset+3,column= 2, sticky=W)

# View Terms
view_terms = Button(root, text="View All", command= view)
view_terms.grid(row=row_offset+3, column = 3)

# Add Term
add_term = Button(root, text="Add Term", command= lambda: add(ja_input.get(), en_input.get()))
add_term.grid(row=row_offset+3, column= 4)

# Update Terms
update_term = Button(root, text="Update", command= rename_window)
update_term.grid(row=row_offset+3, column= 5)

# Delete Terms
delete_term = Button(root, text="Delete", command= lambda: delete(ja_input.get(), en_input.get()))
delete_term.grid(row=row_offset+3, column= 6)

# Create the menu bar
menubar = Menu(root)


################################ FILE MENU FUNCTIONS ########################################################

# For opening files. Checks to make sure it's an sqlite file
def opensql():
    filename = askopenfilename()
    global currentfile
    currentfile = filename
    global c
    global conn
    if ".sqlite" not in str(filename):
        tkMessageBox.showwarning("Wrong file type", "Dictionary requires '.sqlite' files.")
    else:
        with io.open('cddirectory.xml','w') as f:
            f.write(filename)
        conn = sqlite3.connect(filename)
        c = conn.cursor()
        conn.text_factory = str


# For setting up a new sqlite based dictionary if one is deleted or does not already exist
def buildsql():
    raw_file = tkFileDialog.asksaveasfile(mode='w', defaultextension=".sqlite")
    if raw_file is None: # asksaveasfile return `None` if dialog closed with "cancel".
        return
    if ".sqlite" not in str(raw_file):
       tkMessageBox.showwarning("Wrong file type", "Dictionary requires '.sqlite' files.")
    fstr = str(raw_file)
    fstrlst = fstr.split("'")
    f = fstrlst[1]
    conn = sqlite3.connect(f)
    c = conn.cursor()
    c.execute('''CREATE TABLE Glossary
             (ja text, en text)''')
    conn.text_factory = str

def importcsv():
    csvfile = csv.reader(codecs.open('test.csv', 'rU'))
    for line in csvfile:
        array = line.split(',')
        first_item = array[0]

        num_columns = len(array)
        csvfile.seek(0)

        reader = csv.reader(csvfile, delimiter=',')
        included_cols = [0]

        for row in reader:
            content = list(row[i] for i in included_cols)
        print content[0].decode("Shift-JIS")

    csvfile.close()
				     
				     
# Below is an attempt to design a function that imports the contents of a .csv
# file into the opened sqlite dictionary file. This implementation throws back
# an error when encountering an empty cell. 

"""
    with open('test.csv', 'rb') as csvfile:
        # get number of columns
        for line in csvfile.readlines():
            array = line.split(',')
            first_item = array[0]
            num_columns = len(array)
            csvfile.seek(0)
            reader = csv.reader(csvfile, delimiter=',')
            included_cols = [0]
            for row in reader:
                content = list(row[i] for i in included_cols)
            print content[0].decode("Shift-JIS")
    csvfile.close()
"""
    #with open('test.csv', 'r') as f:
        #reader = csv.reader(f, quotechar='|')
        #print reader
        #for row in reader:
        #    print row[0]
        #jp1 = next(reader)
        #print jp1
        #c.execute('''INSERT OR IGNORE INTO Glossary (ja, en)
        #VALUES ( ?, ? )''', ( jp1, en1 ) )
        #cursor.commit()


# Defining function that opens a new window to display main GUI commands
def command_list():
	newwindow = Toplevel(master=root)
	img = PhotoImage(file='fukuicity.gif')
	newwindow.tk.call('wm', 'iconphoto', newwindow._w, img)
	T = Text(newwindow, height=20, width=100)
	T.tag_configure('big', font=('Times New Roman', 15, 'bold'))
	T.insert(END,'\nList of Commands\n', 'big')
	content ="""
JP→EN = Input 'Japanese term' and find the corresponding 'English term'
EN→JP = Input 'English term' and find the corresponding 'Japanese term'
View All = View a list of all terms in the dictionary
Add Term = Add a new term by inputting new terms into the 'Japanese term' and 'English term' boxes. Input a term into each white box.
Update = Open a new window to update existing terms. Input the 'Current term' and the 'Revised term'. Note that you can update a term in one language without updating it in the other language. Select 'Revise JP' to update a Japanese term and 'Revise EN' to update an English term.
Delete = Delete an existing term. Input the 'Japanese term' and corresponding 'English term'
	"""
	T.insert(END, content)
	T.pack()
	mainloop()

def getting_started():
	newwindow = Toplevel(master=root)
	img = PhotoImage(file='fukuicity.gif')
	newwindow.tk.call('wm', 'iconphoto', newwindow._w, img)
	T = Text(newwindow, height=40, width=75)
	T.pack()
	T.insert(END, "To be filled later")
	mainloop()

################################# SET UP TOP MENU BAR ####################

filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Open Dictionary", command=opensql)
filemenu.add_command(label="Create Dictionary", command=buildsql)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="File", menu=filemenu)

# Set up the import menu
importmenu = Menu(menubar, tearoff=0)
importmenu.add_command(label="Import Terms", command=importcsv)
menubar.add_cascade(label="Import", menu=importmenu)

# Set up the help menu
helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="List of Commands", command=command_list)
helpmenu.add_command(label="Getting Started", command=getting_started)
menubar.add_cascade(label="Help", menu=helpmenu)

# Add the entire menu bar
root.config(menu=menubar)

# Check to see if a specific .sqlite file and directory have been previously opened
try:
    global currentfile
    currentfile = open('cddirectory.xml','r').read().decode("Shift-JIS")
    conn = sqlite3.connect(currentfile)
    c = conn.cursor()
    conn.text_factory = str
except:
    opensql()


root.mainloop()
