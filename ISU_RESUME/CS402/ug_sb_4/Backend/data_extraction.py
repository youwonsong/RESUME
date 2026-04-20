import pandas as pd
import numpy as np

class Extractor:
    """Used to extract the data from the standardized spreadsheets. Initialize a new one per spreadsheet"""
    def __init__(self, path):
        """Initialize the object

        Args:
            path (str): the path to the spreadsheet doc. Origin is the Backend folder.
        """
        #Get data
        self.data_path = path
        self.data = create_dataframe(self.data_path, "Summary")
        self.travel_data = create_dataframe(self.data_path, "Travel")
        #Trim off the totals from the data
        year_mask = self.data.isin(['Total Sponsor Funds'])
        _,col = np.where(year_mask)
        self.year_end_col = col[0].item()
        self.data = self.data.iloc[:, 0:self.year_end_col]
        
        year_mask = self.travel_data.isin(['TOTAL'])
        _, col = np.where(year_mask)
        travel_end_col = col[0].item()
        self.travel_data = self.travel_data.iloc[:, 0:travel_end_col+1]

        #Grab indicies for later computation:

        #yearly totals col for cost_share
        df_str = self.data.astype(str)
        mask = df_str.apply(lambda col: col.str.contains('Cost-Shared', case=False, na=False)) & \
            ~df_str.apply(lambda col: col.str.contains('total', case=False, na=False))
        mask = mask.to_numpy()
        self.cost_share_indices = np.argwhere(mask)[:, 1]
        
        #yearly totals for base costs
        mask = df_str.apply(lambda col: col.str.contains('Sponsor Funds', case=False, na=False)) & \
            ~df_str.apply(lambda col: col.str.contains('total', case=False, na=False))
        mask = mask.to_numpy()
        self.baseline_indices = np.argwhere(mask)[:, 1]
        
        #index's for sections

        #Key Personnel
        mask = self.data.isin(['Key Personnel'])
        row, _ = np.where(mask)
        self.key_personnel_index = row.item()
        #Other Personnel
        mask = self.data.isin(['Other Personnel'])
        row, _ = np.where(mask)
        self.other_personnel_index = row.item()
        #Fringe benefits
        mask = self.data.isin(['Fringe Benefits'])
        row, _ = np.where(mask)
        self.fringe_benefits_index = row.item()

        mask = self.data.isin(['Subtotal: Salaries, Wages, and Benefits'])
        row, _ = np.where(mask)
        self.end_fringe_index = row.item()

        #Direct cost
        mask = self.data.isin(['Other Direct Costs'])
        row, _ = np.where(mask)
        self.direct_cost_index = row.item()

        mask = self.data.isin(['Subtotal: Total Direct Costs (TDC)'])
        row, _ = np.where(mask)
        self.end_direct_cost_index = row.item()
        
        #Domestic travel
        mask = self.travel_data.isin(['Domestic Travel'])
        row, _ = np.where(mask)
        self.domestic_index = row.item()

        #International travel
        mask = self.travel_data.isin(['International Travel'])
        row, _ = np.where(mask)
        self.international_index = row.item()

        #Travel
        mask = self.data.isin(['Travel'])
        row, _ = np.where(mask)
        self.travel_index = row.item()

        mask = self.data.isin(['Participant Support Cost'])
        row, _ = np.where(mask)
        self.end_travel_index = row.item()

        #Indirect costs
        mask = self.data.isin(['Indirect Costs'])
        row, _ = np.where(mask)
        self.indirect_index = row.item()

        mask = self.data.isin(['Total Direct + Indirect Costs'])
        row, _ = np.where(mask)
        self.indirect_index_end = row.item()

        #Equipment
        self.equipment_index = np.where(self.data['Unnamed: 2'].str.contains('Equipment', case=False, na=False))[0][0].item()
        self.equipment_end_index = self.travel_index
    
    def grab_key_personnel(self, cost_share):
        """Returns the key personnel information with the following format: Full Name, Monthly Percentage, Year 1 Total, Year 2 Total.

        Returns:
            numYears: an int of the number of years the budget covers
            dataframe: A pandas dataframe with the following format: Full Name, Monthly Percentage, Year 1 Total, Year 2 Total.
        """
        key_personnel_df = self.data.iloc[self.key_personnel_index+1:self.other_personnel_index-1,]
        key_personnel_grab_index = [2, 4]
        key_personnel_columns = ['Full Name', 'Monthly Percentage']
        numYears, key_personnel_df = self.create_return_subset(key_personnel_df, key_personnel_grab_index, key_personnel_columns, cost_share)
        return numYears, key_personnel_df
    
    def grab_other_personnel(self, cost_share):
        """Returns the other personnel information in the following format: Position, Monthly Percentage, Employee Count, Year 1 Total, Year 2 Total

        Returns:
            numYears: an int of the number of years the budget covers
            dataframe: A pandas dataframe in the following format: Position, Monthly Percentage, Employee Count, Year 1 Total, Year 2 Total
        """
        other_personnel_df = self.data.iloc[self.other_personnel_index+1:self.fringe_benefits_index-2,]
        other_personnel_grab_index = [2, 4, 3, 6]
        other_personnel_columns = ['Position',  'Monthly Percentage', 'Base Rate', 'Employee Count']
        numYears, other_personnel_df = self.create_return_subset(other_personnel_df, other_personnel_grab_index, other_personnel_columns, cost_share)
        return numYears, other_personnel_df
    
    def grab_benefits(self, cost_share):
        """Returns the benefits information. In the following format: Position, Percentage.

        Returns:
            numYears: an int of the number of years the budget covers
            dataframe: pandas dataframe in the following format: Position, Percentage.
        """
        benefits_df = self.data.iloc[self.fringe_benefits_index+1:self.end_fringe_index-1,]
        benefits_grab_index = [2, 3]
        benefits_columns = ['Position', 'Percentage']
        numYears, benefits_df = self.create_return_subset(benefits_df, benefits_grab_index, benefits_columns, cost_share)
        return numYears, benefits_df
    
    def grab_direct_cost(self, cost_share):
        """Returns the direct cost information in the following format: Cost, Year 1 Total, Year 2 Total.

        Returns:
            numYears: an int of the number of years the budget covers
            dataframe: pandas dataframe in the following format: Cost, Year 1 Total, Year 2 Total.
        """
        direct_cost_df = self.data.iloc[self.direct_cost_index+1:self.end_direct_cost_index-1,]
        direct_cost_grab_index = [2]
        direct_cost_columns = ['Cost']
        numYears, direct_cost_df = self.create_return_subset(direct_cost_df, direct_cost_grab_index, direct_cost_columns, cost_share)
        return numYears, direct_cost_df
    
    def grab_domestic_travel(self):
        """returns the domestic travel information in the format of: Year, Purpose & Destination, # of People, Airfare/ Person, # Nights, Rate per Night, Lodging Total, # Meal Days, Meal Cost per Day, Meal Total, Ground Transportation, Registration Per Person, TOTAL.

        Returns:
            numYears: an int of the number of years the budget covers
            dataframe: returns a pandas dataframe
        """
        travel = self.travel_data.iloc[self.domestic_index+2:self.international_index-1,]
        travel = travel.reset_index(drop=True)
        travel.columns = travel.iloc[0].values
        travel = travel.drop(index=0, axis=0)
        travel = travel.reset_index(drop=True)
        travel = travel.dropna(subset=['Purpose & Destination'])
        travel = travel.reset_index(drop=True)
        numYears = travel['Year'].max()
        return numYears, travel
    
    def grab_international_travel(self):
        """returns the international travel information in the format of: Year, Purpose & Destination, # of People, Airfare/ Person, # Nights, Rate per Night, Lodging Total, # Meal Days, Meal Cost per Day, Meal Total, Ground Transportation, Registration Per Person, TOTAL.

        Returns:
            numYears: an int of the number of years the budget covers
            dataframe: returns a pandas dataframe. Likely to have 0 rows.
        """
        international =  self.travel_data.iloc[self.international_index+2:,]
        international = international.reset_index(drop=True)
        international.columns = international.iloc[0].values
        international = international.drop(index=0, axis=0)
        international = international.reset_index(drop=True)
        international = international.dropna(subset=['Purpose & Destination'])
        international = international.reset_index(drop=True)
        numYears = international['Year'].max()
        return numYears, international
    
    def grab_indirect_costs(self, cost_share):
        indirect_cost_df = self.data.iloc[self.indirect_index+1:self.indirect_index_end-1,]
        indirect_cost_grab_index = [2,3]
        indirect_cost_columns = ['Cost Name', 'Percentage']
        numYears, indirect_cost_df = self.create_return_subset(indirect_cost_df, indirect_cost_grab_index, indirect_cost_columns, cost_share)
        return numYears, indirect_cost_df
    
    def grab_equipment_costs(self, cost_share):
        equipment_cost_df = self.data.iloc[self.equipment_index+1:self.equipment_end_index-1,]
        equipment_grab_index = [2]
        equipment_cost_columns = ['Cost Name']
        numYears, equipment_cost_df = self.create_return_subset(equipment_cost_df, equipment_grab_index, equipment_cost_columns, cost_share)
        return numYears, equipment_cost_df
    
    def grab_fa_rate(self):
        """Extracts the F&A Use Rate from the F&A Calculation- Sponsor Funds sheet.
        
        Returns:
            float: The extracted F&A rate (e.g., 0.53). Defaults to 0.53 if not found.
        """
        try:
            fa_df = create_dataframe(self.data_path, "F&A Calculation- Sponsor Funds")
            mask = fa_df.astype(str).apply(lambda x: x.str.contains('Use Rate', case=False, na=False))
            rows, cols = np.where(mask)
            
            if len(rows) > 0:
                use_rate_col = cols[0]
                use_rate_row = rows[0]
                
                for i in range(use_rate_row + 1, use_rate_row + 15):
                    val = fa_df.iat[i, use_rate_col]
                
                    if pd.notna(val) and isinstance(val, (int, float)) and val > 0:
                        rate = float(val)
                        return rate if rate < 1 else rate / 100
            return 0.53 
            
        except Exception as e:
            print(f"F&A rate error (use default value 0.53 ): {e}")
            return 0.53

    def extract(self):
        """Extracts all relevant data from the spreadsheet.
        
        Returns:
            numYears: the number of years,
            dfs: a dictionary with all of the baseline dfs. 
            cs_dfs: a dictionary with the costshare dfs. If there is no costshare the df will be empty.
            cs_dfs_exist: true if there are values in at least one cs_df, false if they are all empty
        """
        numYears, key_personnel_df = self.grab_key_personnel(False)
        _, other_personnel_df = self.grab_other_personnel(False)
        _, benefits_df = self.grab_benefits(False)
        _, direct_cost_df = self.grab_direct_cost(False)
        _, domestic_df = self.grab_domestic_travel()
        _, international_df = self.grab_international_travel()
        _, indirect_cost_df = self.grab_indirect_costs(False)
        _, equipment_df = self.grab_equipment_costs(False)
        baseline_dfs = {
            "key_personnel": key_personnel_df,
            "other_personnel": other_personnel_df,
            "benefits": benefits_df,
            "direct_cost": direct_cost_df,
            "domestic": domestic_df,
            "international": international_df,
            "indirect_cost" : indirect_cost_df,
            "equipment": equipment_df
        }
        _, cs_key_personnel_df =  self.grab_key_personnel(True)
        _, cs_other_personnel_df = self.grab_other_personnel(True)
        _, cs_benefits_df = self.grab_benefits(True)
        _, cs_direct_cost_df = self.grab_direct_cost(True)
        _, cs_indirect_cost_df = self.grab_indirect_costs(True)
        _, cs_equipment_df = self.grab_equipment_costs(True)
        cs_dfs = {
            "key_personnel": cs_key_personnel_df,
            "other_personnel": cs_other_personnel_df,
            "benefits": cs_benefits_df,
            "direct_cost": cs_direct_cost_df,
            "indirect_cost" : cs_indirect_cost_df,
            "equipment": cs_equipment_df
        }
        #Assume they are all empty
        cs_dfs_empty = True
        for _, item in cs_dfs.items():
            #If at least one is not
            if(not item.empty):
                cs_dfs_empty = False
        cs_dfs_exist = not cs_dfs_empty
        return numYears, baseline_dfs, cs_dfs, cs_dfs_exist

    def create_return_subset(self, subset_data, grab_index, grab_col_names, cost_share):
        """Cleans out the subset data to remove unnecessary cells. Returns a final df with any number of years. Number of years is also returned.

        Args:
            subset_data (pandas DataFrame): not-clean pandas dataframe for a section
            grab_index (list[int]): list of indexes to grab from the first 6 columns
            grab_col_names (list[str]): list of names for the columns to grab

        Returns:
            numYears (int): an int of the number of years the budget covers
            return_df (pandasDataframe): final dataframe
        """
        if cost_share:
            years_df = subset_data.iloc[:,self.cost_share_indices]
        else:
            years_df = subset_data.iloc[:,self.baseline_indices]
        years_df = years_df.fillna(0)
        years_df = years_df.loc[:, (years_df != 0).any(axis=0)]
        years_df = years_df.loc[(years_df != 0).any(axis=1)]
        years_df.columns = [f"Year {i} Total" for i in range(1, len(years_df.columns)+1)]
        numYears = len(years_df.columns)
        return_df = subset_data.iloc[:, grab_index]
        return_df.columns = grab_col_names
        return_df = pd.merge(return_df, years_df, left_index=True, right_index=True, how='inner')
        return_df = return_df.reset_index(drop=True)
        return numYears, return_df


