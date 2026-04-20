# GRAB TEXT FUNCTION - BASIC
from pypdf import PdfReader
import pandas as pd
import re

class Streamlyne:
    def __init__(self, path):
        self.full_text = grab_text(path)
        self.num_years = grab_num_years(self.full_text)
        self.salary_text, self.fringe_text = separate_salary_and_fringe(self.full_text)
        self.salary_text = re.sub(r'(?<=\d)(?=[A-Za-z])', '\n', self.salary_text)
        self.fringe_text = re.sub(r'(?<=\d)(?=[A-Za-z])', '\n', self.fringe_text)

    def salary_extraction(self):
        """extracts the salary information from the streamlyne document

        Returns:
            faculty_df: dataframe with the information for the faculty
            grad_df: dataframe with the information for the grad students
            professional_df: dataframe with the information for the professionals
            undergrad_df: dataframe with the information for the undergraduate students
        """
        salaries = re.findall(r"(?s)Wages -.*?\d\n(.*?)(?:Salary|Fringe)", self.salary_text)
        result = "".join(salaries)
        result = result.replace(',', '')
        salaries_df = fill_out_salaries(result, self.num_years)
        return salaries_df
    
    def benefits_extraction(self):
        """Extracts the benefits information from a streamlyne document

        Returns:
            ben_faculty_df: the benefits information in a dataframe for the faculty
            ben_grad_assistants_df: the benefits information in a dataframe for the grad assistants
            ben_professional_df: the benefits information in a dataframe for the professionals
            ben_undergrad_df: the benefits information in a dataframe for the undergraduate students
        """
        fringes = re.findall(r"(?s)Wages -.*?\d\n(.*?)(?:Salary|Calculated)", self.fringe_text)
        fringes = "".join(fringes)
        fringes = fringes.replace(',', '')
        fringe_df = fill_out_benefits(fringes, self.num_years)
        return fringe_df

    def travel_extraction(self):
       travel_text = grab_travel(self.full_text)
       travel_df = fill_out_travel_data(travel_text, self.num_years)
       return travel_df

    def direct_cost_extraction(self):
       direct_text = grab_direct_costs(self.full_text)
       direct_df = fill_out_direct_costs(direct_text, self.num_years)
       return direct_df

    def indirect_cost_extraction(self):
       indirect_text = grab_indirect_costs(self.full_text)
       indirect_df = fill_out_indirect_costs(indirect_text, self.num_years)
       return indirect_df

    def equipment_cost_extraction(self):
      equipment_text = re.findall(r"(?s)NON-PERSONNEL\nEquipment.*?\d\n(.*?\n)Travel", self.full_text)
      if(len(equipment_text)>0):
         equipment_text = equipment_text[0]
         equipment_text = equipment_text.replace(',', '')
         equipment_df = fill_out_equipment(equipment_text, self.num_years)
         return equipment_df
      else:
         return

def create_equipment(numYears):
  df = pd.DataFrame({
        'Equipment Name': pd.Series(dtype='str'),
    })
  year_col_dict = {f'Year {i} Total': 0 for i in range(1, numYears + 1)}
  df = df.assign(**year_col_dict)
  return df

def fill_out_equipment(text, numYears):
  df = create_equipment(numYears)
  names = re.findall(r'(?s)(.*?)(?:\d[.\d]+ *)', text)
  moneys = re.findall(r'(?:(\d[.\d]+)[ ])', text)
  names = [s.strip().replace('\n', ' ') for s in names if s.strip()]
  for i in range(0, len(names)):
    name = names[i]
    new_row = []
    new_row.append(name)
    for j in range(0, numYears):
        yearTotal = moneys[i *numYears + j]
        new_row.append(float(yearTotal))
    df.loc[len(df)] = new_row
  return df

