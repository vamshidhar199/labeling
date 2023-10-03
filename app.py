import streamlit as st
import os
import io
from test import save
from PIL import Image
import boto3
from streamlit_img_label import st_img_label
from streamlit_img_label.manage import ImageManager, ImageDirManager
from xml.etree import ElementTree as ET

def remove_files(directory_path, filename_to_keep):
    for filename in os.listdir(directory_path):
        # Create absolute path
        filepath = os.path.join(directory_path, filename)
        
        # Skip the file you want to keep
        if filename == filename_to_keep or filename == filename_to_keep.replace(".jpg", ".xml"):
            continue
        
        try:
            # Check if it's a file or directory
            if os.path.isfile(filepath):
                # If it's a file, remove it
                os.remove(filepath)
            # Optional: Uncomment the below lines if you want to delete subdirectories as well
            # elif os.path.isdir(filepath):
            #     shutil.rmtree(filepath)
        except Exception as e:
            # Print an error message if unable to remove the file or directory
            print(f"Error occurred while deleting file: {filepath}. Error: {e}")

            
def fetch_image_and_save_to_folder(directory_path, image_name, save_path):
    try:
        s3_object = boto3.client("s3").get_object(Bucket="masterprojectbucket", Key=f"{directory_path}/{image_name}")
        image_bytes = s3_object["Body"].read()
        image = Image.open(io.BytesIO(image_bytes))
        image.save(os.path.join(save_path, image_name))
        print(f"Image '{image_name}' saved to '{save_path}'")
        remove_files("./img_dir",image_name)
    except Exception as e:
        print(f"Error fetching and saving image: {e}")

