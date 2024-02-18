import numpy as np
import pandas as pd
import streamlit as st
from streamlit_cropperjs import st_cropperjs
import easyocr
import os
from streamlit_option_menu import option_menu
from datetime import datetime
import json
import time
import shutil
import cv2
import ast

# Set initial session values 
if 'processed_index' not in st.session_state:
    st.session_state['processed_index'] = 0
if 'now' not in st.session_state:    
    st.session_state['now'] = datetime.now()
if 'button_disabled' not in st.session_state:
    st.session_state.button_disabled = False

# Load settings
# set input and output folders
input_folder = ""
output_folder = ""
csv_folder = ""
processed_folder = ""
validated_prefix = ""

# Read settings file with input, output, processing folders
settingsFile = open('settings.json',"r")
settings=json.load(settingsFile)

# Closing file
settingsFile.close()

# Reading setting values and checking if folders exist and create in case they do not access
def check_settings_directories(settings):
    if not os.path.exists(input_folder):
        os.makedirs(input_folder)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    if not os.path.exists(processed_folder):
        os.makedirs(processed_folder)

# read settings json values
input_folder = settings["Input"]
output_folder= settings["Output"]
processed_folder= settings["Processed"]
validated_prefix = settings["Validated_Prefix"]
supported_image_types = settings["Supported Image Types"]

# check all directories
check_settings_directories(settings)



# OCR fuction 
def ocr(image_path, image_name):
    reader = easyocr.Reader(['de'], gpu=False)
    ocr_results = reader.readtext(image_path)
    dfOCRResults = pd.DataFrame(ocr_results, columns=['bbox', 'Namen', 'Confidence Level'])
    dfOCRResults['Bildname'] = image_name

    return dfOCRResults


def names_on_image(dfnames, image):

    listnames=dfnames[['Namen','bbox']].values.tolist()

    for (Namen, bbox) in listnames:

        if (len(Namen)>0 and len(bbox)>0):

            bbox=bbox.replace("[[","(")
            bbox=bbox.replace("]]",")")
            bbox=bbox.replace("[","(")
            bbox=bbox.replace("]",")")

            bbox_tuple=ast.literal_eval(bbox)

            (tl, tr, br, bl) = bbox_tuple
            br_text = (br[0] + 20, br[1] + 50)

            # Draw the bounding box on the image
            try:
                cv2.rectangle(image, tl, br, (229, 83, 0), 5)
                cv2.putText(image, Namen, br_text, cv2.FONT_HERSHEY_SIMPLEX, 2, (229, 83, 0), 10)
            except:
                st.toast("Rechteck oder Namen können auf dem Bild nicht richtig dargestellt werden")
    
    return image
# Use the full page instead of a narrow central column
st.set_page_config(layout="wide")
st.markdown("`©️ Johann Bechtold, nicht für den kommerziellen Gebrauch gedacht. Bitte kontaktiere johann.bechtold@gmail.com für eine kommerzielle Lizenz`")

#Title, Header and Sidebar
logo_url = "https://deutsche-giganetz.de/images/dgn/corporate/branding/wort-bildmarke/DGN_Wort-Bildmarke_rgb.svg"
#st.title('DGN Dizitizer')
#st.divider()
st.sidebar.image(logo_url)
with st.sidebar:
    st.write("##")
    selected = option_menu("Menu", ["OCR", "Validierung", "Settings"], 
        icons=["robot",'keyboard', 'gear'], default_index=1, styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "black", "font-size": "20px"}, 
        "nav-link": {"font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "DarkOrange"},
    })

