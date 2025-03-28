import pandas as pd

# Load the existing datasets
df1 = pd.read_csv("medical_data.csv", on_bad_lines='skip')
df2 = pd.read_csv("symtoms_df.csv", on_bad_lines='skip')

# Remove the unnecessary index column from df2
df2 = df2.drop(columns=['Unnamed: 0'], errors='ignore')

# List of common allergies (expand this as needed)
common_allergies = ["penicillin", "sulfa", "aspirin", "NSAIDs"]

# Function to add a symptom and its probability for adults and children
def add_symptom(row, symptom, adult_prob, child_prob):
    """
    Adds a symptom to the Symptoms column and updates probability columns.
    """
    # Clean the symptom by stripping leading/trailing whitespace and converting to lowercase
    symptom = symptom.strip().lower()

    if pd.isna(row['Symptoms']) or not row['Symptoms']:
        row['Symptoms'] = symptom
        row['Symptom_Keywords'] = symptom.replace('_', ' ') #Replace underscores for keyword consistency
    else:
        # Prevent duplicate symptoms from being added.
        symptoms = [s.strip().lower() for s in str(row['Symptoms']).split(',')] #Split by comma and clean
        keywords = [k.strip().lower() for k in str(row['Symptom_Keywords']).split(';')] if pd.notna(row['Symptom_Keywords']) else []

        if symptom not in symptoms:  # Check if the symptom is already present.
            row['Symptoms'] += f", {symptom}"
            row['Symptom_Keywords'] += f"; {symptom.replace('_', ' ')}"

    # Function to update probability columns
    def update_probability(prob_str, symptom, probability):
        """
        Updates the probability string with the new symptom and probability.
        """
        if pd.isna(prob_str) or not prob_str:
            return f"{symptom}:{probability}"
        else:
            existing_probs = dict(item.split(":") for item in prob_str.split(";") if item)
            if symptom not in existing_probs:
                return f"{prob_str};{symptom}:{probability}"
            else:
                # If symptom exists, return the original string
                return prob_str

    # Update adult and child probabilities
    row['Adult_Symptom_Probability'] = update_probability(row['Adult_Symptom_Probability'], symptom, adult_prob)
    row['Child_Symptom_Probability'] = update_probability(row['Child_Symptom_Probability'], symptom, child_prob)
    return row

# List to hold new rows to be appended to df1
new_rows = []

# Process df2 symptoms and add to df1
for index, row in df2.iterrows():
    disease = row['Disease'].strip() #Clean disease name

    # Find the matching disease in df1
    match = df1[df1['Disease'].str.strip().str.lower() == disease.lower()] #Case-insensitive comparison

    if not match.empty:
        df1_index = match.index[0]  # Get the index of the matching row
        df1_row = df1.loc[df1_index]  #Access row by .loc

        # Add the symptoms to the matching disease in df1 with probabilities

        for i in range(1, 5): #Iterate through the symptom columns
            symptom_col = f'Symptom_{i}'
            symptom = row[symptom_col] if pd.notna(row[symptom_col]) else None # Handle potential NaN values
            if symptom:
                # Assign probabilities based on your knowledge or assumptions
                adult_prob = 4  # Example adult probability (adjust as needed)
                child_prob = 3  # Example child probability (adjust as needed)

                df1.loc[df1_index] = add_symptom(df1_row.copy(), symptom, adult_prob, child_prob) #Use .loc and make copy
                df1_row = df1.loc[df1_index] #Update df1_row to prevent SettingWithCopyWarning
    else:
        # Disease not found in df1, create a new row
        new_row = {'Disease': disease}

        # Add symptoms from df2 to the new row
        symptoms = []
        keywords = []
        adult_probs = []
        child_probs = []

        for i in range(1, 5):
            symptom_col = f'Symptom_{i}'
            symptom = row[symptom_col] if pd.notna(row[symptom_col]) else None
            if symptom:
                symptom = symptom.strip().lower()
                symptoms.append(symptom)
                keywords.append(symptom.replace('_', ' '))
                adult_probs.append(f"{symptom}:4")  # Default probability 4 for adults
                child_probs.append(f"{symptom}:3")  # Default probability 3 for children

        new_row['Symptoms'] = ', '.join(symptoms)
        new_row['Symptom_Keywords'] = '; '.join(keywords)
        new_row['Adult_Symptom_Probability'] = '; '.join(adult_probs)
        new_row['Child_Symptom_Probability'] = '; '.join(child_probs)

        # Fill other columns with default/empty values.  Adjust as needed
        new_row['Medicine'] = ""
        new_row['Dosage'] = ""
        new_row['Severity'] = "Unknown"
        new_row['Contraindications'] = ""
        new_row['Diet'] = ""
        new_row['Precautions'] = ""
        new_row['References'] = ""
        new_row['Age_Group'] = "All"
        new_row['Recommended_Exercises'] = ""
        new_row['Alternative_Therapies'] = ""
        new_row['Recovery_Time'] = ""
        new_row['Emergency_Signs'] = ""
        new_row['Diagnostic_Tests'] = ""
        new_row['Comorbidities_Risks'] = ""
        new_row['Seasonal_Variation'] = ""

        # Add the new row to the list
        new_rows.append(new_row)

