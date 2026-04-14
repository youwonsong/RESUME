import pandas as pd
import numpy as np

class Extractor:
    """Used to extract the data from the standardized spreadsheets. Initialize a new one per spreadsheet"""
    def __init__(self, path):
        """Initialize the object

        Args:
            path (str): the path to the spreadsheet doc. Origin is the Backend folder.
        """
        self.data_path = path
        self.data = create_dataframe(self.data_path, "Summary")
        year_mask = self.data.isin(['Total Sponsor Funds'])
        row,col = np.where(year_mask)
        self.year_end_col = col[0].item()
        self.data = self.data.iloc[:, 0:self.year_end_col-1]
        self.travel_data = create_dataframe(self.data_path, "Travel")
        self.key_personnel_index = np.where(self.data['Unnamed: 2'] == 'Key Personnel')[0][0].item()
        self.other_personnel_index = np.where(self.data['Unnamed: 2'] == 'Other Personnel')[0][0].item()
        self.fringe_benefits_index = np.where(self.data['Unnamed: 2'] == 'Fringe Benefits')[0][0].item()
        self.end_fringe_index = np.where(self.data['Unnamed: 2'] == 'Subtotal: Salaries, Wages, and Benefits')[0][0].item()
        self.direct_cost_index = np.where(self.data['Unnamed: 2'] == 'Other Direct Costs')[0][0].item()
        self.end_direct_cost_index = np.where(self.data['Unnamed: 2']== 'Subtotal: Total Direct Costs (TDC)')[0][0].item()
        self.domestic_index = np.where(self.travel_data['Unnamed: 0']== 'Domestic Travel')[0][0].item()
        self.international_index = np.where(self.travel_data['Unnamed: 0'] == "International Travel")[0][0].item()
        
    
    def grab_key_personnel(self):
        """Returns the key personnel information with the following format: Full Name, Monthly Percentage, Year 1 Total, Year 2 Total.

        Returns:
            numYears: an int of the number of years the budget covers
            dataframe: A pandas dataframe with the following format: Full Name, Monthly Percentage, Year 1 Total, Year 2 Total.
        """
        key_personnel_df = self.data.iloc[self.key_personnel_index+1:self.other_personnel_index-1,]
        key_personnel_grab_index = [2, 4]
        key_personnel_columns = ['Full Name', 'Monthly Percentage']
        numYears, key_personnel_df = create_return_subset(key_personnel_df, key_personnel_grab_index, key_personnel_columns)
        return numYears, key_personnel_df
    
    def grab_other_personnel(self):
        """Returns the other personnel information in the following format: Position, Monthly Percentage, Employee Count, Year 1 Total, Year 2 Total

        Returns:
            numYears: an int of the number of years the budget covers
            dataframe: A pandas dataframe in the following format: Position, Monthly Percentage, Employee Count, Year 1 Total, Year 2 Total
        """
        other_personnel_df = self.data.iloc[self.other_personnel_index+1:self.fringe_benefits_index-2,]
        other_personnel_grab_index = [2, 4, 3, 6, 5]
        other_personnel_columns = ['Position',  'Monthly Percentage', 'Base Rate', 'Employee Count', 'Hours']
        numYears, other_personnel_df = create_return_subset(other_personnel_df, other_personnel_grab_index, other_personnel_columns)
        return numYears, other_personnel_df
    
    def grab_benefits(self):
        """Returns the benefits information. In the following format: Position, Percentage.

        Returns:
            numYears: an int of the number of years the budget covers
            dataframe: pandas dataframe in the following format: Position, Percentage.
        """
        benefits_df = self.data.iloc[self.fringe_benefits_index+1:self.end_fringe_index-1,]
        benefits_grab_index = [2, 3]
        benefits_columns = ['Position', 'Percentage']
        numYears, benefits_df = create_return_subset(benefits_df, benefits_grab_index, benefits_columns)
        return numYears, benefits_df
    
    def grab_direct_cost(self):
        """Returns the direct cost information in the following format: Cost, Year 1 Total, Year 2 Total.

        Returns:
            numYears: an int of the number of years the budget covers
            dataframe: pandas dataframe in the following format: Cost, Year 1 Total, Year 2 Total.
        """
        direct_cost_df = self.data.iloc[self.direct_cost_index+1:self.end_direct_cost_index-1,]
        direct_cost_grab_index = [2]
        direct_cost_columns = ['Cost']
        numYears, direct_cost_df = create_return_subset(direct_cost_df, direct_cost_grab_index, direct_cost_columns)
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

def create_return_subset(subset_data, grab_index, grab_col_names):
    """Cleans out the subset data to remove unnecessary cells. Returns a final df with any number of years. Number of years is also returned.

    Args:
        subset_data (pandas DataFrame): not-clean pandas dataframe for a section
        grab_index (list[int]): list of indexes to grab from the first 6 columns
        grab_col_names (list[str]): list of names for the columns to grab

    Returns:
        numYears (int): an int of the number of years the budget covers
        return_df (pandasDataframe): final dataframe
    """
    years_df = subset_data.iloc[:,7:]
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
    path = "Backend/spreadsheets/test2.xlsm"
    ext = Extractor(path)
    numYears, df = ext.grab_key_personnel()
    print(df.head)
    print(numYears)

# Use the conditional to run the main function
if __name__ == "__main__":
    main()