#!/usr/bin/env python
# coding: utf-8

# In[3]:



import zipfile
import os
from os import error, walk


from bs4 import BeautifulSoup
import re

# from IPython.display import Image as Image_display
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# get_ipython().run_line_magic('matplotlib', 'inline')

from urllib.parse import unquote

import cv2
import pytesseract

from PIL import Image

import json
import io

# Mention the installed location of Tesseract-OCR in your system
pytesseract.pytesseract.tesseract_cmd = "C:/Program Files/Tesseract-OCR/tesseract.exe"


# # Extracting Epub files to folders

# In[4]:


# Converting Epub books to folders containing HTML

# folder path of epub books you want to extract images from
epub_folder = "./data/e_pathshala_epub_debug/"


for root, dirs, files in os.walk(epub_folder):
    for file in files:
        if file.endswith(".epub"):
            folder_name = root+"/"+file[:-5]
            file_name = root+"/"+file
            # print(folder_name)
            # print(file_name)
            if os.path.isdir(folder_name):
                print("  Already extracted : "+folder_name)
            else:
                print("  Extracting to : "+folder_name)
                with zipfile.ZipFile(file_name, 'r') as zip_ref:
                    zip_ref.extractall(folder_name)


# # Loading all textbooks path as html file paths

# In[5]:



classes_folders = []
classes_folders_path = "./data/e_pathshala_epub_debug"
extensions_list = []

for file in os.listdir(classes_folders_path):
    d = os.path.join(classes_folders_path, file).replace("\\","/")
    if os.path.isdir(d):
        classes_folders.append(d)

print(f"number of classes_folders = {len(classes_folders)}")
for classes_folder in classes_folders:
    print(classes_folder)

textbooks_html_files = []
for classes_folder in classes_folders:
    for file in os.listdir(classes_folder):
        d = os.path.join(classes_folder, file).replace("\\","/")
        if os.path.isdir(d):
            html_files = os.listdir(d+"/OEBPS/Text/")
            html_files_path = []
            for html in html_files:
                html_files_path.append(d+"/OEBPS/Text/"+html)
            largest_html_file = max(html_files_path, key=os.path.getsize)
            textbooks_html_files.append(largest_html_file)
            extension = largest_html_file.split(".")[-1]
            if extension not in extensions_list:
                extensions_list.append(extension)

extension_file = open("extension_list.txt", "w")
extension_file.write(str(extensions_list))
extension_file.close()


print(f"number of textbooks_folders = {len(textbooks_html_files)}")
for html in textbooks_html_files:
    print(html)


# # Google vision api to detect text from image

# In[27]:


def detect_text(path):
    """Detects text in the file."""
    from google.cloud import vision
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="./googleapi_key/micro-answer-336515-152e5dd6b508.json"
    client = vision.ImageAnnotatorClient()
    
    with io.open(path, 'rb') as image_file:
        content = image_file.read()
    
    image = vision.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    
    ocr_full_txt_path = path.split("/OEBPS/Images/")[0]+"/OEBPS/Images/"+path.split("/OEBPS/Images/")[1].split(".")[0]+"_full.txt"
    ocr_full_txt_file = open(ocr_full_txt_path, "w")
    print(ocr_full_txt_path)
    ocr_full_txt_file.write(str(response))
    ocr_full_txt_file.close()

    ocr_dict = {"description" : [], "bounding_poly" : []}
    for text in texts:
        ocr_dict["description"].append(text.description)
        vertices_list = []
        for vertex in text.bounding_poly.vertices:
            vertices_list.append((vertex.x,vertex.y))
        ocr_dict["bounding_poly"].append(vertices_list)
    
    ocr_json = json.dumps(ocr_dict)
    ocr_json_path = path.split("/OEBPS/Images/")[0]+"/OEBPS/Images/"+path.split("/OEBPS/Images/")[1].split(".")[0]+".json"
    ocr_json_file = open(ocr_json_path, "w")
    print(ocr_json_path)
    ocr_json_file.write(ocr_json)
    ocr_json_file.close()
       
    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))

    return ocr_dict


