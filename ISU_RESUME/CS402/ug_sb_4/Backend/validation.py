from streamlyne_ext import Streamlyne
from data_extraction import Extractor
import pandas as pd
from rapidfuzz import process, fuzz
import re
import numpy as np

def validation_helper(ss_dict, st_dict, num_years, ss_new_col_name, st_new_col_name, ss_match_index, st_match_index):
     spreadsheet_salary_names = matching_preparation(ss_dict, ss_match_index, ss_new_col_name)
     streamlyne_salary_names = matching_preparation(st_dict, st_match_index, st_new_col_name)
     result_df = match_names(spreadsheet_salary_names, streamlyne_salary_names, ss_new_col_name, st_new_col_name)
     final_df = merge_yearly_totals(result_df, ss_dict, st_dict, num_years, ss_match_index, st_match_index)
     return final_df

def validate_salaries(ss_extractor, st_extractor):
     numYears, keyPersonnel = ss_extractor.grab_key_personnel()
     _, otherPersonnel = ss_extractor.grab_other_personnel()
     otherPersonnel["Position"] = np.where(
        otherPersonnel["Employee Count"] > 1,
        otherPersonnel["Position"] + " 1 - " + otherPersonnel["Employee Count"].astype(str),
        otherPersonnel["Position"]
     )
     salaries_df = st_extractor.salary_extraction()
     spreadsheet_dict = {"keyPersonnel": keyPersonnel, "otherPersonnel": otherPersonnel}
     streamlyne_dict = {"salaries_df": salaries_df}
     final_df = validation_helper(spreadsheet_dict, streamlyne_dict, numYears, "Name", "Name", 0, 0)
     return final_df

def validate_benefits(ss_extractor, st_extractor):
     numYears, ss_benefits = ss_extractor.grab_benefits()
     st_benefits = st_extractor.benefits_extraction()
     spreadsheet_dict = {"ss_benefits": ss_benefits}
     streamlyne_dict = {"st_benefits": st_benefits}
     final_df = validation_helper(spreadsheet_dict, streamlyne_dict, numYears, "Name", "Name", 0, 0)
     return final_df

def validate_direct_costs(ss_extractor, st_extractor):
    numYears, ss_direct = ss_extractor.grab_direct_cost()
    st_direct = st_extractor.direct_cost_extraction()
    ss_direct = direct_cost_preparation(ss_direct)
    spreadsheet_dict = {"ss_direct": ss_direct}
    streamlyne_dict = {"st_direct": st_direct}
    final_df = validation_helper(spreadsheet_dict, streamlyne_dict, numYears, "Cost Name", "Cost Name", 0, 0)
    return final_df

def validate_travel(ss_extractor, st_extractor):
    num_years, domestic_df = ss_extractor.grab_domestic_travel()
    domestic_df = travel_preparation(domestic_df, "Domestic")
    _, international_df = ss_extractor.grab_international_travel()
    international_df = travel_preparation(international_df, "International")
    ss_domestic = pd.concat([domestic_df, international_df])
    st_domestic = st_extractor.travel_extraction()
    spreadsheet_dict = {"ss_domestic": ss_domestic}
    streamlyne_dict = {"st_domestic": st_domestic}
    final_df = validation_helper(spreadsheet_dict, streamlyne_dict, num_years, "Type", "Type", 0, 0)
    return final_df

def validate_indirect(ss_extractor, st_extractor):
     numYears, ss_indirect = ss_extractor.grab_indirect_costs()
     st_indirect = st_extractor.indirect_cost_extraction()
     spreadsheet_dict = {"ss_indirect": ss_indirect}
     streamlyne_dict = {"st_indirect": st_indirect}
     final_df = validation_helper(spreadsheet_dict, streamlyne_dict, numYears, "Name", "Name", 0, 0)
     return final_df

