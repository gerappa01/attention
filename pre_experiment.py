import json

print("Pre-experiment questionnaire")
print("""You will take part in a study on Adaptive Learning. To process your results, we would like to ask you the
following questions. Please read this paper carefully and answer honestly and to the best of your abilities.
There are no right or wrong answers.""")

data = {}

print("\nFACTUAL:")
data["initials"] = input("Your initials (First name, Family name): ").strip()
data["sex"] = input("Sex (M/F): ").strip().upper()
data["sleep_hours"] = input("Hours of sleep last night: ").strip()

print("\nCurrent energy level:")
print("\n".join([
    "1: I'M ALMOST DEAD",
    "2: Yaawn…",
    "3: I could use some sleep",
    "4: Normal",
    "5: Feeling good",
    "6: I'm on top of my game",
    "7: I could run a marathon!"
]))
data["energy_level"] = input("Select a number (1–7): ").strip()

print("\nREADING SKILLS:")
data["read_moby_dick"] = input("Have you ever read (parts of) Moby Dick before? (Y/N): ").strip().upper()

print("\nAre you an avid reader?")
print("\n".join([
    "1: Never read a book, like ever",
    "2: Only read when forced",
    "3: Rarely read, maybe articles",
    "4: Enjoy reading, but infrequent",
    "5: Read a few books a year",
    "6: Read often, several books/month",
    "7: I read every chance I get"
]))
data["avid_reader"] = input("Select a number (1–7): ").strip()

print("\nSelf-reported English level:")
print("\n".join([
    "1: Me no speak English good.",
    "2: I can say some things, but not much.",
    "3: I understand basic stuff, but it's hard.",
    "4: I can have a simple conversation.",
    "5: I can express myself clearly, though not perfectly.",
    "6: I communicate fluently and understand most nuance.",
    "7: I converse with the utmost eloquence and command a refined register."
]))
data["english_level"] = input("Select a number (1–7): ").strip()

print("\nSELF-CONTROL & ATTENTION:")
likert = [
    "1: Never",
    "2: Rarely",
    "3: Occasionally",
    "4: Sometimes",
    "5: Often",
    "6: Usually",
    "7: Always"
]

def likert_prompt(question_key, question_text):
    print(f"\n{question_text}")
    print("\n".join(likert))
    data[question_key] = input("Select a number (1–7): ").strip()

likert_prompt("dishes_procrastination", "How often do you put off doing the dishes?")
likert_prompt("deadline_extensions", "Do you frequently ask for deadline extensions?")
likert_prompt("focus_on_difficult_material", "“I find it easy to stay focused when reading difficult material.”")
likert_prompt("distracted_by_thoughts", "“I often get distracted by my own thoughts.”")
likert_prompt("delayed_gratification", "“I can delay gratification if needed (e.g., finishing work before Netflix)”")

print("How motivated are you to become more well-read?")
data["motivation_to_be_well_read"] = input("Select a number (1–7): ").strip()

likert_prompt("think_about_goals", "How often do you think about your long-term goals?")

print("\nList 4–5 medium- or long-term goals you have in life (bullet points or sentences):")
data["personal_goals"] = input("> ").strip()

print("\nHow would becoming more literate or well-read help you achieve these goals?")
data["literacy_help"] = input("> ").strip()

# Dump as JSON
print("\n=== JSON OUTPUT ===")
print(json.dumps(data, indent=2))
