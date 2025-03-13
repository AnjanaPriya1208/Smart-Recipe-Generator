import torchvision.transforms as transforms
import os

# Importing the database connection function
import database_connection

# Set environment variables to avoid OpenMP and oneDNN conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Import libraries in a specific order
import cv2
import numpy as np
import pytesseract
import easyocr

from transformers import AutoModelForImageClassification
from PIL import Image
import torch
import openai

# Preprocessing function for image enhancement (OCR)
def preprocess_image(image):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    thresh_image = cv2.adaptiveThreshold(blurred_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY, 11, 2)
    kernel = np.ones((3, 3), np.uint8)
    processed_image = cv2.morphologyEx(thresh_image, cv2.MORPH_CLOSE, kernel)
    return processed_image

# Tesseract OCR Function
def ocr_with_tesseract(image):
    text = pytesseract.image_to_string(image)
    return text

# EasyOCR Function
def ocr_with_easyocr(image_path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path, detail=0)
    return result

# GPT API call
def ask_gpt(prompt):
    gpt_key = database_connection.get_gpt_key()
    openai.api_key = gpt_key
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
       messages=[
    {"role": "system", "content": "You are an assistant that identifies ingredients, estimates cooking time in minutes and return only numbers like 30, 20 etc, and provides only the cuisine type in a brief format (e.g., 'American cuisine'). Avoid extra descriptive text.And in procedure do not include cooking time and cuisine type"},
    {"role": "user", "content": prompt}
],
        max_tokens=150
    )
    
    return response.choices[0].message['content']

# Fruits/Vegetables detection using pre-trained model
def classify_fruit_vegetable(image):
    model = AutoModelForImageClassification.from_pretrained("jazzmacedo/fruits-and-vegetables-detector-36")
    labels = list(model.config.id2label.values())

    preprocess = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    pil_image = Image.fromarray(image)
    input_tensor = preprocess(pil_image).unsqueeze(0)
    outputs = model(input_tensor)
    predicted_idx = torch.argmax(outputs.logits, dim=1).item()
    predicted_label = labels[predicted_idx]
    return predicted_label

import io

def register_user(profile_picture, username, phone_number, email_id, password=None):
    connection = database_connection.get_db_connection()

    if not connection:
        print("Failed to connect to the database.")
        return

    try:
        cur = connection.cursor()

        # Check if the username already exists
        cur.execute('SELECT * FROM "Registration_Details" WHERE "Username" = %s', (username,))
        if cur.fetchone():
            print(f"Username '{username}' is already taken. Please choose another.")
            return

        # Convert the profile picture (UploadedFile) to a byte array
        if hasattr(profile_picture, 'read'):
            profile_picture_bytes = profile_picture.read()  # Convert the image to bytes
        else:
            print("Profile picture is not in the correct format.")
            return

        # Print to check values before insertion
        print(f"Inserting user: {username}, {phone_number}, {email_id}")

        # Insert new user details with profile picture as byte array (BYTEA)
        cur.execute(""" 
            INSERT INTO "Registration_Details" ("Profile", "Username", "Phone_Number", "Email_id", "Password") 
            VALUES (%s, %s, %s, %s, %s)
        """, (profile_picture_bytes, username, phone_number, email_id, password))

        connection.commit()
        print("User registered successfully.")
    except Exception as e:
        print(f"Database error during user registration: {e}")
    finally:
        if cur:
            cur.close()
        if connection:
            connection.close()



def login_user(username, password):
    # Connect to the database
    connection = database_connection.get_db_connection()

    if not connection:
        print("Failed to connect to the database.")
        return False

    try:
        cur = connection.cursor()

        # Query to check if the username exists
        cur.execute('SELECT "Password" FROM "Registration_Details" WHERE "Username" = %s', (username,))
        stored_password = cur.fetchone()

        # Check if the password matches
        if stored_password and stored_password[0] == password:
            print("Login successful!")
            return True  # Username and password match
        else:
            print("Invalid username or password.")
            return False  # Invalid login credentials
    except Exception as e:
        print(f"Error during login verification: {e}")
        return False
    finally:
        if cur:
            cur.close()
        if connection:
            connection.close()

# Function to insert data into Recipes_Details table
import psycopg2  # Or the appropriate database library you're using

# def insert_recipe(username, ingredients, recipe_name, cooking_time, nutritional_info, cuisine):
#     try:
#         # Establish the connection to the database
#         connection = database_connection.get_db_connection()
#         if connection:
#             cursor = connection.cursor()

#             # Prepare the SQL query to insert the recipe into the database
#             insert_query = """
#             INSERT INTO "Recipes_Details" ("Username", "Ingredients", "Recipe_Generated", "Cooking_Time", "Nutritional_Value", "Cuisine")
#             VALUES (%s, %s, %s, %s, %s, %s)
#             """
#             # Execute the query
#             cursor.execute(insert_query, (username, ', '.join(ingredients), recipe_name, cooking_time, nutritional_info, cuisine))

#             # Commit the transaction
#             connection.commit()

#             # Close the cursor and connection
#             cursor.close()
#             connection.close()
#             return True  # Indicate successful insertion
#         else:
#             print("Failed to connect to the database.")
#             return False
#     except Exception as e:
#         print(f"Error inserting recipe into the database: {e}")
#         return False
#     finally:
#         if cursor:
#             cursor.close()
#         if connection:
#             connection.close()








