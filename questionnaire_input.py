import os
import pandas as pd
from datetime import datetime

def get_valid_input(prompt, input_type, valid_range=None, valid_options=None):
    """Get and validate user input based on type and constraints."""
    while True:
        user_input = input(prompt)
        
        # Handle empty input
        if not user_input.strip():
            print("Input cannot be empty. Please try again.")
            continue
            
        # Validate based on input type
        if input_type == "str":
            return user_input
        
        elif input_type == "num":
            try:
                value = float(user_input)
                return value
            except ValueError:
                print("Please enter a valid number.")
                
        elif input_type == "int":
            try:
                value = int(user_input)
                if valid_range and (value < valid_range[0] or value > valid_range[1]):
                    print(f"Please enter a number between {valid_range[0]} and {valid_range[1]}.")
                    continue
                return value
            except ValueError:
                print("Please enter a valid integer.")
                
        elif input_type == "option":
            if user_input.upper() in valid_options:
                return user_input.upper()
            else:
                options_str = "/".join(valid_options)
                print(f"Please enter one of the following options: {options_str}")

def collect_pre_questionnaire():
    """Collect pre-experiment questionnaire data."""
    print("\n=== PRE-EXPERIMENT QUESTIONNAIRE ===\n")
    
    # Get participant initials
    initials = get_valid_input("Enter participant initials (e.g., 'J-D'): ", "str")
    experiment_type = get_valid_input("Enter experiment type\n1. Prompt\n2. Meme\n3. Control: ", "int", valid_range=[1, 3])
    
    # Create folder if it doesn't exist
    folder_name = f"collected_data/EX_{"-".join(initials.split(' '))}_{experiment_type}"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Created folder: {folder_name}")
    
    # Collect pre-questionnaire data
    pre_data = {
        "initials": initials,
        "timestamp": datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
        "sex": get_valid_input("Sex (M/F): ", "option", valid_options=["M", "F"]),
        "hours_of_sleep": get_valid_input("Hours of sleep: ", "num"),
        "energy_level": get_valid_input("Energy level (1-7): ", "int", valid_range=[1, 7]),
        "read_moby_dick": get_valid_input("Have you read Moby Dick? (Y/N): ", "option", valid_options=["Y", "N"]),
        "avid_reader": get_valid_input("Avid reader (1-7): ", "int", valid_range=[1, 7]),
        "english_level": get_valid_input("English level (1-7): ", "int", valid_range=[1, 7]),
        "dishes": get_valid_input("Dishes (1-7): ", "int", valid_range=[1, 7]),
        "extensions": get_valid_input("Extensions (1-7): ", "int", valid_range=[1, 7]),
        "stay_focused_difficult_materials": get_valid_input("Stay focused on difficult materials (1-7): ", "int", valid_range=[1, 7]),
        "distracted": get_valid_input("Distracted (1-7): ", "int", valid_range=[1, 7]),
        "delay_gratification": get_valid_input("Delay gratification (1-7): ", "int", valid_range=[1, 7]),
        "motivated_to_be_well_read": get_valid_input("Motivated to be well-read (1-7): ", "int", valid_range=[1, 7]),
        "long_term_goals_rating": get_valid_input("Long-term goals (1-7): ", "int", valid_range=[1, 7]),
        "long_term_goals_text": get_valid_input("Long term goals (text): ", "str"),
        "becoming_more_literate": get_valid_input("Becoming more literate (text): ", "str")
    }
    
    # Save to CSV
    df = pd.DataFrame([pre_data])
    filename = f"{folder_name}/pre_questionnaire_{initials}.csv"
    df.to_csv(filename, index=False)
    print(f"\nPre-questionnaire data saved to {filename}")
    
    return initials, folder_name

def collect_post_questionnaire(initials, folder_name):
    """Collect post-experiment questionnaire data."""
    print("\n=== POST-EXPERIMENT QUESTIONNAIRE ===\n")
    
    # Collect post-questionnaire data
    post_data = {
        "initials": initials,
        "timestamp": datetime.now().strftime('%Y-%m-%d-%H-%M-%S'),
        "engaged": get_valid_input("Engaged (1-7): ", "int", valid_range=[1, 7]),
        "difficult": get_valid_input("Difficult (1-7): ", "int", valid_range=[1, 7]),
        "focused": get_valid_input("Focused (1-7): ", "int", valid_range=[1, 7]),
        "zoning_out": get_valid_input("Zoning out (Y/N): ", "option", valid_options=["Y", "N"]),
        "wander": get_valid_input("Wander (1-7): ", "int", valid_range=[1, 7]),
        "helpful": get_valid_input("Helpful (1-7): ", "int", valid_range=[1, 7]),
        "relevant": get_valid_input("Relevant (1-7): ", "int", valid_range=[1, 7]),
        "continue_using": get_valid_input("Continue using (Y/N): ", "option", valid_options=["Y", "N"]),
        "anything_else": get_valid_input("Anything else (text): ", "str")
    }
    
    # Save to CSV
    df = pd.DataFrame([post_data])
    filename = f"{folder_name}/post_questionnaire_{initials}.csv"
    df.to_csv(filename, index=False)
    print(f"\nPost-questionnaire data saved to {filename}")

def main():
    print("=== QUESTIONNAIRE DATA ENTRY TOOL ===")
    print("This tool helps you enter paper-based questionnaire data into digital format.")
    
    while True:
        print("\nSelect an option:")
        print("1. Enter pre-experiment questionnaire")
        print("2. Enter post-experiment questionnaire")
        print("3. Enter both questionnaires")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            initials, folder_name = collect_pre_questionnaire()
        
        elif choice == "2":
            initials = get_valid_input("Enter participant initials (e.g., 'J-D'): ", "str")
            experiment_type = get_valid_input("Enter experiment type\n1. Prompt\n2. Meme\n3. Control: ", "int", valid_range=[1, 3])
            
            # Create folder if it doesn't exist
            folder_name = f"collected_data/EX_{"-".join(initials.split(' '))}_{experiment_type}"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                print(f"Created folder: {folder_name}")
                
            collect_post_questionnaire(initials, folder_name)
        
        elif choice == "3":
            initials, folder_name = collect_pre_questionnaire()
            collect_post_questionnaire(initials, folder_name)
        
        elif choice == "4":
            print("Exiting program. Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter a number between 1 and 4.")

if __name__ == "__main__":
    main() 