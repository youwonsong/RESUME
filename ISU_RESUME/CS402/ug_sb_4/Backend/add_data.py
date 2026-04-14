from pathlib import Path
from docxtpl import DocxTemplate
from data_extraction import Extractor
from doc_utils import add_section
from extract_section import extract_section
import pandas as pd
import re


# ── Read exact totals from the spreadsheet's own formula rows ─────────────────

def _read_summary_totals(data_path: str, n_years: int) -> dict:
    """
    Reads key budget figures directly from the Summary sheet's pre-computed rows
    so that our output exactly matches the spreadsheet's formula results.

    Returns a dict with:
      indirect_rate  – float (e.g. 0.4285 or 0.53)
      tdc_total      – float (Total Direct Costs, all years summed)
      indirect_total – float (Indirect Costs, all years summed)
      budget_total   – float (Total Direct + Indirect, all years summed)

    Any entry is None when the value cannot be found.
    """
    out = {"indirect_rate": None, "tdc_total": None,
           "indirect_total": None, "budget_total": None}
    try:
        df = pd.read_excel(data_path, sheet_name="Summary")

        def _year_vals(row_series):
            """Return the first n_years non-zero numeric values from a Series."""
            vals = [v for v in row_series.values
                    if isinstance(v, (int, float)) and v > 100]
            return vals[:n_years]

        # ── Indirect rate from "IDC on …" row (Unnamed:3 column) ─────────────
        # Search only in the description column (col index 2) to avoid
        # accidentally matching the header row (which has "Indirect Costs" label)
        idc_mask = df.iloc[:, 2].astype(str).str.contains(
            r'IDC on', na=False, case=False, regex=True)
        idc_rows = df[idc_mask]
        if not idc_rows.empty:
            raw = idc_rows.iloc[0].iloc[3]          # Unnamed:3 = Rate column
            if isinstance(raw, (int, float)) and raw > 0:
                out["indirect_rate"] = raw if raw <= 1 else raw / 100
            elif isinstance(raw, str):
                try:
                    v = float(raw.strip().rstrip('%'))
                    out["indirect_rate"] = v / 100 if v > 1 else v
                except ValueError:
                    pass

        # ── TDC row ───────────────────────────────────────────────────────────
        tdc_mask = df.apply(
            lambda col: col.astype(str).str.contains(
                r'Subtotal: Total Direct Costs \(TDC\)', na=False, regex=True)
        ).any(axis=1)
        tdc_rows = df[tdc_mask]
        if not tdc_rows.empty:
            yv = _year_vals(tdc_rows.iloc[0])
            if yv:
                out["tdc_total"] = sum(yv)

        # ── Indirect Costs row (labeled "H" in the first column) ──────────────
        h_mask = df.iloc[:, 0].astype(str).str.strip() == 'H'
        h_rows = df[h_mask]
        if not h_rows.empty:
            yv = _year_vals(h_rows.iloc[0])
            if yv:
                out["indirect_total"] = sum(yv)

        # ── Total Direct + Indirect row (labeled "I") ─────────────────────────
        i_mask = df.iloc[:, 0].astype(str).str.strip() == 'I'
        i_rows = df[i_mask]
        if not i_rows.empty:
            yv = _year_vals(i_rows.iloc[0])
            if yv:
                out["budget_total"] = sum(yv)

    except Exception:
        pass   # caller uses computed fallbacks
    return out


# ── Formatting helpers ────────────────────────────────────────────────────────

def money(x):
    try:
        return "${:,.2f}".format(float(x))
    except (ValueError, TypeError):
        return "$0.00"

def pct(x):
    try:
        return "{:.1f}%".format(float(x) * 100)
    except (ValueError, TypeError):
        return "0.0%"

def fmt_mo(x):
    try:
        val = round(float(x), 2)
    except (ValueError, TypeError):
        return "0"
    if val == 0:
        return "0"
    s = f"{val:g}"
    if s.startswith("0."):
        return s[1:]
    return s


# ── Fringe rate helpers ───────────────────────────────────────────────────────