# Append new rows to df1
df1 = pd.concat([df1, pd.DataFrame(new_rows)], ignore_index=True)

# *** ALLERGY HANDLING (AFTER MERGING) ***

def add_allergy_info(row):
    """
    Adds allergy-related information to the Contraindications and Precautions.
    """
    contraindications = str(row['Contraindications']) if pd.notna(row['Contraindications']) else ""
    precautions = str(row['Precautions']) if pd.notna(row['Precautions']) else ""

    for allergy in common_allergies:
        if allergy in contraindications.lower() or allergy in precautions.lower():
            continue  # Skip if already mentioned

        contraindications += f", Allergy to {allergy}" if contraindications else f"Allergy to {allergy}"
        precautions += f", Avoid products containing {allergy}" if precautions else f"Avoid products containing {allergy}"

    row['Contraindications'] = contraindications.strip(', ')
    row['Precautions'] = precautions.strip(', ')
    return row

# Iterate through each row in df1 and apply the function to allergy handling
df1 = df1.apply(add_allergy_info, axis=1)


def adjust_dosage_and_alternatives(row):
    """
    Adjusts dosage and alternatives based on age group.
    """
    age_group = row['Age_Group']

    # Correctly handle NaN values in 'Age_Group'
    if pd.isna(age_group) or not isinstance(age_group, str) or age_group.lower() == "all":
        # If 'Age_Group' is NaN, treat it as "All Ages"
        is_adult = False  # Assume not adult-only
    else:
        is_adult = age_group.lower() == "adult+"

    # Adjust dosages for children
    if not is_adult:
        medicine = str(row['Medicine']) if pd.notna(row['Medicine']) else ""
        dosage = str(row['Dosage']) if pd.notna(row['Dosage']) else ""
        if medicine and "Adults:" in dosage:
            dosage = dosage.replace("Adults:", "Children: Consult a doctor for appropriate dosage. Adults:")
        elif medicine and not dosage:
            dosage = "Consult a doctor for appropriate dosage for children."
        row['Dosage'] = dosage

    # Add alternative therapies for all age groups
    alt_therapies = str(row['Alternative_Therapies']) if pd.notna(row['Alternative_Therapies']) else ""
    if not alt_therapies:
        alt_therapies = "Consult a healthcare professional for alternative therapies."
    row['Alternative_Therapies'] = alt_therapies
    return row

# Iterate through each row in df1 and apply the function to adjust dosage and alternatives
df1 = df1.apply(adjust_dosage_and_alternatives, axis=1)

# Save the updated DataFrame to the original CSV file
df1.to_csv("medical_data.csv", index=False)

print("medical_data.csv has been updated.")