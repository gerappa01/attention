import json

print("Post-experiment questionnaire")
print("""Now that you finished the experiment, we would like to ask you to answer a few more questions.
Please be honest and reflective — your feedback helps improve future versions of the tool.""")

data = {}

# Helper
likert_7 = [
    "1: Never",
    "2: Rarely",
    "3: Occasionally",
    "4: Sometimes",
    "5: Often",
    "6: Usually",
    "7: Always"
]

def likert_prompt(key, question, labels=None):
    print(f"\n{question}")
    if labels:
        print("\n".join([f"{i+1}: {label}" for i, label in enumerate(labels)]))
    else:
        print("\n".join(likert_7))
    data[key] = input("Select a number (1–7): ").strip()

# 1. Engagement
likert_prompt(
    "engagement_level",
    "How engaged did you feel while reading?",
    ["What reading?", "Meh", "Somewhat", "Focused", "Into it", "Absorbed", "I *was* Ishmael"]
)

# 2. Perceived difficulty
likert_prompt(
    "text_difficulty",
    "How difficult was the text for you?",
    ["Easy peasy", "Manageable", "Bit tricky", "Challenging", "Very dense", "Mentally taxing", "UGH!"]
)

# 3. Focus
likert_prompt(
    "focus_level",
    "How focused were you overall?",
    ["Not very", "Slightly", "Occasionally", "Moderately", "Mostly", "Very", "Laser-like"]
)

# 4. Zoning out
print("\nDid you notice yourself zoning out?")
print("1: Yes\n2: No")
data["zoned_out"] = input("Select 1 or 2: ").strip()

# 5. Mind wandering count (fun labels)
likert_prompt(
    "mind_wandering_count",
    "How many times did your mind wander during the reading? (Even if unnoticed by the program)",
    ["Once", "Twice", "Thrice", "Four-ever", "High five", "Six pack", "Seventh heaven"]
)

# 6. Helpfulness of attention prompts
likert_prompt(
    "attention_prompt_helpfulness",
    "How helpful were the attention prompts?",
    ["Bothering", "Annoying", "Neutral", "Mildly helpful", "Useful", "Very helpful", "Absolutely clutch"]
)

# 7. Personal relevance of messages
likert_prompt(
    "personal_relevance",
    "Did the content of the attention messages feel personally relevant to you?",
    ["Not at all", "Barely", "Somewhat", "Moderately", "Often", "Strongly", "Spoke to my soul"]
)

# 8. Willingness to use again
print("\nWould you continue using a tool like this while studying or reading?")
print("1: Nope\n2: Heck yeah")
data["use_tool_again"] = input("Select 1 or 2: ").strip()

# 9. Optional comments
print("\nAnything else you would like to add?")
data["additional_comments"] = input("> ").strip()

# Dump
print("\n=== JSON OUTPUT ===")
print(json.dumps(data, indent=2))