def run(img_dir, labels):
    print(st.experimental_get_query_params().get('image')[0])
    st.set_option("deprecation.showfileUploaderEncoding", False)
    idm = ImageDirManager(img_dir)

    if "files" not in st.session_state:
        print("inside file not in session")
        fetch_image_and_save_to_folder("ReportImages", st.experimental_get_query_params().get('image')[0], "img_dir")
        st.session_state["files"] = idm.get_all_files()
        st.session_state["annotation_files"] = idm.get_exist_annotation_files()
        st.session_state["image_index"] = 0
    else:
        idm.set_all_files(idm.get_all_files())
        idm.set_annotation_files(st.session_state["annotation_files"])
    
    def refresh():
        st.session_state["files"] = idm.get_all_files()
        st.session_state["annotation_files"] = idm.get_exist_annotation_files()
        st.session_state["image_index"] = 0
    
    # def get_image_from_s3(directory_path, image_name):
    #     try:
    #         s3_object = boto3.client("s3").get_object(Bucket="masterprojectbucket", Key=f"{directory_path}/{image_name}")
    #         image_bytes = s3_object["Body"].read()
    #         image = Image.open(io.BytesIO(image_bytes))
    #         return image
    #     except Exception as e:
    #         st.error(f"Error retrieving image: {e}")
    #         return None

    def next_image():
        image_index = st.session_state["image_index"]
        if image_index < len(st.session_state["files"]) - 1:
            st.session_state["image_index"] += 1
        else:
            st.warning('This is the last image.')

    def previous_image():
        image_index = st.session_state["image_index"]
        if image_index > 0:
            st.session_state["image_index"] -= 1
        else:
            st.warning('This is the first image.')

    def next_annotate_file():
        image_index = st.session_state["image_index"]
        next_image_index = idm.get_next_annotation_image(image_index)
        if next_image_index:
            st.session_state["image_index"] = idm.get_next_annotation_image(image_index)
        else:
            st.warning("All images are annotated.")
            next_image()
    
    def xml_to_yolo(xml_string, class_mapping):
        yolo_annotations = ""
        
        root = ET.fromstring(xml_string)
        image_width = float(root.find('./size/width').text)
        image_height = float(root.find('./size/height').text)

        for obj in root.findall('object'):
            class_name = obj.find('name').text
            class_id = -1
            class_id = class_mapping.index(class_name)
            print(class_id)
            if class_id == -1:
                continue
            
            bndbox = obj.find('bndbox')
            xmin = float(bndbox.find('xmin').text)
            ymin = float(bndbox.find('ymin').text)
            xmax = float(bndbox.find('xmax').text)
            ymax = float(bndbox.find('ymax').text)
            
            x_center = (xmin + xmax) / (2 * image_width)
            y_center = (ymin + ymax) / (2 * image_height)
            width = (xmax - xmin) / image_width
            height = (ymax - ymin) / image_height
            
            yolo_annotations += f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n"
        
        return yolo_annotations

    def go_to_image():
        file_index = st.session_state["files"].index(st.session_state["file"])
        st.session_state["image_index"] = file_index

    # Sidebar: show status
    n_files = len(st.session_state["files"])
    n_annotate_files = len(st.session_state["annotation_files"])
    st.sidebar.write("Total files:", n_files)
    st.sidebar.write("Total annotate files:", n_annotate_files)
    st.sidebar.write("Remaining files:", n_files - n_annotate_files)

    st.sidebar.selectbox(
        "Files",
        st.session_state["files"],
        index=st.session_state["image_index"],
        on_change=go_to_image,
        key="file",
    )
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.button(label="Previous image", on_click=previous_image)
    with col2:
        st.button(label="Next image", on_click=next_image)
    st.sidebar.button(label="Next need annotate", on_click=next_annotate_file)
    st.sidebar.button(label="Refresh", on_click=refresh)

    # Main content: annotate images
    img_file_name = idm.get_image(st.session_state["image_index"])
    # img_file_name = "img003712.jpg"
    img_path = os.path.join(img_dir, img_file_name)
    im = ImageManager(img_path)
    img = im.get_img()
    resized_img = im.resizing_img()
    resized_rects = im.get_resized_rects()
    rects = st_img_label(resized_img, box_color="red", rects=resized_rects)

    def annotate():
        im.save_annotation()
        image_annotate_file_name = img_file_name.split(".")[0] + ".xml"
        if image_annotate_file_name not in st.session_state["annotation_files"]:
            st.session_state["annotation_files"].append(image_annotate_file_name)
        
        # Read the XML content from the file
        print("./img_dir/"+img_file_name.split(".")[0] + ".xml")
        with open("./img_dir/"+img_file_name.split(".")[0] + ".xml", 'r') as file:
            xml_string = file.read()
        
        # Convert the XML content to YOLO format
        yolo_annotations = xml_to_yolo(xml_string, custom_labels)
        
        #path to save yolo annotations
        output_filepath = "./img_dir/"+img_file_name.split(".")[0]+".txt"
        #print(output_filepath)
        
        # Save the YOLO annotations to the output file
        try:
            with open(output_filepath, 'w') as file:
                file.write(yolo_annotations)
                #print(f"YOLO annotations saved to: {output_filepath}")
                st.success('Annotations saved')
        except Exception as e:
            st.error('Error saving annotations')
            print(f"Error writing to {output_filepath}: {e}")
        #next_annotate_file()

    if rects:
        st.button(label="Save", on_click=annotate)
        preview_imgs = im.init_annotation(rects)

        for i, prev_img in enumerate(preview_imgs):
            prev_img[0].thumbnail((200, 200))
            col1, col2 = st.columns(2)
            with col1:
                col1.image(prev_img[0])
            with col2:
                default_index = 0
                if prev_img[1]:
                    default_index = labels.index(prev_img[1])

                select_label = col2.selectbox(
                    "Label", labels, key=f"label_{i}", index=default_index
                )
                im.set_annotation(i, select_label)

if __name__ == "__main__":
    custom_labels = ["black_core", "crack", "finger", "star_crack", "thick_line", "corner", "fragment", "scratch", "printing_error", "horizontal_dislocation", "vertical_dislocation", "short_circuit"]
    run("img_dir", custom_labels)