def direct_cost_preparation(spreadsheet_df):
    spreadsheet_df['group'] = spreadsheet_df['Cost'].str.extract(r'(^[^ |:|-]+)')
    to_group_list = ["Tuition", "Other"]
    to_group = spreadsheet_df[spreadsheet_df['group'].isin(to_group_list)]
    unchanged = spreadsheet_df[~spreadsheet_df['group'].isin(to_group_list)]

    cols_to_agg = spreadsheet_df.loc[:, ~spreadsheet_df.columns.isin(['Cost', 'group'])].columns

    grouped = (
        to_group
        .groupby('group', as_index=False)
        .agg({col: 'sum' for col in cols_to_agg})
    )
    result = pd.concat([
        unchanged.drop(columns='group'),
        grouped.rename(columns={'group': 'Cost'})
    ], ignore_index=True)
    return result

def travel_preparation(travel_df, type):
    if(not travel_df.empty):
        grouped = (
            travel_df
            .groupby('Year', as_index = False)
            .agg({'TOTAL': 'sum'})
        )
        pivoted = (
            grouped
            .pivot_table(columns='Year', values='TOTAL', aggfunc='sum')
            .rename(columns=lambda x: f"Year {x} Total")
            .reset_index(drop=True)      
        )
        pivoted.columns.name = None
        pivoted.insert(0, "Type", type)
        
        
        return pivoted
    else:
        return travel_df

def clean_name(x):
    x = x.lower()
    x = re.sub(r'\b(asst)\b', 'assistant ', x)
    x = re.sub(r'\btbd\b', '', x)
    x = re.sub(r'graduate', '', x)
    x = re.sub(r'costs', '', x)
    x = re.sub(r'[^a-z0-9 ]', '', x)
    return x.strip()

def matching_preparation(df_list, match_index, column_name):
  rows = []
  for name, df in df_list.items():
        df = enumerate_repeats_only(df, match_index)
        # Get the value at the given index
        col_values = df.iloc[:,match_index]
        for val in col_values:
          rows.append({
              column_name: val,
              "source": name
          })
  return pd.DataFrame(rows)

def enumerate_repeats_only(df, col_index):
    # Count occurrences within each group
    counts = df.groupby(df.columns[col_index]).cumcount() + 1

    # Determine which values actually repeat
    repeats = df[df.columns[col_index]].duplicated(keep=False)

    # Append enumeration only for repeated values
    df[df.columns[col_index]] = df[df.columns[col_index]] + repeats.map(
        lambda r: "" if not r else ""
    )  # placeholder, replaced below

    df.loc[repeats, df.columns[col_index]] = (
        df.loc[repeats, df.columns[col_index]] + " " + counts[repeats].astype(str)
    )

    return df

def match_names(spreadsheet_df, streamlyne_df, spreadsheet_col_name, streamlyne_col_name):
    spreadsheet_df['spreadsheet_clean'] = spreadsheet_df[spreadsheet_col_name].apply(clean_name)
    streamlyne_df['streamlyne_clean'] = streamlyne_df[streamlyne_col_name].apply(clean_name)
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
    matches_df = matches_df[matches_df['score'] > 45]
    result = matches_df.merge(spreadsheet_df, on='spreadsheet_clean', how='inner')
    result.rename(columns={spreadsheet_col_name: 'spreadsheet_name', 'source':'spreadsheet_source'}, inplace=True)
    result = result.merge(streamlyne_df, on='streamlyne_clean', how = 'inner')
    result.rename(columns={streamlyne_col_name: 'streamlyne_name', 'source':'streamlyne_source'}, inplace=True)
    return result

