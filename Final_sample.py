import streamlit as st
import base64
import numpy as np
from PIL import Image
from sample_main import register_user, login_user, preprocess_image, ocr_with_tesseract, ocr_with_easyocr, ask_gpt, classify_fruit_vegetable
import database_connection
import io

# Function to set the background image
def set_background_image(image_path):
    try:
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{encoded_image}");
                background-size: cover;
                background-attachment: fixed;
                background-position: right;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except FileNotFoundError:
        st.error("Background image file not found. Please check the path.")

# Set the background image
set_background_image("C:/Users/anjan/OneDrive/Desktop/Smart_Recipe/Smart-Recipe-Generator_oct_2024/Main Project/background/bg_1.jpg")

# CSS for animations
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
    <style>
        /* Animation for title */
        @keyframes slide-down {
            0% { transform: translateY(-50px); opacity: 0; }
            100% { transform: translateY(0); opacity: 1; }
        }
        .animated-title {
            animation: slide-down 1.5s ease-out;
            font-family: 'Playfair Display', serif;
            font-size: 3em;
            color: black;
            text-align: center;
        }

        /* Animation for subtitle */
        @keyframes fade-in {
            0% { opacity: 0; }
            100% { opacity: 1; }
        }
        .animated-subtitle {
            animation: fade-in 2s ease-in;
            font-size: 1.2em;
            text-align: center;
            margin-top: -10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Display animated title and subtitle
title = '''
Snap & Savor<br>
<span style="font-size: 0.8em;">The Smart Recipe Generator</span>
'''
st.markdown(f'<h1 class="animated-title" style="text-align: center;">{title}</h1>', unsafe_allow_html=True)

caption = '''
"Say goodbye to boring meals and hello to culinary adventures!
Simply upload a photo of what you have on hand, and let our recipe generator inspire your next feast.
Taste the excitement in every bite!"
'''
st.markdown(f'<p class="animated-subtitle">{caption}</p>', unsafe_allow_html=True)

# Initialize session state for login and registration
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Store generated recipe details in session state
if "recipe_name" not in st.session_state:
    st.session_state.recipe_name = ""
if "unique_ingredients" not in st.session_state:
    st.session_state.unique_ingredients = []
if "procedure" not in st.session_state:
    st.session_state.procedure = ""
if "nutritional_info" not in st.session_state:
    st.session_state.nutritional_info = ""
if "cooking_time" not in st.session_state:
    st.session_state.cooking_time = ""
if "cuisine" not in st.session_state:
    st.session_state.cuisine = ""

# Function to hide login/register UI after login
def show_login_register():
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.subheader("Login")
            username = st.text_input("Username:", key="login_username")
            password = st.text_input("Password:", type="password", key="login_password")
            
            if st.button("Login"):
                if login_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Welcome back, {username}!")
                    st.session_state.logged_in = True  # Force rerun to refresh and show recipe generation functionality
                else:
                    st.error("Invalid username or password")

        with tab2:
            st.subheader("Register")
            new_username = st.text_input("New Username", key="register_username")
            new_password = st.text_input("New Password", type="password", key="register_password")
            phone_number = st.text_input("Phone Number", key="register_phone")
            email_id = st.text_input("Email ID", key="register_email")
            profile_picture = st.file_uploader("Upload Profile Picture", type=["jpg", "jpeg", "png"], key="register_picture")
            
            if st.button("Register"):
                if new_username and new_password and phone_number and email_id:
                    if not register_user(profile_picture, new_username, phone_number, email_id, new_password):
                        st.success("Registration successful. Please log in.")
                    else:
                        st.error("Registration failed. Please try again.")
                else:
                    st.error("Please complete all fields: username, password, phone number, and email ID.")


import time

def is_recipe_in_database(recipe_name):
    # Placeholder function to check if recipe_name exists in the database
    connection = database_connection.get_db_connection()
    if connection:
        cur = connection.cursor()
        query = 'SELECT COUNT(*) FROM "Recipes_Details" WHERE "Recipe_Generated" LIKE %s'
        cur.execute(query, (f"%{recipe_name}%",))
        result = cur.fetchone()
        cur.close()
        connection.close()
        return result[0] > 0
    return False


def show_recipe_generation():
    if st.session_state.logged_in:
        set_background_image("C:/Users/anjan/OneDrive/Desktop/Smart_Recipe/Smart-Recipe-Generator_oct_2024/Main Project/background/dip_bg.jpg")

        col1, col2 = st.columns([7, 2])
        with col2:
            if st.button("Logout"):
                st.session_state.logged_in = False
                st.session_state.username = ""
                # Clear session state on logout
                st.session_state.recipe_name = ""
                st.session_state.unique_ingredients = []
                st.session_state.procedure = ""
                st.session_state.nutritional_info = ""
                st.session_state.cooking_time = ""
                st.session_state.cuisine = ""

        st.sidebar.title("Profile")
        # User profile information retrieval code here...
        # Fetch user profile information from the database
        user_info = None
        try:
            connection = database_connection.get_db_connection()
            if connection:
                cur = connection.cursor()

                # Query to get user details
                cur.execute('SELECT "Phone_Number", "Email_id", "Profile" FROM "Registration_Details" WHERE "Username" = %s', (st.session_state.username,))
                user_info = cur.fetchone()

                if user_info:
                    phone_number, email_id, profile_picture_bytes = user_info

                    # Check if profile_picture_bytes exists and display the image
                    if profile_picture_bytes:
                        profile_image = Image.open(io.BytesIO(profile_picture_bytes))  # Convert byte array to image
                        st.sidebar.image(profile_image, use_column_width=True)

                    # Display user profile information
                    st.sidebar.write("**Username:**", st.session_state.username)
                    st.sidebar.write("**Phone Number:**", phone_number if phone_number else "Not provided")
                    st.sidebar.write("**Email ID:**", email_id if email_id else "Not provided")

                else:
                    st.sidebar.write("No profile information found.")
        except Exception as e:
            print(f"Error fetching user profile data: {e}")
        finally:
            connection = database_connection.get_db_connection()
            cur = connection.cursor()
            if cur:
                cur.close()
            if connection:
                connection.close()
        
        st.markdown(f"Hello, {st.session_state.username}! Welcome back to the Smart Recipe Generator.")
        if st.session_state.logged_in:
            tab1, tab2 = st.tabs(["Home", "Saved Recipes"])

            with tab1:
                st.subheader("Upload images of ingredients to generate a recipe")
                # Step 1: Define the text
                st.write("**Upload crisp, individual images of fruits, vegetables, or labeled products**")
                st.write("**Avoid grouped or cluttered images for best results**")
  

                uploaded_images = st.file_uploader("Upload Ingredient Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

                # Dropdown for user preference
                preference = st.selectbox(
                    "Select your preference:",
                    ["Vegetarian", "Non-Vegetarian", "Dessert"]
                )

                # Function to generate a unique recipe
                def generate_unique_recipe():
                    # Initialize the unique recipes list in session state if not already
                    if "generated_recipes" not in st.session_state:
                        st.session_state["generated_recipes"] = set()

                    # Attempt to generate a unique recipe, with a maximum of 10 attempts
                    unique_recipe_found = False
                    attempt_count = 0

                    while not unique_recipe_found and attempt_count < 10:
                        attempt_count += 1
                        # Recipe generation prompt
                        recipe_prompt = (
                            f"Generate a unique recipe name based on the following labels or ingredients: {', '.join(st.session_state.unique_ingredients)} and preference {preference}."
                            "Do not generate random recipes. Only generate recipes using the given ingredients."
                            "Do not use the word 'recipe' at the end of the name. Generate a new recipe each time, using a different cuisine if possible."
                            "Do not add cuisine name like Italian, Thai at the end of the recipe name."
                            "Try to give different, unique, surprising names for recipes and do not use words mostly like 'delight', 'medley' and produce new procedures and do not repeat earlier recipes."
                            "If required, include extra ingredients for variety and new recipes but include the preference of Non Vegetarian, Vegetarian, Desserts which the user selects as {preference}."
                            "Do not give additional information like procedure, cuisine, preference , nutritonal information and cooking time in recipe name."
                        )
                        recipe_name = ask_gpt(recipe_prompt).strip()

                        # Check if the recipe is unique
                        if recipe_name not in st.session_state.generated_recipes:
                            st.session_state.recipe_name = recipe_name
                            st.session_state.generated_recipes.add(recipe_name)
                            unique_recipe_found = True

                            # Generate additional recipe details
                            procedure_prompt = (
                                f"Provide a step-by-step procedure in new lines for preparing the recipe '{recipe_name}' using ingredients : {', '.join(st.session_state.unique_ingredients)} and the preference {preference} of the user." 
                                "Make sure to give the {preference} item you are considering like for Non-vegetarian, give the item like chicken,Egg etc." 
                                "Do not say like add your optional non vegetarian ingredient.This goes for all preferences." 
                                "Do not give additional data like ingredients, cuisine, cooking time, preference, nutritional information in this section. "
                            )
                            st.session_state.procedure = ask_gpt(procedure_prompt).strip()

                            cooking_time_prompt = f"Estimate the cooking time for '{recipe_name}' in minutes. Return only a number."
                            st.session_state.cooking_time = ask_gpt(cooking_time_prompt).strip()

                            nutritional_info_prompt = (
                                f"Given the following recipe: '{recipe_name}', please provide the nutritional information, "
                                "including approximate values for calories, protein, fat, and carbohydrates. "
                                "List each value on a new line in grams. Format:\n"
                                "- Calories: 10g\n"
                                "- Protein: 5g \n"
                                "- Fat:3g \n"
                                "- Carbohydrates: 9g\n"
                                "Do not give additional data like procedure, ingredients, cuisine, cooking time in this section. "
                            )
                            st.session_state.nutritional_info = ask_gpt(nutritional_info_prompt).strip()

                            cuisine_prompt = f"Identify the cuisine type for '{recipe_name}'.Do not give additional data like procedure, ingredients, nutritional information and cooking time in this section."
                            st.session_state.cuisine = ask_gpt(cuisine_prompt).strip()

                        else:
                            time.sleep(0.5)  # Small delay to avoid rapid requests

                    if not unique_recipe_found:
                        st.warning("Could not generate a unique recipe. Please try again later.")
                    else:
                        st.success(f"Generated a unique recipe.")

                # UI for recipe generation
                if "show_generate_recipe_button" not in st.session_state:
                    st.session_state.show_generate_recipe_button = True

                if st.session_state.show_generate_recipe_button:
                    if st.button("Generate Recipe"):
                        if uploaded_images:
                            # Code to process images and detect ingredients
                            all_detected_ingredients = []
                            for uploaded_file in uploaded_images:
                                image = np.array(Image.open(uploaded_file))
                                preprocessed_image = preprocess_image(image)
                                detected_text = ocr_with_tesseract(preprocessed_image)
                                detected_text_easyocr = ocr_with_easyocr(image)
                                combined_text = detected_text.strip() + ' ' + ' '.join(detected_text_easyocr).strip()

                                if len(combined_text.strip()) > 10:
                                    gpt_prompt = f"Identify and list only the ingredients or food items from this text: '{combined_text}'"
                                    gpt_response = ask_gpt(gpt_prompt)
                                    detected_ingredients = gpt_response.strip().split(", ")
                                    all_detected_ingredients.extend(detected_ingredients)
                                else:
                                    detected_label = classify_fruit_vegetable(image)
                                    all_detected_ingredients.append(detected_label)

                            st.session_state.unique_ingredients = list(set(all_detected_ingredients))
                            generate_unique_recipe()
                            st.session_state.show_generate_recipe_button = False
                        else:
                            st.warning("Please upload at least one ingredient image.")

                if st.session_state.get("recipe_name"):
                    st.subheader("Generated Recipe Details")
                    st.write(f"**Recipe Name:** {st.session_state.recipe_name}")
                    st.write(f"**Detected Ingredients:** {', '.join(st.session_state.unique_ingredients)}")
                    st.write("**Procedure:**")
                    st.write(st.session_state.procedure)
                    st.write("**Nutritional Information:**")
                    st.write(st.session_state.nutritional_info)
                    st.write(f"**Cooking Time:** {st.session_state.cooking_time} minutes")
                    st.write(f"**Cuisine:** {st.session_state.cuisine}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Save Recipe"):
                            def insert_recipe(username, ingredients, recipe_name, cooking_time, nutritional_info, cuisine):
                                try:
                                    connection = database_connection.get_db_connection()
                                    if connection:
                                        cursor = connection.cursor()
                                        recipe_generated = f"Recipe: {st.session_state.recipe_name}\nIngredients: {', '.join(st.session_state.unique_ingredients)}\nProcedure:\n{st.session_state.procedure}\nNutritional Info:\n{st.session_state.nutritional_info}\nCooking Time: {st.session_state.cooking_time} minutes\nCuisine: {st.session_state.cuisine}"
                                        insert_query = """
                                        INSERT INTO "Recipes_Details" ("Username", "Ingredients", "Recipe_Generated", "Cooking_Time", "Nutritional_Value", "Cuisine")
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                        """
                                        cursor.execute(insert_query, (username, ', '.join(ingredients), recipe_generated, cooking_time, nutritional_info, cuisine))
                                        connection.commit()
                                        cursor.close()
                                        connection.close()
                                        return True
                                    else:
                                        st.error("Failed to connect to the database.")
                                        return False
                                except Exception as e:
                                    st.error(f"Error inserting recipe into the database: {e}")
                                    return False

                            if insert_recipe(
                                st.session_state.username,
                                st.session_state.unique_ingredients,
                                st.session_state.recipe_name,
                                st.session_state.cooking_time,
                                st.session_state.nutritional_info,
                                st.session_state.cuisine,
                            ):
                                st.success("Recipe saved successfully!")
                                st.session_state.saved = True  # Update save status
                            

                    with col2:
                        if st.button("Generate New Recipe"):
                            generate_unique_recipe()
                            st.session_state.show_generate_recipe_button = False

            with tab2:
                st.subheader("Saved Recipes")
                
                # Function to fetch saved recipes from the database
                def fetch_saved_recipes(username):
                    try:
                        connection = database_connection.get_db_connection()
                        if connection:
                            cursor = connection.cursor()
                            
                            fetch_query = """
                            SELECT "Recipe_Generated" FROM "Recipes_Details"
                            WHERE "Username" = %s
                            """
                            cursor.execute(fetch_query, (username,))
                            recipes = cursor.fetchall()
                            
                            connection.commit()
                            cursor.close()
                            connection.close()
                            
                            return [recipe[0] for recipe in recipes]
                        else:
                            print("Failed to connect to the database.")
                            return []
                    except Exception as e:
                        print(f"Error fetching recipes from the database: {e}")
                        return []
                    finally:
                        if cursor:
                            cursor.close()
                        if connection:
                            connection.close()
                
                # Fetch saved recipes for the logged-in user
                saved_recipes = fetch_saved_recipes(st.session_state.username)

                # Dropdown to select a saved recipe
                if saved_recipes:
                    selected_recipe = st.selectbox("Select a saved recipe:", saved_recipes)

                    # Display the selected recipe
                    if selected_recipe:
                        st.text_area("Recipe Details:", selected_recipe, height=300)
                else:
                    st.info("No recipes saved yet.")


# Main flow of the app
if st.session_state.logged_in:
    show_recipe_generation()
else:
    show_login_register()