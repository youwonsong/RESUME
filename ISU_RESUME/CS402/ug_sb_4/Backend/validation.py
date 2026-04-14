from streamlyne_ext import Streamlyne
from data_extraction import Extractor
import pandas as pd
from rapidfuzz import process, fuzz
import re


def spreadsheet_name_consolidation(keyPersonnel, otherPersonnel):
    # --- Expand rows based on Employee Count ---
    expanded = otherPersonnel.loc[
        otherPersonnel.index.repeat(otherPersonnel['Employee Count'])
    ].reset_index(drop=True)  # ✅ critical to avoid index issues

    # --- Create numbering within each Position ---
    expanded['num'] = expanded.groupby('Position').cumcount() + 1

    # --- Build name column ---
    expanded['name'] = expanded['Position'] + ' ' + expanded['num'].astype(str)

    # --- Remove numbering if only 1 employee for that position ---
    counts = expanded.groupby('Position')['Position'].transform('count')
    expanded.loc[counts == 1, 'name'] = expanded['Position']

    # --- Combine with keyPersonnel ---
    final_df = pd.concat([
        keyPersonnel[['Full Name']].rename(columns={'Full Name': 'name'}).assign(source='keyPersonnel'),
        expanded[['name']].assign(source='otherPersonnel')
    ], ignore_index=True)
    return final_df

def streamlyne_name_consolidation(faculty_df, grad_df, profes_df, undergrad_df):
    dfs = {
    'faculty_df': faculty_df,
    'grad_df': grad_df,
    'profes_df': profes_df,
    'undergrad_df': undergrad_df
    }

    # Build combined dataframe
    combined_df = pd.concat([
        df[['Full Name']].assign(source=name)
        for name, df in dfs.items()
    ], ignore_index=True)

    # Rename column if you want
    combined_df = combined_df.rename(columns={'Full Name': 'name'})
    return combined_df

def clean_name(x):
    x = x.lower()
    x = re.sub(r'\b(asst)\b', 'assistant ', x)
    x = re.sub(r'\btbd\b', '', x)
    x = re.sub(r'graduate', '', x)
    x = re.sub(r'[^a-z0-9 ]', '', x)
    return x.strip()

def match_names(spreadsheet_df, streamlyne_df):
    spreadsheet_df['spreadsheet_clean'] = spreadsheet_df['name'].apply(clean_name)
    streamlyne_df['streamlyne_clean'] = streamlyne_df['name'].apply(clean_name)
    list1 = spreadsheet_df['spreadsheet_clean'].tolist()
    list2 = streamlyne_df['streamlyne_clean'].tolist()

    matches = []

    for name in list1:
        match, score, _ = process.extractOne(
            name,
            list2,
            scorer=fuzz.token_sort_ratio 
        )
        
        matches.append({
            'spreadsheet_clean': name,
            'streamlyne_clean': match,
            'score': score
        })

    matches_df = pd.DataFrame(matches)
    matches_df = matches_df[matches_df['score'] > 50]
    result = matches_df.merge(spreadsheet_df, on='spreadsheet_clean', how='inner')
    result.rename(columns={'name': 'spreadsheet_name', 'source':'spreadsheet_source'}, inplace=True)
    result = result.merge(streamlyne_df, on='streamlyne_clean', how = 'inner')
    result.rename(columns={'name': 'streamlyne_name', 'source':'streamlyne_source'}, inplace=True)
    return result

def add_data(result_df, keyPersonnel, otherPersonnel, faculty_df, grad_df, profes_df, undergrad_df, numYears):
    spreadsheet_list = pd.Series({
    'keyPersonnel': keyPersonnel,
    'otherPersonnel': otherPersonnel
    })
    streamlyne_list = pd.Series({
        'faculty_df': faculty_df,
        'grad_df': grad_df,
        'profes_df': profes_df,
        'undergrad_df': undergrad_df
    })
    result_df = add_data_helper(result_df, spreadsheet_list, "Spreadsheet", "spreadsheet_source")
    result_df = add_data_helper(result_df, streamlyne_list, "Streamlyne", "streamlyne_source")
    
    column_order = ['spreadsheet_name', 'streamlyne_name']

    for y in range(1, numYears+1):
        spreadsheet_col = f"Spreadsheet Year {y} Total"
        streamlyne_col = f"Streamlyne Year {y} Total"
        diff_col = f"Difference Year {y}"
        result_df[diff_col] = (
            result_df[spreadsheet_col] - result_df[streamlyne_col]
        )
        column_order += [spreadsheet_col, streamlyne_col, diff_col]
    
    column_order += ['spreadsheet_clean', 'streamlyne_clean', 'score', 'spreadsheet_source', 'streamlyne_source']

    result_df = result_df[column_order]
    print(result_df)
    print(result_df.columns)
    return result_df

def add_data_helper(result_df, sources, origin, source):
    all_year_cols = set()
    for df in sources:
        cols = [c for c in df.columns if c.startswith("Year ") and c.endswith(" Total")]
        all_year_cols.update(cols)
    for col in all_year_cols:
        new_col = f"{origin} {col}"
        result_df[new_col] = None  # create once

        for source_name, df in sources.items():
            if col not in df.columns:
                continue
            mask = result_df[source] == source_name
            target_rows = result_df.loc[mask]

            # Align by position
            values = df[col].reset_index(drop=True)

            # Only take as many values as target rows
            aligned_values = values.iloc[:len(target_rows)]

            # Assign
            result_df.loc[mask, new_col] = aligned_values.values
    return result_df

def main():
    print("Starting program")
    spread_extractor = Extractor("spreadsheets/PD7040 Budget_ISU_USDA_DSFAS_Gelder.xlsm")
    numYears, keyPersonnel = spread_extractor.grab_key_personnel()
    _, otherPersonnel = spread_extractor.grab_other_personnel()
    namesDf = spreadsheet_name_consolidation(keyPersonnel, otherPersonnel)
    pdf_extractor = Streamlyne("./streamlyne/Budget+Summary+Detailed+Page-479215.pdf")
    faculty_df, grad_df, profes_df, undergrad_df = pdf_extractor.salary_extraction()
    stream_names_df = streamlyne_name_consolidation(faculty_df, grad_df, profes_df, undergrad_df)
    dataframes = pd.Series({
        'Spreadsheet - Key Personnel': keyPersonnel, 
        'Spreadsheet - Other Personnel': otherPersonnel, 
        'Streamlyne - Faculty': faculty_df, 
        'Streamlyne - Graduate Students': grad_df, 
        'Streamlyne - Professionals and Scientific': profes_df, 
        'Streamlyne - Undergraduate Students': undergrad_df})
    for name, df in dataframes.items():
        print(f"{name}----------------------------------------------------------------")
        print(df)
    print("==============================================================================================================================")
    final_df = match_names(namesDf, stream_names_df)
    result_df = add_data(final_df, keyPersonnel, otherPersonnel, faculty_df, grad_df, profes_df, undergrad_df, numYears)
    print(result_df[['spreadsheet_name', 'streamlyne_name','Spreadsheet Year 1 Total', 'Streamlyne Year 1 Total', 'Difference Year 1']])
    
# Use the conditional to run the main function
if __name__ == "__main__":
    main()