def merge_yearly_totals(result_df, spreadsheet_dfs, stream_dfs, n_years, ss_match_index, st_match_index):
    spreadsheet_yearly_dict = {f'Spreadsheet Year {i} Total': float(0) for i in range(1, n_years + 1)}
    streamlyne_yearly_dict = {f'Streamlyne Year {i} Total': float(0) for i in range(1, n_years + 1)}
    difference_dict = {f'Difference Year {i} Total': float(0) for i in range(1, n_years + 1)}
    result_df = result_df.assign(**spreadsheet_yearly_dict)
    result_df = result_df.assign(**streamlyne_yearly_dict)
    result_df = result_df.assign(**difference_dict)
    for _, row in result_df.iterrows():
        row_label = row.name
        # print("Row Label")
        # print(row_label)
        ss_source = row["spreadsheet_source"]
        st_source = row["streamlyne_source"]

        # print("SOURCE NAMES")
        # print(ss_source)
        # print(st_source)

        ss_df = spreadsheet_dfs[ss_source]
        st_df = stream_dfs[st_source]

        # print("SOURCE DF")
        # print(ss_df)
        # print(st_df)

        # Extract the correct rows by label
        # print("SS NAME")
        # print(row["spreadsheet_name"])
        ss_match = row["spreadsheet_name"]
        st_match = row["streamlyne_name"]
        # print("SS COL")
        ss_df_col = ss_df.columns[ss_match_index]
        st_df_col = st_df.columns[st_match_index]

        ss_row = ss_df.loc[ss_df[ss_df_col] == ss_match]
        st_row = st_df.loc[st_df[st_df_col] == st_match]

        # print("SPREADSHEET ROW")
        # print(ss_row)
        # print("STREAMLYNE ROW")
        # print(st_row)

        

        for i in range(1, n_years +1):
            column_name = f"Year {i} Total"
            ss_val = ss_row[column_name].item()
            st_val = st_row[column_name].item()
            diff = ss_val - st_val
            result_df.at[row_label, f"Spreadsheet {column_name}"] = ss_val
            result_df.at[row_label, f"Streamlyne {column_name}"] = st_val
            result_df.at[row_label, f"Difference {column_name}"] = diff
    
    # Build ordered year columns
    ordered_cols = []
    for i in range(1, n_years + 1):
        ordered_cols.append(f"Spreadsheet Year {i} Total")
        ordered_cols.append(f"Streamlyne Year {i} Total")
        ordered_cols.append(f"Difference Year {i} Total")

    # Identify your non-year columns
    id_cols = [
        "spreadsheet_name",
        "streamlyne_name",
        "score",
        "streamlyne_source"
    ]
    end_cols = [
        "spreadsheet_source",
        "streamlyne_source",
        "spreadsheet_clean",
        "streamlyne_clean"
    ]

    # Combine and reorder
    final_cols = id_cols + ordered_cols + end_cols
    result_df = result_df[final_cols]

    return result_df

def validation(spreadsheet_path, streamlyne_path):
    spread_extractor = Extractor(spreadsheet_path)
    pdf_extractor = Streamlyne(streamlyne_path)
    salaries_df = validate_salaries(spread_extractor, pdf_extractor)
    benefits_df = validate_benefits(spread_extractor, pdf_extractor)
    direct_cost_df = validate_direct_costs(spread_extractor, pdf_extractor)
    travel_df = validate_travel(spread_extractor, pdf_extractor)
    indirect_df = validate_indirect(spread_extractor, pdf_extractor)
    return salaries_df, benefits_df, direct_cost_df, travel_df, indirect_df

def main():
    print("Starting program")
    salaries, benefits, direct_cost, travel, indirect = validation("spreadsheets/PD7040 Budget_ISU_USDA_DSFAS_Gelder.xlsm", "./streamlyne/Budget+Summary+Detailed+Page-479215.pdf")
    print("Salaries-----------------------------------------------------------------")
    print(salaries.filter(regex='spreadsheet_name|Difference'))
    print("Benefits-----------------------------------------------------------------")
    print(benefits.filter(regex='spreadsheet_name|Difference'))
    print("Direct Costs-----------------------------------------------------------------")
    print(direct_cost.filter(regex='spreadsheet_name|Difference'))
    print("Travel-----------------------------------------------------------------")
    print(travel.filter(regex='spreadsheet_name|Difference'))
    print("Indirect Costs-----------------------------------------------------------------")
    print(indirect.filter(regex='spreadsheet_name|Difference'))
if __name__ == "__main__":
    main()