if selected=="OCR":
    conOCR = st.container(border=True)
    ocr_input_option = conOCR.radio("OCR Option",['Verzeichnis','Einzelnes Bild'],horizontal=True)
    
    # And within an expander
    if ocr_input_option == "Verzeichnis":
        my_expander_folders = conOCR.expander("Verzeichnisse", expanded=True)
        with my_expander_folders:
            st.write("Input Verzeichnis:", input_folder)
            st.write("Output Verzeichnis:",output_folder)
        # And within an expander
        my_expander_image = conOCR.expander("Bild auswählen", expanded=False)
        with my_expander_image:
        #Image uploader and saver
            input_image=st.file_uploader(label='Wähle hier das einzelne Bild für die Erkennung',type=['png','jpeg','jpg'],)
            if input_image:
                pic = input_image.read()
                cropped_pic = st_cropperjs(pic=pic, btn_text="Bildauschnitt festlegen", key="foo")
                if cropped_pic:
                    st.image(cropped_pic, output_format="PNG")
                    st.button("Bild sichern",help="Speiche das Bild im Input Verzeichnis")
    else:
        my_expander_folders = conOCR.expander("Verzeichnisse", expanded=False)
        with my_expander_folders:
            st.write("Input Verzeichnis:", input_folder)
            st.write("Output Verzeichnis:",output_folder)
            # And within an expander
        my_expander_image = conOCR.expander("Bild auswählen", expanded=True)
        with my_expander_image:
        #Image uploader and saver
            input_image=st.file_uploader(label='Wähle hier das einzelne Bild für die Erkennung',type=['png','jpeg','jpg'],)
            if input_image:
                pic = input_image.read()
                cropped_pic = st_cropperjs(pic=pic, btn_text="Bildauschnitt festlegen", key="foo")
                if cropped_pic:
                    st.image(cropped_pic, output_format="PNG")
                    if st.button("Bild sichern",help="Speiche das Bild im Input Verzeichnis"):
    
                        while True:
                                try:
                                    with open(os.path.join(input_folder,input_image.name),"wb") as f: 
                                        f.write(cropped_pic)
                                    break
                                except:
                                    if os.path.isdir (input_folder) == False:
                                        os.mkdir(input_folder)
                                        with open(os.path.join(input_folder,input_image.name),"wb") as f: 
                                            f.write(cropped_pic)         
                        st.success(str(input_image.name) +' hochgeladen')
                single_file_name = input_folder + input_image.name
    
    conOCR.write("##")
    colOCRButton, colProgress = conOCR.columns((1,4))
    if colOCRButton.button("OCR starten",help="Starte die Texterkennung mit dem ausgewählten Input"):
        if ocr_input_option=='Verzeichnis':

            filesInInputFolder = os.listdir(input_folder)

            
            progress_text = "OCR läuft"
            progressbar_ocr = colProgress.progress(0, text=progress_text)
            if len(filesInInputFolder) > 0:
                progressbar_step = (1/len(filesInInputFolder))
            iteration = 1

            for image in filesInInputFolder:

                #replace all define image types in settings

                image_name = image

                for image_type in supported_image_types:
                    image_name = image_name.replace(image_type, "")

                #image_name=image
                #image_name = image.replace(".jpeg", "")
                #image_name = image.replace(".png", "")
                #image_name = image.replace(".jpg", "")

                st.toast(image_name)

                image_input_path = input_folder + image
                image_processed_path = processed_folder + image
                csv_path = output_folder + image_name + ".csv"
                dfImage = ocr(image_input_path, image_name)
                dfImage.to_csv(path_or_buf=csv_path)

                # Move file from input to processed folder
                shutil.move(image_input_path, image_processed_path)

                progress=progressbar_step*iteration
                progressbar_ocr.progress(progress, text=progress_text)
                iteration+=1
            
            # successful execution of OCR
            st.toast('OCR erfolgreich durchgeführt, bitte output Verzeichnis prüfen.')
            time.sleep(5)
            progressbar_ocr.empty()


        elif ocr_input_option=='Einzelnes Bild':

            if len(single_file_name) > 0:
                progress_text = "OCR läuft"
                progressbar_ocr = colProgress.progress(0, text=progress_text)

                image_input_path = input_folder + input_image.name
                image_processed_path = processed_folder + input_image.name
                csv_path = output_folder + input_image.name.split(".")[0] + ".csv"
                dfImage = ocr(single_file_name, input_image.name.split(".")[0])
                dfImage.to_csv(path_or_buf=csv_path)

                # Move file from input to processed folder
                shutil.move(image_input_path, image_processed_path)
                progressbar_ocr.progress(100, text=progress_text)
                time.sleep(5)
                progressbar_ocr.empty()

            # successful execution of OCR
            st.toast('OCR erfolgreich durchgeführt, bitte output Verzeichnis prüfen.')              