def fill_out_indirect_costs(text, numYears):
  indirect_df = create_indirect_costs(numYears)
  text = text.replace('%', '')
  names = re.findall(r'(?s)(.*?)(?:\d[.\d]+ *)', text)
  moneys = re.findall(r'(?:(\d[.\d]+)[ ])', text)
  names = [s.strip().replace('\n', ' ') for s in names if s.strip()]
  for i in range(0, len(names)):
    name = names[i]
    new_row = []
    new_row.append(name)
    for j in range(0, numYears+1):
        yearTotal = moneys[i *numYears + j]
        new_row.append(float(yearTotal))
    indirect_df.loc[len(indirect_df)] = new_row
  return indirect_df

def create_indirect_costs(numYears):
  df = pd.DataFrame({
        'Name': pd.Series(dtype='str'),
        'Rate': pd.Series(dtype='float')
    })
  year_col_dict = {f'Year {i} Total': 0 for i in range(1, numYears + 1)}
  df = df.assign(**year_col_dict)
  return df

def grab_indirect_costs(full_text):
  indirect = re.findall(r"(?s)INDIRECT COSTS(?:.*?)\n(.*?)TOTALS", full_text)[0]
  indirect = indirect.replace(',', '')
  return indirect

def fill_out_direct_costs(direct, numYears):
  direct_df = create_direct_costs(numYears)
  names = re.findall(r'(?s)(.*?)(?:\d[.\d]+ *)', direct)
  moneys = re.findall(r'(?:(\d[.\d]+)[ ])', direct)
  names = [s.strip().replace('\n', ' ') for s in names if s.strip()]
  for i in range(0, len(names)):
    name = names[i]
    new_row = []
    new_row.append(name)
    for j in range(0, numYears):
        yearTotal = moneys[i *numYears + j]
        new_row.append(float(yearTotal))
    direct_df.loc[len(direct_df)] = new_row
  return direct_df

def create_direct_costs(numYears):
  df = pd.DataFrame({
        'Cost Name': pd.Series(dtype='str'),
    })
  year_col_dict = {f'Year {i} Total': 0 for i in range(1, numYears + 1)}
  df = df.assign(**year_col_dict)
  return df

def grab_direct_costs(full_text):
  direct = re.findall(r"(?s)Other Direct(?:.*?)\n(.*?)Calculated", full_text)[0]
  direct = direct.replace(',', '')
  return direct

def grab_travel(text):
  travel = re.findall(r"(?s)(Travel.*?)Other", text)[0]
  travel = travel.replace(',', '')
  return travel

def fill_out_travel_data(travel, num_years):
    travel_df = create_travel(num_years)
    domestic_data = re.findall(r"Domestic (.*)\n", travel)
    domestic_present = False
    if(len(domestic_data)>0):
      domestic_present = True
    international_data = re.findall(r"International (.*)\n", travel)
    international_present = False
    if(len(international_data)>0):
      international_present = True
    if(domestic_present):
      domestic_data = domestic_data[0]
      moneys = re.findall(r"(?:(\d[.\d]+)[ ])", domestic_data)
      new_row = []
      new_row.append("Domestic")
      for j in range(0, num_years):
        yearTotal = moneys[j]
        new_row.append(float(yearTotal))
      travel_df.loc[len(travel_df)] = new_row
    if(international_present):
      international_data = international_data[0]
      moneys = re.findall(r"(?:(\d[.\d]+)[ ])", international_data)
      new_row = []
      new_row.append("International")
      for j in range(0, num_years):
        yearTotal = moneys[j]
        new_row.append(float(yearTotal))
      travel_df.loc[len(travel_df)] = new_row
    return travel_df

def create_travel(numYears):
    df = pd.DataFrame({
        'Type': pd.Series(dtype='str'),
    })
    year_col_dict = {f'Year {i} Total': 0 for i in range(1, numYears + 1)}
    df = df.assign(**year_col_dict)
    return df