def detect_document(path):
    """Detects document features in an image."""
    from google.cloud import vision

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="./googleapi_key/micro-answer-336515-152e5dd6b508.json"
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.Image(content=content)

    response = client.document_text_detection(image=image)
    ocr_dict = {"block": [],"bounding_poly": []}
    for page in response.full_text_annotation.pages:
        for block in page.blocks:
            # print('\nBlock confidence: {}\n'.format(block.confidence))
            block_vertices = []
            for vertex in block.bounding_box.vertices:
                block_vertices.append((vertex.x,vertex.y))
                
            # print('\nBlock bounding box: {}\n'.format(block_vertices))
            
            block_dict = {"text":"","paragraph": [],"bounding_poly": []}
            for paragraph in block.paragraphs:
                # print('Paragraph confidence: {}'.format(paragraph.confidence))
                paragraph_vertices = []
                for vertex in paragraph.bounding_box.vertices:
                    paragraph_vertices.append((vertex.x,vertex.y))
                # print('\nParagraph bounding box: {}\n'.format(paragraph_vertices))
                
                para_dict = {"text":"", "word": [], "bounding_poly": []}
                for word in paragraph.words:
                    word_text = ''.join([
                        symbol.text for symbol in word.symbols
                    ])
                    # print('Word text: {} (confidence: {})'.format(word_text, word.confidence))
                   

                    word_vertices = []
                    for vertex in word.bounding_box.vertices:
                        word_vertices.append((vertex.x,vertex.y))

                    if para_dict["text"] == "":
                        para_dict["text"] = word_text
                    else:
                        para_dict["text"] = para_dict["text"] +" "+ word_text
                        
                    para_dict["word"].append(word_text)
                    para_dict["bounding_poly"].append(word_vertices)
                if block_dict["text"] == "":
                    block_dict["text"] =  para_dict["text"]
                else:
                    block_dict["text"] = block_dict["text"] +" "+ para_dict["text"]
                block_dict["paragraph"].append(para_dict)
                block_dict["bounding_poly"].append(paragraph_vertices)
            ocr_dict["block"].append(block_dict)
            ocr_dict["bounding_poly"].append(block_vertices)
            
    ocr_full_txt_path = path.split("/OEBPS/Images/")[0]+"/OEBPS/Images/"+path.split("/OEBPS/Images/")[1].split(".")[0]+"_full.txt"
    ocr_full_txt_file = open(ocr_full_txt_path, "w")
    print(ocr_full_txt_path)
    ocr_full_txt_file.write(str(response))
    ocr_full_txt_file.close()

    ocr_json = json.dumps(ocr_dict)
    ocr_json_path = path.split("/OEBPS/Images/")[0]+"/OEBPS/Images/"+path.split("/OEBPS/Images/")[1].split(".")[0]+".json"
    ocr_json_file = open(ocr_json_path, "w")
    print(ocr_json_path)
    ocr_json_file.write(ocr_json)
    ocr_json_file.close()

    if response.error.message:
        raise Exception(
            '{}\nFor more info on error messages, check: '
            'https://cloud.google.com/apis/design/errors'.format(
                response.error.message))
    return ocr_dict


# # Extracting captions and corresponding image 

# In[29]:



def remove_non_ascii(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])


