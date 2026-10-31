import streamlit as st
import os
from dotenv import load_dotenv
from groq import Groq, AuthenticationError, RateLimitError, APIConnectionError, APIStatusError

load_dotenv()

def gen_plan(fitness_goal:str, current_weight:int, desired_weight:int, height:int, gender:str, age:int, activity_level:str, experience_level:str, days_per_week:int, mins_per_session:int,equipment:list[str], limitations:str)->str:
    # 1. API key verification
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Please set it in your environment or .env file.")

    model = os.getenv("GROQ_MODEL")

    # BMI calculation
    weight_kg = current_weight
    height_m = height / 100
    bmi = weight_kg / (height_m * height_m)

    equipment_str = ", ".join(equipment) if equipment else "No equipment (bodyweight only)"

    prompt = f"""
    Create a personalized workout plan based on the following details:
    - Fitness Goal: {fitness_goal}
    - Current Weight: {current_weight}kg
    - Desired Weight: {desired_weight}kg
    - Height: {height}cm
    - BMI: {bmi:.1f}
    - Gender: {gender}
    - Age: {age}
    - Activity Level: {activity_level}
    - Experience Level: {experience_level}
    - Days per week: {days_per_week}
    - Time per session: {mins_per_session} minutes
    - Equipment Access: {equipment_str}
    - Limitations/Injuries: {limitations or 'None'}

    Generate a detailed workout plan matching the requested frequency with specific exercises, sets, reps, rest times, and notes. Create a weekly plan daywise. Also, add disclaimer in case of any injuries/limitations are mentioned.
    """

    client = Groq(api_key=api_key)

    chat_completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are an expert fitness coach. Create safe, realistic workout routines based on user constraints."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    # Validate LLM output structure and content
    if not chat_completion.choices or not chat_completion.choices[0].message:
        raise ValueError("Received an empty response from the AI model.")

    response_text = chat_completion.choices[0].message.content
    if not response_text or not response_text.strip():
        raise ValueError("The AI model returned a blank response. Please try generating again.")

    return response_text.strip()


# Page setup
st.set_page_config(page_title="Workout Plan Generator", layout="centered")

st.title("🏋️ Workout Plan Generator")
st.write("Customize your workout preferences below to generate a tailored routine.")

with st.form(key="workout_form"):
    fitness_goal = st.selectbox(
        label="Enter your fitness goal",
        options=["Build muscle", "Lose fat", "General fitness", "Improve endurance"],
        index=0
    )

    col1, col2 = st.columns(2)
    with col1:
        current_weight = st.number_input(
            label="Current Weight (kg)",
            min_value=0.0,
            max_value=300.0,
            value=70.0,
            step=0.5
        )
        height = st.number_input(
            label="Height (cm)",
            min_value=0.0,
            max_value=250.0,
            value=170.0,
            step=1.0
        )
        gender = st.selectbox(
            label="Gender",
            options=["Male", "Female", "Other / Prefer not to say"],
            index=0
        )

    with col2:
        desired_weight = st.number_input(
            label="Desired Weight (kg)",
            min_value=0.0,
            max_value=300.0,
            value=68.0,
            step=0.5
        )
        age = st.number_input(
            label="Age",
            min_value=0,
            max_value=120,
            value=25,
            step=1
        )
        activity_level = st.selectbox(
            label="Activity Level",
            options=["Sedentary", "Lightly active", "Moderately active", "Very active"],
            index=0
        )

    experience_level = st.selectbox(
        label="Experience Level",
        options=["Beginner", "Intermediate", "Advanced"],
        index=0
    )

    days_per_week = st.slider(
        label="Days Available Per Week",
        min_value=1,
        max_value=7,
        value=3,
        step=1
    )

    mins_per_session = st.selectbox(
        label="Session time (minutes)",
        options=["30", "45", "60", "90"],
        index=2
    )

    equipment = st.multiselect(
        label="Equipment Access",
        options=["No equipment (bodyweight)", "Home dumbbells", "Full gym"],
        default=["No equipment (bodyweight)"]
    )

    limitations = st.text_area(
        label="Specify any injuries or limitations (Optional)",
        placeholder="e.g., bad knees, lower back pain, no overhead pressing",
        help="Specify any physical conditions or movements you need to avoid."
    )

    submit_button = st.form_submit_button(label="Generate Plan")
    
if submit_button:
    # ---------------------------------------------------------
    # 1. INPUT VALIDATION (Friendly messages, prevents app crash)
    # ---------------------------------------------------------
    validation_errors = []

    if height <= 50.0:
        validation_errors.append("Please enter a realistic height (greater than 50 cm).")
    if current_weight <= 20.0:
        validation_errors.append("Please enter a realistic current weight (greater than 20 kg).")
    if desired_weight <= 20.0:
        validation_errors.append("Please enter a realistic desired weight (greater than 20 kg).")
    if age < 12:
        validation_errors.append("Please enter a valid age (12 or older).")
    if days_per_week < 1:
        validation_errors.append("Please select at least 1 workout day per week.")
    if not equipment:
        validation_errors.append("Please select at least one equipment option (select 'No equipment' if none).")

    if validation_errors:
        for err in validation_errors:
            st.warning(f"⚠️ {err}")
        st.stop()  # Clean stop: prevents the rest of the script from executing

    # ---------------------------------------------------------
    # 2. BACKEND / LLM EXECUTION WITH TRY-EXCEPT
    # ---------------------------------------------------------
    payload = {
        "fitness_goal": fitness_goal,
        "current_weight": current_weight,
        "desired_weight": desired_weight,
        "height": height,
        "gender": gender,
        "age": age,
        "activity_level": activity_level,
        "experience_level": experience_level,
        "days_per_week": days_per_week,
        "mins_per_session": mins_per_session,
        "equipment": equipment,
        "limitations": limitations.strip() if limitations else None
    }

    with st.spinner("Connecting to coach AI and preparing your plan..."):
        try:
            plan = gen_plan(**payload)
            st.success("Your workout plan is ready!")
            st.markdown("### Generated Workout Plan")
            st.markdown(plan)

        # Catch authentication issues (invalid/expired GROQ_API_KEY)
        except AuthenticationError:
            st.error("🔑 Invalid API Key. Please verify your Groq API key in your `.env` file.")

        # Catch usage rate limits
        except RateLimitError:
            st.warning("⏳ The service is currently busy or rate limits were exceeded. Please wait a minute and try again.")

        # Catch offline/network drops
        except APIConnectionError:
            st.error("🌐 Network Connection Error: Unable to reach Groq servers. Please check your internet connection.")

        # Catch HTTP status errors (500 internal server, 404 bad model, etc.)
        except APIStatusError as status_err:
            st.error(f"⚠️ Groq Service Error (Status code: {status_err.status_code}). Please try again later.")

        # Catch empty responses or missing environment variables
        except ValueError as val_err:
            st.warning(f"⚠️ {val_err}")

        # Fallback for unexpected exceptions
        except Exception as err:

            st.error("⚠️ An unexpected error occurred while generating your plan. Please try again.")
            with st.expander("Technical Error Details"):
                st.code(str(err))