def _get_person_fringe_rate(name: str, rates_by_name: dict, fallback_rate: float) -> float:
    """
    Look up a person's fringe rate from the rates_by_name dict.
    Tries in order:
      1. Exact (case-insensitive) full-name match
      2. Last-name match
      3. Partial / substring match
    Falls back to fallback_rate if nothing matches.
    """
    name_lower = name.lower().strip()
    name_parts = name_lower.split()
    last_name  = name_parts[-1] if name_parts else ""

    # 1. Exact match
    for key, rate in rates_by_name.items():
        if key.lower().strip() == name_lower:
            return rate

    # 2. Last-name match
    if last_name:
        for key, rate in rates_by_name.items():
            key_parts = key.lower().strip().split()
            if key_parts and key_parts[-1] == last_name:
                return rate

    # 3. Substring match
    for key, rate in rates_by_name.items():
        kl = key.lower().strip()
        if name_lower in kl or kl in name_lower:
            return rate
        if last_name and last_name in kl:
            return rate

    return fallback_rate


def _extract_category_rates(ben_df: pd.DataFrame):
    """
    Parse the benefits dataframe and return:
      rates_by_name : {person_or_position_name: rate}  (all non-zero entries)
      cat_rates     : {faculty, ps, grad, ug, postdoc}  (keyword-detected defaults)
    Works for any ISU spreadsheet regardless of how many personnel are listed.
    """
    rates_by_name = {}
    for _, row in ben_df.iterrows():
        pos = str(row.get("Position", "")).strip()
        if pos in ("nan", "0", ""):
            continue
        try:
            rate = float(row.get("Percentage", 0))
        except (ValueError, TypeError):
            continue
        if rate > 0:
            rates_by_name[pos] = rate

    # Detect per-category defaults from position keyword matching
    faculty_rate  = 0.318
    ps_rate       = 0.405
    grad_rate     = 0.152
    ug_rate       = 0.018
    postdoc_rate  = 0.367

    for pos, rate in rates_by_name.items():
        pl = pos.lower()
        if "faculty" in pl:
            faculty_rate = rate
        elif "p&s" in pl or ("professional" in pl and "scientific" in pl):
            ps_rate = rate
        elif "post" in pl and "doc" in pl:
            postdoc_rate = rate
        elif "undergrad" in pl or ("hourly" in pl and "undergraduate" in pl) or "ug" in pl:
            ug_rate = rate
        elif "grad" in pl or "research asst" in pl:
            grad_rate = rate

    return rates_by_name, {
        "faculty":  faculty_rate,
        "ps":       ps_rate,
        "grad":     grad_rate,
        "ug":       ug_rate,
        "postdoc":  postdoc_rate,
    }


# ── Main context builder ──────────────────────────────────────────────────────