def fill_out_benefits(text, numYears):
  df = create_benefits(numYears)
  names = re.findall(r'(?s)(.*?)(?:\d[.\d]+ *)', text)
  moneys = re.findall(r'(?:(\d[.\d]+)[ ])', text)
  names = [s.strip().replace('\n', ' ') for s in names if s.strip()]
  for i in range(0, len(names)):
    name = names[i]
    new_row = []
    new_row.append(name)
    for j in range(0, numYears):
        yearTotal = moneys[i *numYears + j]
        new_row.append(float(yearTotal))
    df.loc[len(df)] = new_row
  return df

def create_benefits(numYears):
  df = pd.DataFrame({
        'Full Name': pd.Series(dtype='str'),
    })
  year_col_dict = {f'Year {i} Total': 0 for i in range(1, numYears + 1)}
  df = df.assign(**year_col_dict)
  return df

def fill_out_salaries(text, numYears):
    arr = re.findall(r"((?:.*\n){,2}[(].*?[)])\n", text)
    df = create_personnel(numYears)
    for person in arr:
        new_row = []
        tbd_exist = re.findall(r"(TBD)", person)
        if(len(tbd_exist) >0):
          name = re.findall(r"(?s)(.*TBD)", person)
          name = name[0].replace('\n', ' ')
          person = re.findall(r"(?s).*?TBD([\s\S]*)", person)[0]
        else:
          name = re.findall(r"^(.*?)[ ]\d", person)
          name = name[0]
        new_row.append(name)
        money = re.findall(r"(?:(\d.*?) )", person)
        percent = money[numYears]
        percent = percent.replace(',', '')
        new_row.append(float(percent))
        for i in range(0,numYears):
            money[i] = money[i].replace(',', '')
            new_row.append(float(money[i]))
        df.loc[len(df)] = new_row
    return df

def separate_salary_and_fringe(text):
    salary = re.findall(r"(?s)(Salary.*?Fringe)", text)
    salary = salary[0]
    fringe = re.findall(r"(?s)Fringe(.*)", text)
    fringe = fringe[0]
    return salary, fringe

def grab_personnel(full_text):
    personnel = re.findall(r"(?s)PERSONNEL(.*?)NON-PERSONNEL", full_text)
    personnel = personnel[0]
    return personnel

def create_personnel(num_years):
    df = pd.DataFrame({
        'Full Name': pd.Series(dtype='str'),
        'Monthly Percentage': pd.Series(dtype='float'),
    })
    year_col_dict = {f'Year {i} Total': 0 for i in range(1, num_years + 1)}
    df = df.assign(**year_col_dict)
    return df

def grab_num_years(text):
    numYears = int(re.findall(r".*Period (\d)", text)[0])
    return numYears

def grab_text(path):
    reader = PdfReader(path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text()
    return full_text


def main():
    print("Starting program")
    strmlyne = Streamlyne("./streamlyne/Budget+Summary+Detailed+Page-479215.pdf")
    salaries_df = strmlyne.salary_extraction()
    #ben_faculty_df, ben_grad_df, ben_profess_df, ben_undergrad_df = strmlyne.benefits_extraction()
    print("---------------------------------------------------------------------------------")
    print("Salaries")
    print(salaries_df)
    print("---------------------------------------------------------------------------------")
    print("Benefits")
    benefits_df = strmlyne.benefits_extraction()
    print(benefits_df)
    print("---------------------------------------------------------------------------------")
    print("Travel")
    travel_df = strmlyne.travel_extraction()
    print(travel_df.head())
    print("---------------------------------------------------------------------------------")
    print("Direct Costs")
    direct_df = strmlyne.direct_cost_extraction()
    print(direct_df.head())
    print("---------------------------------------------------------------------------------")
    print("Indirect Costs")
    indirect_df = strmlyne.indirect_cost_extraction()
    print(indirect_df.head())
    print("---------------------------------------------------------------------------------")
    print("Equipment Costs")
    equipment_df = strmlyne.equipment_cost_extraction()
    print(equipment_df)

# Use the conditional to run the main function
if __name__ == "__main__":
    main()