for filename in textbooks_html_files:
    try:
        fp = open(filename, encoding="utf8")
        print("++++++++++++++++++++++++++++   START   +++++++++++++++++++++")
        print(filename)
    except:
        print("***************  Error while opening file   ***************")
        print(filename)
        print("************************************************************")
    extension = filename.split(".")[-1]
    if extension == "xhtml":
        try:
            print("@@@@@@@@@@@@   XML parser @@@@@@@@@@@@")
            soup = BeautifulSoup(fp, 'lxml-xml')
        except Exception as e:
            print(" ^^^^^^^^^^^ Error while html parsing ^^^^^^^^^^^^^^^^^^^")
            print(e)
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

    elif extension == "html":
        try:
            print("@@@@@@@@@@@@   HTML parser @@@@@@@@@@@@")
            soup = BeautifulSoup(fp, 'lxml')
        except Exception as e:
            print(" ^^^^^^^^^^^ Error while html parsing ^^^^^^^^^^^^^^^^^^^")
            print(e)
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

    all_fig = soup.find_all(string=re.compile("^Fig"))
    i = 1
    max_caption_words = 60
    min_caption_words = 6
    
    def extract_lastfig(txt):
        txt = remove_non_ascii(txt).strip().replace("\n"," ")
        last_index = [_.start() for _ in re.finditer(r"Fig", txt)][-1]
        return txt[last_index:]

    for fig in all_fig:
        print("------- fig  "+str(i)+"   --------")
        
        caption_parent_text = extract_lastfig(fig.parent.parent.get_text())
        caption_grandparent_text = extract_lastfig(fig.parent.parent.parent.get_text())
        fig_text = extract_lastfig(fig)

        if len(fig_text.split()) >= max_caption_words:
            continue
        elif len(fig_text.split()) >= min_caption_words:
            print(f"fig\nlength = {len(fig.split())}")
            print(fig_text)
        elif len(caption_parent_text.split()) >= max_caption_words:
            print(f"fig\nlength = {len(fig.split())}")
            print(fig_text)
        elif len(caption_grandparent_text.split()) >= max_caption_words:
            print(f" fig + parent\n length = {len(caption_parent_text.split())}")
            print(caption_parent_text)
        else:
            print( f"fig + grandparent \nlength = {len(caption_grandparent_text.split())}")
            print(caption_grandparent_text)

        same_el_img = fig.parent.find_all("img")
        prev_img = fig.parent.find_previous("img")

        def get_image_path(html_path,img_src): # get image path from (html path) and (image path in html file)
            oebps_path = html_path.split("/Text/")[0]
            img_src = img_src[2:]
            return unquote(oebps_path+img_src)

        def convert_trans_to_white_bg(trans_image_path): # change background from transparent to white background
            im_test = Image.open(trans_image_path)
            
            fill_color = (255,255,255)  # white background color

            im_test = im_test.convert("RGBA")   # it had mode P after DL it from OP
            if im_test.mode in ('RGBA', 'LA'):
                background = Image.new(im_test.mode[:-1], im_test.size, fill_color)
                background.paste(im_test, im_test.split()[-1]) # omit transparency
                im_test = background
            white_image_path = trans_image_path[:-4] + "_white.png"
            im_test.convert("RGB").save(white_image_path)
            return white_image_path

        if same_el_img == []:
            if prev_img == None:
                print("No image found")
            else:
                image_path = get_image_path(filename,prev_img["src"])
                # image_path = convert_trans_to_white_bg(image_path)
                print("previous image = "+ image_path)
        else:
            image_path = get_image_path(filename,same_el_img[-1]["src"])
            # image_path = convert_trans_to_white_bg(image_path)
            print("same tag image = "+ image_path)

        # ocr_full_txt_path = image_path.split("/OEBPS/Images/")[0]+"/OEBPS/Images/"+image_path.split("/OEBPS/Images/")[1].split(".")[0]+"_full.txt"
        ocr_json_path = image_path.split("/OEBPS/Images/")[0]+"/OEBPS/Images/"+image_path.split("/OEBPS/Images/")[1].split(".")[0]+".json"
        # plt.imshow(mpimg.imread(image_path))
        # plt.show()
        if os.path.isfile(ocr_json_path):
            print("    Json already exist :  "+ocr_json_path)
            json_file = open(ocr_json_path)
            ocr_dict = json.load(json_file)
        else:
            print("  $$$$  Calling google vision API $$$$ ")
            ocr_dict = detect_document(image_path)
        print("~~~~~~~ Labels  ~~~~~~~~")
        if len(ocr_dict["block"]) > 0:
            for i in range(0,len(ocr_dict["block"])):
                block_dict = ocr_dict["block"][i]
                print(block_dict["text"])
                # print(block_dict["text"], "  ",ocr_dict["bounding_poly"][i])
                for i in range(0,len(block_dict["paragraph"])):
                    para_dict = block_dict["paragraph"][i]
                    print("     -",para_dict["text"])
                    # print("      ",para_dict["text"],"   ",block_dict["bounding_poly"][i])
        else:
            print("  NO Labels  ")
        print("~~~~~~~~~~~~~~~~~~~~~~~~")
        # print("~~~~~~~~~~~~~~~~~  Labels  ~~~~~~~~~~~~~~~")
        # print(pytesseract.image_to_string(Image.open(image_path)).strip())
        # # detect_text(image_path)
        # print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        i = i + 1
    print("++++++++++++++++++++++++++++   END   +++++++++++++++++++++\n")


# In[26]:



# testimg1 = "./data/e_pathshala_epub_debug/class_10_science/26_5240_11/OEBPS/Images/806.png"
# testimg2 = "./data/e_pathshala_epub_debug/class_11_biology/89_5156_6/OEBPS/Images/1897.png"
# testimg3 = "./data/e_pathshala_epub_debug/class_10_science/26_5240_11/OEBPS/Images/1192.png"

# testimg4 = "./data/e_pathshala_epub_debug/class_10_science/26_5240_11/OEBPS/Images/1099.png"

# testimg5 = "./data/e_pathshala_epub_debug/class_8_science/37_5238_6/OEBPS/Images/image29.png"


# def detect_document(path):
#     """Detects document features in an image."""
#     from google.cloud import vision

#     os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="./googleapi_key/micro-answer-336515-152e5dd6b508.json"
#     client = vision.ImageAnnotatorClient()

#     with io.open(path, 'rb') as image_file:
#         content = image_file.read()

#     image = vision.Image(content=content)

#     response = client.document_text_detection(image=image)
#     ocr_dict = {"block": [],"bounding_poly": []}
#     for page in response.full_text_annotation.pages:
#         for block in page.blocks:
#             # print('\nBlock confidence: {}\n'.format(block.confidence))
#             block_vertices = []
#             for vertex in block.bounding_box.vertices:
#                 block_vertices.append((vertex.x,vertex.y))
                
#             # print('\nBlock bounding box: {}\n'.format(block_vertices))
            
#             block_dict = {"text":"","paragraph": [],"bounding_poly": []}
#             for paragraph in block.paragraphs:
#                 # print('Paragraph confidence: {}'.format(paragraph.confidence))
#                 paragraph_vertices = []
#                 for vertex in paragraph.bounding_box.vertices:
#                     paragraph_vertices.append((vertex.x,vertex.y))
#                 # print('\nParagraph bounding box: {}\n'.format(paragraph_vertices))
                
#                 para_dict = {"text":"", "word": [], "bounding_poly": []}
#                 for word in paragraph.words:
#                     word_text = ''.join([
#                         symbol.text for symbol in word.symbols
#                     ])
#                     # print('Word text: {} (confidence: {})'.format(word_text, word.confidence))
                   

#                     word_vertices = []
#                     for vertex in word.bounding_box.vertices:
#                         word_vertices.append((vertex.x,vertex.y))

#                     if para_dict["text"] == "":
#                         para_dict["text"] = word_text
#                     else:
#                         para_dict["text"] = para_dict["text"] +" "+ word_text
                        
#                     para_dict["word"].append(word_text)
#                     para_dict["bounding_poly"].append(word_vertices)
#                 if block_dict["text"] == "":
#                     block_dict["text"] =  para_dict["text"]
#                 else:
#                     block_dict["text"] = block_dict["text"] +" "+ para_dict["text"]
#                 block_dict["paragraph"].append(para_dict)
#                 block_dict["bounding_poly"].append(paragraph_vertices)
#             ocr_dict["block"].append(block_dict)
#             ocr_dict["bounding_poly"].append(block_vertices)
            
           
#     res_file = open("output_test.txt","w")
#     res_file.write(str(response))
#     res_file.close()
#     if response.error.message:
#         raise Exception(
#             '{}\nFor more info on error messages, check: '
#             'https://cloud.google.com/apis/design/errors'.format(
#                 response.error.message))
#     return ocr_dict

# if os.path.isfile("output_detect_text.json"):
#     json_file = open("output_detect_text.json")
#     ocr_dict = json.load(json_file)
#     json_file.close()
# else:
#     ocr_dict = detect_document(testimg5)
#     ocr_file = open("output_detect_text.json","w")
#     ocr_file.write(json.dumps(ocr_dict))
#     ocr_file.close()

# for i in range(0,len(ocr_dict["block"])):
#     block_dict = ocr_dict["block"][i]
#     print(block_dict["text"])
#     # print(block_dict["text"], "  ",ocr_dict["bounding_poly"][i])
#     for i in range(0,len(block_dict["paragraph"])):
#         para_dict = block_dict["paragraph"][i]
#         print("     -",para_dict["text"])
#         # print("      ",para_dict["text"],"   ",block_dict["bounding_poly"][i])

# # testimg = testimg3
# # ocr_dict = detect_text(testimg)

# # print(ocr_dict)