def build_context(ext: Extractor, spreadsheet_name: str = "",
                   data_path: str = "") -> dict:
    """
    Build the Jinja2 template context dict from an Extractor.
    Budget totals and the indirect rate are read directly from the spreadsheet's
    own formula rows so the output matches the spreadsheet exactly.
    Works with any number of years and any ISU budget spreadsheet.
    """

    # ── 1. Extract from Excel ─────────────────────────────────────────────────
    n_years,  key_df    = ext.grab_key_personnel()
    _,        other_df  = ext.grab_other_personnel()
    _,        ben_df    = ext.grab_benefits()
    _,        direct_df = ext.grab_direct_cost()
    _,        travel_df = ext.grab_domestic_travel()

    year_cols = [c for c in key_df.columns if "Year" in c]

    # Read exact totals from the spreadsheet's formula rows
    sheet_totals = _read_summary_totals(data_path, n_years) if data_path else {}
    fa_rate = sheet_totals.get("indirect_rate") or ext.grab_fa_rate()

    # ── 2. Fringe rates ───────────────────────────────────────────────────────
    rates_by_name, cat_rates = _extract_category_rates(ben_df)

    faculty_rate_val = cat_rates["faculty"]
    ps_rate_val      = cat_rates["ps"]
    grad_rate_val    = cat_rates["grad"]
    ug_rate_val      = cat_rates["ug"]
    postdoc_rate_val = cat_rates["postdoc"]

    # ── 3. KEY PERSONNEL ──────────────────────────────────────────────────────
    faculty_names_list = []
    ps_names_list      = []
    key_personnel      = []
    total_key_cost     = 0.0

    for i, (_, row) in enumerate(key_df.iterrows()):
        name = str(row.get("Full Name", "")).strip()
        if not name or name == "nan":
            continue

        months   = float(row.get("Monthly Percentage", 0) or 0)
        y_totals = [float(row.get(yc, 0) or 0) for yc in year_cols]
        salary_val = sum(y_totals)
        if salary_val == 0:
            continue

        y1 = y_totals[0] if len(y_totals) > 0 else 0
        y2 = y_totals[1] if len(y_totals) > 1 else 0
        y3 = y_totals[2] if len(y_totals) > 2 else 0

        # All key personnel are listed as Co-PI in the budget justification
        # (is_pi flag is kept for Template2 structural use only)
        role = "Co-PI"

        # Fringe: look up by name, fall back to faculty rate
        fringe_rate = _get_person_fringe_rate(name, rates_by_name, faculty_rate_val)
        fringe_val  = salary_val * fringe_rate
        p_total     = salary_val + fringe_val
        total_key_cost += p_total

        last_name = name.split()[-1]

        # Classify into fringe label table (faculty vs P&S)
        if abs(fringe_rate - ps_rate_val) < 0.01:
            if last_name not in ps_names_list:
                ps_names_list.append(last_name)
        else:
            if last_name not in faculty_names_list:
                faculty_names_list.append(last_name)

        base_monthly = (y1 / months) if months > 0 else 0

        key_personnel.append({
            "is_pi":          (i == 0),
            "role":           role,
            "display_title":  f"{name} ({role})",
            "name":           name,
            "last_name":      last_name,
            "months":         fmt_mo(months),
            "total_months":   fmt_mo(months * n_years),
            "base_salary_y1": money(base_monthly),
            "base_salary_9mo":money(base_monthly * 9),
            "y1_total":       money(y1),
            "y2_total":       money(y2),
            "y3_total":       money(y3),
            "total":          money(p_total),
            "salary":         money(salary_val),
            "fringe":         money(fringe_val),
        })

    # ── 4. OTHER PERSONNEL ────────────────────────────────────────────────────
    other_list   = []
    groups       = {k: {"months": 0.0, "y1": 0.0, "y2": 0.0, "total": 0.0, "name": ""}
                    for k in ("ps", "grad", "ug", "postdoc")}
    total_other_cost = 0.0
    grad_count   = 1

    # Map short codes / full names for known P&S staff
    ps_name_map = {
        "p&s- dh":        "Daryl Herzmann",
        "p&s- cg":        "Craig Gelder",
        "p&s- cc":        "Craig Gelder",
        "daryl herzmann": "Daryl Herzmann",
    }

    for _, row in other_df.iterrows():
        pos       = str(row.get("Position", "")).strip()
        pos_lower = pos.lower()
        months    = float(row.get("Monthly Percentage", 0) or 0)
        y_totals  = [float(row.get(yc, 0) or 0) for yc in year_cols]
        pure_salary = sum(y_totals)
        if pure_salary == 0:
            continue

        # Classify position into one of the four groups
        if "post" in pos_lower and "doc" in pos_lower:
            target       = "postdoc"
            display_role = "Postdoc"
            f_rate       = _get_person_fringe_rate(pos, rates_by_name, postdoc_rate_val)
        elif "undergrad" in pos_lower or pos_lower.startswith("ug") or (
                "hourly" in pos_lower and "undergraduate" in pos_lower):
            target       = "ug"
            display_role = "Undergraduate Student"
            f_rate       = ug_rate_val
        elif "grad" in pos_lower or "research asst" in pos_lower:
            target       = "grad"
            display_role = f"Graduate Student {grad_count}"
            grad_count  += 1
            f_rate       = grad_rate_val
        elif ("professional" in pos_lower or "scientific" in pos_lower
              or "analyst" in pos_lower or "p&s" in pos_lower
              or pos_lower in ps_name_map):
            target       = "ps"
            display_role = "Professional & Scientific"
            f_rate       = ps_rate_val
        else:
            # Try a name-based fringe lookup before giving up
            f_rate       = _get_person_fringe_rate(pos, rates_by_name, 0.0)
            target       = None
            display_role = pos

        actual_fringe = pure_salary * f_rate
        actual_total  = pure_salary + actual_fringe
        total_other_cost += actual_total

        try:   hours_val = int(float(row.get("Hours", 40) or 40))
        except: hours_val = 40
        try:   rate_val  = float(row.get("Base Rate", 18) or 18)
        except: rate_val  = 18.0
        try:   count_val = int(float(row.get("Employee Count", 1) or 1))
        except: count_val = 1

        # Annual base salary for P&S staff (monthly base rate × 12 months)
        # Shown in Template1 as "(Base Salary for year 1: $X)"
        annual_base = money(rate_val * 12) if target == "ps" and rate_val > 100 else ""

        other_list.append({
            "role":              pos,
            "display_role":      display_role,
            "target":            target,
            "months":            fmt_mo(months),
            "hours":             str(hours_val),
            "hourly_rate":       money(rate_val),
            "count":             count_val,
            "total":             money(actual_total),
            "salary":            money(pure_salary),
            "fringe":            money(actual_fringe),
            "annual_base_salary": annual_base,  # P&S only; empty string for others
        })

        if target:
            g = groups[target]
            g["months"] += months
            g["y1"]     += y_totals[0] if y_totals else 0
            g["y2"]     += y_totals[1] if len(y_totals) > 1 else 0
            g["total"]  += pure_salary   # Template2 intentionally shows salary only
            if not g["name"]:
                g["name"] = pos

            if target == "ps" and pure_salary > 0:
                actual_name = ps_name_map.get(pos_lower, pos)
                actual_last = actual_name.split()[-1]
                if actual_last not in ps_names_list:
                    ps_names_list.append(actual_last)

    formatted_groups = {
        k: {
            "name":     v["name"],
            "months":   fmt_mo(v["months"]),
            "y1_total": money(v["y1"]),
            "y2_total": money(v["y2"]),
            "total":    money(v["total"]),
        }
        for k, v in groups.items()
    }

    dynamic_faculty_names = ", ".join(faculty_names_list) if faculty_names_list else "Faculty"
    dynamic_ps_names      = ", ".join(ps_names_list)      if ps_names_list      else "P&S Staff"

    order_map = {"grad": 1, "ug": 2, "ps": 3, "postdoc": 4}
    other_list.sort(key=lambda x: order_map.get(x["target"], 99))

    # ── 5. TRAVEL ─────────────────────────────────────────────────────────────
    travel_list      = []
    total_travel_val = 0.0   # Fully dynamic — computed from spreadsheet data

    if not travel_df.empty:
        grouped_travel = {}

        for _, row in travel_df.iterrows():
            try:    t_total = float(row.get("TOTAL", 0) or 0)
            except: t_total = 0.0
            if t_total == 0:
                continue
            total_travel_val += t_total

            raw_purpose = str(row.get("Purpose & Destination", "Travel"))
            p_lower     = raw_purpose.lower()

            if "visit" in p_lower or "field" in p_lower:
                cat = "field"
            elif "conference" in p_lower or "neurips" in p_lower:
                cat = "conference"
            else:
                cat = raw_purpose

            raw_year = str(row.get("Year", "1"))
            y_list   = [y.strip() for y in re.findall(r'\d+', raw_year)]
            if not y_list:
                y_list = [raw_year]

            try:    people = int(float(row.get("# of People", 1) or 1))
            except: people = 1
            if people == 0:
                people = 1

            if cat not in grouped_travel:
                airfare      = float(row.get("Airfare/ Person",         0) or 0)
                registration = float(row.get("Registration Per Person", 0) or 0)
                hotel        = float(row.get("Lodging Total",           0) or 0)
                meals        = float(row.get("Meal Total",              0) or 0)
                mileage      = float(row.get("Ground Transportation",   0) or 0)
                per_trip     = airfare + registration + hotel + meals + mileage

                grouped_travel[cat] = {
                    "purpose":           raw_purpose,
                    "years_list":        y_list,
                    "total_val":         t_total,
                    "people":            str(people),
                    "per_trip_cost_rep": per_trip,
                    "airfare":           money(airfare),
                    "registration":      money(registration),
                    "hotel":             money(hotel),
                    "nights":            int(float(row.get("# Nights",    0) or 0)),
                    "meal_days":         int(float(row.get("# Meal Days", 0) or 0)),
                    "expenses":          money(meals),
                    "mileage":           money(mileage),
                }
            else:
                grouped_travel[cat]["total_val"] += t_total
                for y in y_list:
                    if y not in grouped_travel[cat]["years_list"]:
                        grouped_travel[cat]["years_list"].append(y)

        for cat, data in grouped_travel.items():
            yl = sorted(data["years_list"])
            if len(yl) > 2:    years_str = ", ".join(yl[:-1]) + f", and {yl[-1]}"
            elif len(yl) == 2: years_str = f"{yl[0]} and {yl[1]}"
            else:              years_str = yl[0]

            travel_list.append({
                "purpose":       data["purpose"],
                "years":         years_str,
                "has_year_1":    "1" in data["years_list"],  # used by Template2
                "people":        data["people"],
                "per_trip_cost": money(data["per_trip_cost_rep"]),
                "airfare":       data["airfare"],
                "registration":  data["registration"],
                "hotel":         data["hotel"],
                "nights":        data["nights"],
                "meal_days":     data["meal_days"],
                "expenses":      data["expenses"],
                "mileage":       data["mileage"],
                "total":         money(data["total_val"]),
                "attendee_desc": "",   # placeholder; fill in manually per project if needed
            })

    def get_travel_order(item):
        p = item["purpose"].lower()
        if "field" in p or "visit" in p:        return 1
        if "conference" in p or "neurips" in p: return 2
        return 3

    travel_list.sort(key=get_travel_order)

    # ── 6. OTHER DIRECT COSTS ─────────────────────────────────────────────────
    def get_cost_dict(keyword):
        if direct_df.empty:
            return {"y1": "$0", "y2": "$0", "total": "$0"}
        matches = direct_df[
            direct_df["Cost"].str.contains(keyword, na=False, case=False, regex=True)
        ]
        if matches.empty:
            return {"y1": "$0", "y2": "$0", "total": "$0"}
        y_cols_d = [c for c in matches.columns if "Year" in c]
        # Sum ALL matching rows (e.g. Tuition has multiple sub-rows)
        y1    = matches[y_cols_d[0]].sum() if len(y_cols_d) > 0 else 0
        y2    = matches[y_cols_d[1]].sum() if len(y_cols_d) > 1 else 0
        total = matches[y_cols_d].sum().sum()
        return {"y1": money(y1), "y2": money(y2), "total": money(total)}

    mat = get_cost_dict("Materials")
    pub = get_cost_dict("Publication")
    con = get_cost_dict("Consultant|Professional Services")
    tui = get_cost_dict("Tuition")
    sto = get_cost_dict("Storage|Computing|Computer")
    pla = get_cost_dict("Planet")

    y_cols_dir = [c for c in direct_df.columns if "Year" in c]
    total_other_direct_val = (
        direct_df[y_cols_dir].sum().sum() if not direct_df.empty else 0.0
    )

    # ── 7. TOTALS ─────────────────────────────────────────────────────────────
    # Use the spreadsheet's own formula-computed values where available.
    # This avoids rounding errors from per-person fringe computation and ensures
    # the document matches the spreadsheet exactly.
    total_salary_fringe = total_key_cost + total_other_cost   # used for section subtotals

    total_direct_val  = (sheet_totals.get("tdc_total")
                         or total_salary_fringe + total_travel_val + total_other_direct_val)
    total_indirect_val = (sheet_totals.get("indirect_total")
                          or total_direct_val * fa_rate)
    total_budget_val   = (sheet_totals.get("budget_total")
                          or total_direct_val + total_indirect_val)

    # ── 8. RETURN CONTEXT DICT ────────────────────────────────────────────────
    return {
        # Project metadata
        "project_name":  spreadsheet_name,

        # Key personnel (full list; Template1 loops all, Template2 uses is_pi flag)
        "pi_name":                key_personnel[0]["name"]          if key_personnel else "",
        "pi_total":               key_personnel[0]["total"]         if key_personnel else "$0",
        "pi_salary_sum":          key_personnel[0]["salary"]        if key_personnel else "$0",
        "pi_fringe_sum":          key_personnel[0]["fringe"]        if key_personnel else "$0",
        "pi_months":              key_personnel[0]["months"]        if key_personnel else "0",
        "pi_base_salary":         key_personnel[0]["base_salary_y1"] if key_personnel else "$0",
        "key_personnel":          key_personnel,

        # Other personnel
        "other_personnel":        other_list,
        "other":                  formatted_groups,

        # Fringe rates & name lists
        "faculty_rate":           pct(faculty_rate_val),
        "ps_rate":                pct(ps_rate_val),
        "grad_rate":              pct(grad_rate_val),
        "ug_rate":                pct(ug_rate_val),
        "faculty_names":          dynamic_faculty_names,
        "ps_names":               dynamic_ps_names,

        "n_years": n_years,

        # Personnel cost subtotals
        "total_key_personnel_cost":   money(total_key_cost),
        "total_other_personnel_cost": money(total_other_cost),
        "total_salary_wages_fringe":  money(total_salary_fringe),

        # Travel
        "travel_details": travel_list,
        "total_travel":   money(total_travel_val),

        # Other direct cost line items
        "materials":   mat,
        "publication": pub,
        "consultant":  con,
        "tuition":     tui,
        "storage":     sto,
        "planet":      pla,

        # Budget totals — entirely from spreadsheet data
        "total_direct_costs":    money(total_other_direct_val),
        "total_direct_sum":      money(total_direct_val),
        "total_indirect_sum":    money(total_indirect_val),
        "total_budget_sum":      money(total_budget_val),
        "indirect_rate":         pct(fa_rate),
        "indirect_off_campus_rate": pct(fa_rate),
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    base            = Path(__file__).resolve().parent
    spreadsheet_dir = base / "spreadsheets"
    outputs_dir     = base / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    # Process every .xlsm and .xlsx file found in the spreadsheets folder
    xlsm_files = sorted(
        list(spreadsheet_dir.glob("*.xlsm")) + list(spreadsheet_dir.glob("*.xlsx"))
    )

    if not xlsm_files:
        print("No spreadsheet files found in", spreadsheet_dir)
        return

    for xlsm_path in xlsm_files:
        spreadsheet_name = xlsm_path.stem
        print(f"\n{'='*60}")
        print(f"Processing: {xlsm_path.name}")
        print("=" * 60)

        try:
            ext = Extractor(str(xlsm_path))
            ctx = build_context(ext, spreadsheet_name, data_path=str(xlsm_path))
        except Exception as e:
            print(f"  ERROR extracting data from {xlsm_path.name}: {e}")
            continue

        for t_name in ["Template1.docx", "Template2.docx"]:
            template_path = base / "templates" / t_name
            if not template_path.exists():
                print(f"  Template not found: {t_name}")
                continue

            try:
                doc = DocxTemplate(str(template_path))
                doc.render(ctx)
                add_section(
                    doc,
                    "Additional Information",
                    "This is just a section to list out some other key details",
                )
                output_path = outputs_dir / f"{spreadsheet_name}_{t_name}.docx"
                doc.save(str(output_path))
                print(f"  Generated : {output_path.name}")

                if t_name == "Template1.docx":
                    section_path = outputs_dir / f"{spreadsheet_name}_key_personnel_section.docx"
                    extract_section(str(output_path), "Key Personnel", str(section_path))
                    print(f"  Extracted : {section_path.name}")

            except Exception as e:
                print(f"  ERROR rendering {t_name}: {e}")


if __name__ == "__main__":
    main()