elif selected=="Validierung":
    
    # Generell zwei Spalten Layout
    st.subheader("Bilder")
    conValidation = st.container(border=True)
    colVal1,colVal2 = conValidation.columns((2,1))

    expander_images = colVal1.expander("Liste der Bilder", expanded=True)
    with expander_images:
    # image picker
        filesInFolders = os.listdir(processed_folder)
        dffilesInFolders = pd.DataFrame(filesInFolders,columns=['Datei'])
        dffilesInFolders["Name"]=dffilesInFolders["Datei"].str.split(".").str[0]
        dffilesInFolders["Typ"]=dffilesInFolders["Datei"].str.rsplit(".").str[-1]
        st.dataframe(dffilesInFolders["Name"],use_container_width=100)
    
    colVal2Button1, colVal2Button2 = colVal2.columns((2))
    if colVal2Button1.button("Zurück",use_container_width=15):
        if st.session_state['processed_index'] > 0:
            st.session_state['processed_index'] = st.session_state['processed_index'] - 1
        elif st.session_state['processed_index'] == 0:
            st.session_state['processed_index'] = 0
            st.toast("Anfang der Liste erreicht")
        else:
            st.session_state['processed_index'] = st.session_state['processed_index'] + 1
    if colVal2Button2.button("Vor",use_container_width=15):
        if st.session_state['processed_index'] == (len(dffilesInFolders) - 1):
            st.session_state['processed_index'] = (len(dffilesInFolders) - 1)
            st.toast("Ende der Liste erreicht")
        else:
            st.session_state['processed_index']=st.session_state['processed_index'] + 1 

    #st.write(len(dffilesInFolders))
    # two column layout
    colImages, colNames = st.columns((2))
    colImages.subheader("Ausgewähltes Bild")
    conImages=colImages.container(border=True)

    # Get Names Data Frame
    if len(filesInFolders) > 0:
        csv_name = output_folder + filesInFolders[st.session_state['processed_index']].split(".")[0] + ".csv"
        dfNames = pd.read_csv(csv_name)

        # Get Image and enrich with rectagle and Name on image
        image = cv2.imread(processed_folder + filesInFolders[st.session_state['processed_index']])
        image_show = names_on_image(dfNames, image)
        conImages.image(image_show)
        conImages.caption(filesInFolders[st.session_state['processed_index']])
    
        #conImages.image(processed_folder + filesInFolders[st.session_state['processed_index']], caption=filesInFolders[st.session_state['processed_index']])

        colNames.subheader("Namen")
        conNames=colNames.container(border=True)


        # conNames.write(csv_name)
        
        # transform capitalize words, e.g. first latter as capital folowing as lower case
        dfNames['Namen'] = dfNames['Namen'].str.capitalize()


        dfFinal=conNames.data_editor(data=dfNames[['Namen','Confidence Level']], num_rows='dynamic')

        if conNames.button("Validiert"):
            dfFinal.to_csv(output_folder + validated_prefix,index=False)
    
    else:
        st.toast("Keine Bilder im processed Verzeichnis für die Validierung")

elif selected=="Spende":
    st.write("##")
    donation=st.number_input(label='Spendenbeitrag', min_value=10)
    if st.button("Spende an Johann 🙃 😤 "):
        if donation < 15:
            st.toast('Oh wow: ' + str(donation) + '€, lieb von dir!',icon='😘')
        else: 
            st.toast('Das ist stark, Mensch ' + str(donation) + '€, sehr sehr lieb von dir!',icon='😘')
            st.balloons()

elif selected=="Dynamics":
    st.write("##")
    agree = st.checkbox('Ist es schwer Checkboxen zu nutzen?')

    if agree:
        st.toast('Ne du, komm schon du kannst es auch. Ich glaube an dich 💪')

elif selected=="Settings":
    st.write("##")  
    st.subheader("Verzeichnisse")

    colFolders, colSpace, colDescription = st.columns((6,1,4))

    user_input_input_folder = colFolders.text_input("Input", value=input_folder)
    user_input_output_folder = colFolders.text_input("Output", value=output_folder)
    user_input_processed_folder = colFolders.text_input("Processed", value=processed_folder)
    user_validated_prefix = colFolders.text_input("Validated File Prefix", value=validated_prefix)

    colDescription.caption("Verzeichnisse für den Prozess. Input für die Bilddateien. \
                 Im Output Verzeichnis landen die CSV Datein mit den Namen\
                 im Processed die prozessierten Bilddateien")
    
    st.write("##")
    if st.button("Settings speichern"):

        settingsFile = open('settings.json',"r")
        settings=json.load(settingsFile)

        # Open the JSON file for reading
        settings["Input"] = user_input_input_folder
        settings["Output"] = user_input_output_folder
        settings["Processed"] = user_input_processed_folder
        settings["Validated_Prefix"] = user_validated_prefix

        check_settings_directories(settings)

        # Write the updated data back to the JSON file
        with open('settings.json', 'w') as settingsFile:
            json.dump(settings, settingsFile)
        
         # Closing file
        settingsFile.close()