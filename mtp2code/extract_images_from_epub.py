
import zipfile
import os
from os import error, walk


# Converting Epub books to folders containing HTML
# ---------------------------------------------------------------------

# folder path of epub books you want to extract images from
# epub_folder = "C:/Users/gopis/Desktop/mtp2code/data/e_pathshala_epub/"


# for root, dirs, files in os.walk(epub_folder):
#     for file in files:
#         if file.endswith(".epub"):
#             folder_name = root+"/"+file[:-5]
#             file_name = root+"/"+file
#             print(folder_name)
#             print(file_name)
#             with zipfile.ZipFile(file_name, 'r') as zip_ref:
#                 zip_ref.extractall(folder_name)

# ----------------------------------------------------------------------

from bs4 import BeautifulSoup
import re

classes_folders = []
classes_folders_path = "./data/e_pathshala_epub"

for file in os.listdir(classes_folders_path):
    d = os.path.join(classes_folders_path, file).replace("\\","/")
    if os.path.isdir(d):
        classes_folders.append(d)

print(f"len of classes_folders = {len(classes_folders)}")
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

print(f"len of textbooks_folders = {len(textbooks_html_files)}")
for html in textbooks_html_files:
    print(html)



filename1 = "C:/Users/gopis/Desktop/mtp2code/data/e_pathshala_epub/class_10_science/18_5240_3/OEBPS/Text/Chapter-3.html"

filename2 = "C:/Users/gopis/Desktop/mtp2code/data/e_pathshala_epub/class_10_science/22_5240_7/OEBPS/Text/Chapter-7.html"

filename3 = "C:/Users/gopis/Desktop/mtp2code/data/e_pathshala_epub/class_9_science/5_5239_5/OEBPS/Text/Untitled-3.xhtml"

filename4 = "C:/Users/gopis/Desktop/mtp2code/data/e_pathshala_epub/class_8_science/43_5238_12/OEBPS/Text/ch12.xhtml"

filename5 = "C:/Users/gopis/Desktop/mtp2code/data/e_pathshala_epub/class_7_science/58_5237_9/OEBPS/Text/Untitled-9.xhtml"

filename_not_working = "C:/Users/gopis/Desktop/mtp2code/data/e_pathshala_epub/class_8_science/38_5238_7/OEBPS/Text/ch7.xhtml"

all_files = [filename1,filename2,filename3,filename4,filename5]

def remove_non_ascii(text):
    return ''.join([i if ord(i) < 128 else ' ' for i in text])



extensions_list = []


for filename in textbooks_html_files:
    try:
        # with open(filename, encoding="utf8") as fp:
        fp = open(filename, encoding="utf8")
        print("++++++++++++++++++++++++++++   START   +++++++++++++++++++++")
        print(filename)
    except:
        print("***************  Error while opening file   ***************")
        print(filename)
        print("************************************************************")
    extension = filename.split(".")[-1]
    if extension not in extensions_list:
        extensions_list.append(extension)
    if extension == "xhtml":
        try:
            print("@@@@@@@@@@@@   XML parser")
            soup = BeautifulSoup(fp, 'lxml-xml')
        except Exception as e:
            print(" ^^^^^^^^^^^ Error while html parsing ^^^^^^^^^^^^^^^^^^^")
            # print(filename)
            print(e)
            print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^")

    elif extension == "html":
        try:
            # soup = BeautifulSoup(fp, 'xml')
            print("@@@@@@@@@@@@   HTML parser")
            soup = BeautifulSoup(fp, 'lxml')
        except Exception as e:
            print(" ^^^^^^^^^^^ Error while html parsing ^^^^^^^^^^^^^^^^^^^")
            # print(filename)
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
        if same_el_img == []:
            if prev_img == None:
                print("No image found")
            else:
                print("previous image = "+ prev_img["src"])
        else:
            print("same tag image = "+ same_el_img[-1]["src"])
        i = i + 1
    print("++++++++++++++++++++++++++++   END   +++++++++++++++++++++\n")

extension_file = open("extension_list.txt", "w")
extension_file.write(str(extensions_list))
extension_file.close()


# for filename in all_files:
#     print("++++++++++++++++++++++++++++   START   +++++++++++++++++++++")
#     print(filename)
#     with open(filename) as fp:
#         soup = BeautifulSoup(fp, 'xml')
#         all_p = soup.find_all('p', "caption")
#         all_img = soup.find_all('img')
#         all_cap = soup.find_all(attrs={"class": "caption"})

#         i = 1
#         for el in all_cap:
#             caption = el.get_text()
#             caption = caption.replace("\n","")
#             # caption = caption.replace(" ","")
#             if caption=="":
#                 continue
#             print("  ---------------------------   "+str(i)+"  -------------------------- ")
#             print(caption)
#             print("   ")
#             same_el_img = el.find_all("img")
#             prev_img = el.find_previous("img")
#             if same_el_img == []:    
#                 print(prev_img["src"])
#             else:
#                 print(same_el_img[0]["src"])
#             print("   ")
#             i = i+1
#             print("  ******************************************************************* ")
    
#     print("++++++++++++++++++++++++++++   END   +++++++++++++++++++++\n")