def create_dataframe(path, sheet_name):
    """Reads the excel at the specific location

    Args:
        path (str): the location of the spreadsheet
        sheet_name (str): the name of the specific sheet

    Returns:
        dataframe: pandas dataframe
    """
    data = pd.read_excel(path, sheet_name = sheet_name)
    return data

def main():
    print("Starting program")
    path = "spreadsheets/BOB Budget.xlsm"
    ext = Extractor(path)
    _, dfs, cs_dfs, cs_dfs_exist = ext.extract()
    for key, item in dfs.items():
        print(f"{key}-------------------------------------------------------------------")
        print(item)
    if(cs_dfs_exist):
        print("COST SHARE===================================================================")
        for key, item in cs_dfs.items():
            print(f"{key}-------------------------------------------------------------------")
            print(item)
    # print("Key Personnel -------------------------------------------------------------------")
    # _, df = ext.grab_key_personnel()
    # print(df)
    # print("Other Personnel------------------------------------------------------------------")
    # _, df = ext.grab_other_personnel()
    # print(df)
    # print("Fringe Benefits------------------------------------------------------------------")
    # _, df = ext.grab_benefits()
    # print(df)
    # print("Equipment------------------------------------------------------------------------")
    # _, df = ext.grab_equipment_costs()
    # print(df)
    # print("Domestic Travel------------------------------------------------------------------")
    # _, df = ext.grab_domestic_travel()
    # print(df)
    # print("International Travel-------------------------------------------------------------")
    # _, df = ext.grab_international_travel()
    # print(df)
    # print("Other Direct Costs---------------------------------------------------------------")
    # _, df = ext.grab_direct_cost()
    # print(df)
    # print("Indirect Costs-------------------------------------------------------------------")
    # _, df = ext.grab_indirect_costs()
    # print(df)

# Use the conditional to run the main function
if __name__ == "__main__":
    main()