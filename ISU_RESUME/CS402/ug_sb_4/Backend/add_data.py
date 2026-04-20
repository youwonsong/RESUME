from pathlib import Path
from docxtpl import DocxTemplate, RichText
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

        # ── Budget total: round(TDC) + round(Indirect) ────────────────────────
        # This ensures the three displayed values (Direct, Indirect, Budget)
        # always sum correctly without floating-point accumulation error.
        if out["tdc_total"] is not None and out["indirect_total"] is not None:
            out["budget_total"] = round(out["tdc_total"]) + round(out["indirect_total"])

    except Exception:
        pass   # caller uses computed fallbacks
    return out


# ── Formatting helpers ────────────────────────────────────────────────────────

def money(x):
    try:
        return "${:,.0f}".format(round(float(x)))
    except (ValueError, TypeError):
        return "$0"

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

_NUM_WORDS = {0:"zero",1:"one",2:"two",3:"three",4:"four",5:"five",
              6:"six",7:"seven",8:"eight",9:"nine",10:"ten"}

def num_word(n):
    """Convert a small integer to its English word (2 → 'two'). Falls back to str."""
    try:
        return _NUM_WORDS.get(int(float(n)), str(int(float(n))))
    except (ValueError, TypeError):
        return str(n)


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


# ── Config sheet reader ──────────────────────────────────────────────────────

def _read_config(data_path: str) -> dict:
    """
    Read the 'Config' sheet from the spreadsheet.
    Expected layout:
        A: Field name   B: Value
    Returns a dict {field_name: value_string}.
    Falls back to empty dict if sheet is missing.
    """
    if not data_path:
        return {}
    try:
        df = pd.read_excel(data_path, sheet_name="Config", header=0)
        config = {}
        for _, row in df.iterrows():
            key = str(row.iloc[0]).strip()
            val = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
            if key and key != "nan":
                config[key] = val
        return config
    except Exception:
        return {}


# ── Tuition year/term detail extractor ───────────────────────────────────────

def _extract_tuition_years(data_path: str, n_years: int) -> list:
    """
    Read per-year, per-term tuition details from the Tuition sheet.

    Returns a list of n_years dicts, each with:
        year   – "1", "2", …
        terms  – list of {"count": "2", "term": "Fall 2026"} for non-zero terms

    Column layout (0-indexed) in the Tuition sheet:
        Year counts   : cols 2, 4, 5, 6, 7  for years 1-5
        Term names    : cols 10, 12, 14, 16, 18  for years 1-5
    Term rows for the active PhD section: Summer (+0), Fall (+2), Spring (+4)
    """
    if not data_path:
        return []
    try:
        df = pd.read_excel(data_path, sheet_name="Tuition", header=None)

        yr_count_cols = [2, 4, 5, 6, 7][:n_years]
        yr_term_cols  = [10, 12, 14, 16, 18][:n_years]

        # Find the active PhD-students row (first one with any non-zero Year count)
        active_phd_row = None
        for i, row in df.iterrows():
            label = str(row.iloc[0]).strip().lower()
            if "phd students" in label and "enter no" in label:
                try:
                    counts = [float(str(row.iloc[c]).strip())
                              for c in yr_count_cols
                              if c < len(row) and str(row.iloc[c]).strip() not in ("nan", "")]
                    if any(c > 0 for c in counts):
                        active_phd_row = i
                        break
                except (ValueError, TypeError):
                    pass

        if active_phd_row is None:
            return []

        fall_row   = active_phd_row + 2
        spring_row = active_phd_row + 4

        result = []
        for yi in range(n_years):
            cc, tc = yr_count_cols[yi], yr_term_cols[yi]
            terms = []
            for row_idx in [active_phd_row, fall_row, spring_row]:
                if row_idx >= len(df):
                    continue
                row = df.iloc[row_idx]
                count_str = str(row.iloc[cc]).strip() if cc < len(row) else ""
                term_str  = str(row.iloc[tc]).strip() if tc < len(row) else ""
                if count_str in ("nan", "", "0") or term_str in ("nan", ""):
                    continue
                try:
                    count_val = int(float(count_str))
                    if count_val > 0:
                        terms.append({"count": str(count_val), "term": term_str})
                except (ValueError, TypeError):
                    pass
            result.append({"year": str(yi + 1), "terms": terms})
        return result
    except Exception:
        return []


def _build_tuition_years(year_totals: list, year_details: list) -> list:
    """
    Merge per-year tuition totals with per-term details into a single list.
    year_totals  – from tui["years"]: [{"year":"1","total":"$X"}, …]
    year_details – from _extract_tuition_years(): [{"year":"1","terms":[…]}, …]
    Returns      – [{"year":"1","total":"$X","terms":[{"count":"2","term":"Fall 2026"},…]}, …]
    """
    detail_map = {d["year"]: d.get("terms", []) for d in year_details}
    result = []
    for yt in year_totals:
        yr    = yt["year"]
        terms = detail_map.get(yr, [])
        # Pre-format as plain string so Template3 doesn't need inline Jinja2 loops
        if terms:
            parts = [
                f"{t['count']} student{'s' if int(t['count']) != 1 else ''} for {t['term']} term"
                for t in terms
            ]
            terms_text = "Tuition total is for " + ", ".join(parts) + "."
        else:
            terms_text = ""
        result.append({
            "year":       yr,
            "total":      yt["total"],
            "terms":      terms,
            "terms_text": terms_text,   # ready-to-use string for Template3
        })
    return result


def _build_travel_lines(travel_years: list) -> list:
    """
    Flatten travel_years into a single list of text lines for Template3.
    Avoids nested {%p for %} loops which can corrupt docxtpl XML.

    Each element: {"text": str}
    Structure per year:
        Year X: $TOTAL
        Travel to [purpose] for [N] person(s). Airfare …
        Travel to …  (repeat per trip)
    """
    lines = []
    for i, yr in enumerate(travel_years):
        n = yr['year']
        # Blank line between years (before year 2, 3, …)
        if i > 0:
            lines.append({"rtext": RichText()})
        # Header line — only "Year X:" underlined, rest plain
        rt_header = RichText()
        rt_header.add(f"Year {n}:", underline=True)
        rt_header.add(f" {yr['total']}   Year {n} Domestic Travel (Yr{n}TravelDom)")
        lines.append({"rtext": rt_header})
        # Trip detail lines — plain
        for t in yr.get("trips", []):
            detail_text = (
                f"Travel to {t['purpose']} for {t['people']} person(s). "
                f"Airfare is estimated at {t['airfare']}. "
                f"Lodging total is {t['lodging_total']}, estimated at "
                f"{t['nights']} nights at {t['rate_per_night']}. "
                f"Meals total is {t['meals_total']}, estimated at "
                f"{t['meal_days']} meal days at {t['meal_per_day']} "
                f"and Registration costs are estimated as {t['registration']}. "
                f"Ground transportation costs are estimated to be {t['ground_transport']}."
            )
            rt_detail = RichText()
            rt_detail.add(detail_text, bold=False)
            lines.append({"rtext": rt_detail})
    return lines


def _build_tuition_lines(year_totals: list, year_details: list) -> list:
    """
    Flatten tuition year/term data into a single list of text lines for Template3.

    Each element: {"text": str}
    Structure per year:
        Year X: $TOTAL
        Tuition total is for N students for Fall 2026 term, …
    """
    tuition_years = _build_tuition_years(year_totals, year_details)
    lines = []
    for i, yr in enumerate(tuition_years):
        # Blank line between years (before year 2, 3, …)
        if i > 0:
            lines.append({"text": ""})
        lines.append({"text": f"Year {yr['year']}: {yr['total']}"})
        if yr.get("terms_text"):
            lines.append({"text": yr["terms_text"]})
    return lines


# ── Materials item extractor ─────────────────────────────────────────────────

def _extract_materials_items(data_path: str, n_years: int) -> list:
    """
    Read individual materials line-items from the Summary sheet.

    The spreadsheet's G-section sometimes has sub-rows directly below the
    "Materials and Supplies" category row.  Each sub-row has a text label in
    column C and year-cost values in the year columns.  Those rows are returned
    as a list of dicts with keys:
        name      – item label (str)
        cost      – total cost formatted as "$X,XXX" (str)
        quantity  – number of units inferred from the label (str), default "1"

    Returns an empty list when no sub-rows are found or data_path is empty.
    """
    if not data_path:
        return []
    try:
        df = pd.read_excel(data_path, sheet_name="Summary", header=None)

        # Locate "Materials and Supplies" row and the next G-section category row
        mat_mask   = df.iloc[:, 2].astype(str).str.strip().str.lower() == "materials and supplies"
        mat_rows   = df[mat_mask]
        if mat_rows.empty:
            return []

        mat_idx = mat_rows.index[0]

        # Keywords that mark the START of the next G-section category row.
        # Using prefix matching so singular/plural/minor wording differences
        # are all caught (e.g. "Publication cost" and "Publication costs" both
        # start with "publication").
        stop_keywords = [
            "publication",
            "consultant",
            "computer service",
            "equipment or facility",
            "off site",
            "alteration",
            "subaward",
            "tuition",
            "subtotal",
            "third party",
            "postage",
            "telecom",
            "not subject",
            "other",
        ]

        # Find year columns (columns 7, 9, 11, … for Year1, Year2, Year3, …)
        # Column H (index 7) is Year 1, J (9) Year 2, L (11) Year 3, …
        year_col_indices = [7 + 2 * i for i in range(n_years)]

        items = []
        for idx in range(mat_idx + 1, min(mat_idx + 20, len(df))):
            row = df.iloc[idx]
            label = str(row.iloc[2]).strip()
            col_a = str(row.iloc[0]).strip()

            # Stop at a new section letter (A-H) in col A
            if col_a and col_a.upper() in list("ABCDEFGH"):
                break
            # Stop at empty/nan labels
            if label == "nan" or label == "":
                break
            # Stop at any known next-category label (prefix-based, case-insensitive)
            if any(label.lower().startswith(kw) for kw in stop_keywords):
                break

            # Sum year costs for this sub-row
            year_vals = []
            for ci in year_col_indices:
                if ci < len(row):
                    v = row.iloc[ci]
                    try:
                        year_vals.append(float(v) if not pd.isna(v) else 0.0)
                    except (TypeError, ValueError):
                        year_vals.append(0.0)
                else:
                    year_vals.append(0.0)

            total = sum(year_vals)
            if total <= 0:
                continue  # skip $0 sub-items

            # Infer quantity from label (e.g. "2 Desktop Computers" → quantity=2)
            import re as _re
            qty_match = _re.match(r'^(\d+)\s+', label)
            quantity  = qty_match.group(1) if qty_match else "1"

            items.append({
                "name":     label,
                "cost":     "${:,.0f}".format(total),
                "quantity": quantity,
            })

        return items
    except Exception:
        return []


# ── Main context builder ──────────────────────────────────────────────────────

def build_context(ext: Extractor, spreadsheet_name: str = "",
                   data_path: str = "") -> dict:
    """
    Build the Jinja2 template context dict from an Extractor.
    Budget totals and the indirect rate are read directly from the spreadsheet's
    own formula rows so the output matches the spreadsheet exactly.
    Works with any number of years and any ISU budget spreadsheet.
    """

    # Fall back to the Extractor's own path if caller didn't supply one
    # (e.g. when Flask calls build_context(extract) without data_path)
    if not data_path:
        data_path = getattr(ext, "data_path", "") or ""

    # ── 1. Extract from Excel ─────────────────────────────────────────────────
    n_years,  key_df    = ext.grab_key_personnel(False)
    _,        other_df  = ext.grab_other_personnel(False)
    _,        ben_df    = ext.grab_benefits(False)
    _,        direct_df = ext.grab_direct_cost(False)
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
    faculty_names_list   = []
    ps_names_list        = []   # ALL P&S names (key + other) → used by Template1
    other_ps_names_list  = []   # only OTHER-personnel P&S → used by Template2
    key_personnel        = []
    total_key_cost       = 0.0

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
        if hours_val == 0:
            hours_val = 40   # default to 40 hrs/month when blank

        try:
            raw_base = float(row.get("Base Rate", 18) or 18)
            # Base Rate in the spreadsheet can be either:
            #   - a true hourly rate  (e.g. $18/hr)  when <= $100
            #   - a monthly salary    (e.g. $720/mo)  when > $100
            # For UG students the spreadsheet stores the monthly amount;
            # we derive the hourly rate by dividing by hours per month.
            if raw_base > 100:
                rate_val = raw_base / hours_val   # monthly → hourly
            else:
                rate_val = raw_base               # already hourly
        except (ValueError, TypeError):
            rate_val = 18.0

        try:   count_val = int(float(row.get("Employee Count", 1) or 1))
        except: count_val = 1

        # Annual base salary for P&S staff (monthly base rate × 12 months)
        # Shown in Template1 as "(Base Salary for year 1: $X)"
        annual_base = money(raw_base * 12) if target == "ps" and raw_base > 100 else ""

        other_list.append({
            "role":              display_role,
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
                    ps_names_list.append(actual_last)    # last name for Template1 fringe table
                # Track other-personnel P&S names separately for Template2 (full name)
                if actual_name not in other_ps_names_list:
                    other_ps_names_list.append(actual_name)

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

    dynamic_faculty_names  = ", ".join(faculty_names_list)      if faculty_names_list      else "Faculty"
    dynamic_ps_names       = ", ".join(ps_names_list)           if ps_names_list           else "P&S Staff"
    dynamic_other_ps_names = ", ".join(other_ps_names_list)     if other_ps_names_list     else "P&S Staff"

    order_map = {"grad": 1, "ug": 2, "ps": 3, "postdoc": 4}
    other_list.sort(key=lambda x: order_map.get(x["target"], 99))

    # ── 5. TRAVEL ─────────────────────────────────────────────────────────────
    travel_list       = []
    total_travel_val  = 0.0
    travel_year_totals = []   # filled below if travel data exists

    # Supplement travel_df with NaN-purpose rows that data_extraction drops.
    # These are real travel entries where the purpose cell was left blank.
    try:
        _raw = ext.travel_data.iloc[
            ext.domestic_index + 2 : ext.international_index - 1, :
        ].reset_index(drop=True)
        _raw.columns = _raw.iloc[0].values
        _raw = _raw.drop(index=0).reset_index(drop=True)
        _missing = _raw[
            _raw["Purpose & Destination"].isna()
            & pd.to_numeric(_raw["Year"],  errors="coerce").notna()
            & (pd.to_numeric(_raw["TOTAL"], errors="coerce") > 0)
        ].copy()
        if not _missing.empty:
            travel_df = pd.concat([travel_df, _missing], ignore_index=True)
    except Exception:
        pass   # fall back to the rows we already have

    if not travel_df.empty:
        grouped_travel = {}

        for _, row in travel_df.iterrows():
            try:    t_total = float(row.get("TOTAL", 0) or 0)
            except: t_total = 0.0
            if t_total == 0:
                continue

            raw_purpose = str(row.get("Purpose & Destination", "") or "")
            # Treat blank / NaN purpose as "Unknown" for categorisation
            if raw_purpose in ("", "nan", "None"):
                raw_purpose = "Unknown"
            p_lower = raw_purpose.lower()

            raw_year = str(row.get("Year", "1") or "1")
            y_list   = [y.strip() for y in re.findall(r'\d+', raw_year)]
            if not y_list:
                y_list = [raw_year]

            try:    people = int(float(row.get("# of People", 1) or 1))
            except: people = 1
            if people == 0:
                people = 1

            is_year1 = "1" in y_list

            # Read cost components to classify the trip type
            try:    airfare      = float(row.get("Airfare/ Person",         0) or 0)
            except: airfare      = 0.0
            try:    registration = float(row.get("Registration Per Person", 0) or 0)
            except: registration = 0.0
            try:    hotel        = float(row.get("Lodging Total",           0) or 0)
            except: hotel        = 0.0
            try:    meals        = float(row.get("Meal Total",              0) or 0)
            except: meals        = 0.0
            try:    mileage      = float(row.get("Ground Transportation",   0) or 0)
            except: mileage      = 0.0
            per_trip = airfare + registration + hotel + meals + mileage

            # Classify trip:
            #  - "field"      : only mileage/meals, no airfare, no registration
            #  - "conference" : has airfare OR registration (AWRA, NeurIPS, etc.)
            #  - raw_purpose  : anything else
            if "visit" in p_lower or "field" in p_lower or (
                    airfare == 0 and registration == 0 and mileage > 0):
                cat = "field"
            elif (airfare > 0 or registration > 0
                  or "conference" in p_lower or "neurips" in p_lower
                  or "awra" in p_lower or raw_purpose == "Unknown"):
                cat = "conference"
            else:
                cat = raw_purpose

            total_travel_val += t_total

            if cat not in grouped_travel:
                grouped_travel[cat] = {
                    "purpose":           raw_purpose,
                    "years_list":        y_list[:],
                    "total_val":         t_total,
                    "year1_val":         t_total if is_year1 else 0,
                    # per-year tracking for people & weighted cost sum.
                    # cost_by_year stores per_trip*people (total cost) so we can
                    # compute the true average per-person cost at the end:
                    #   avg_per_person = cost_by_year[y] / people_by_year[y]
                    "people_by_year":    {y: people         for y in y_list},
                    "cost_by_year":      {y: per_trip * people for y in y_list},
                    "airfare":           money(airfare),
                    "registration":      money(registration),
                    "hotel":             money(hotel),
                    "nights":            (lambda v: 0 if pd.isna(v) else int(float(v)))(row.get("# Nights",    0) or 0),
                    "meal_days":         (lambda v: 0 if pd.isna(v) else int(float(v)))(row.get("# Meal Days", 0) or 0),
                    "expenses":          money(meals),
                    "mileage":           money(mileage),
                }
            else:
                grouped_travel[cat]["total_val"] += t_total
                if is_year1:
                    grouped_travel[cat]["year1_val"] += t_total
                for y in y_list:
                    if y not in grouped_travel[cat]["years_list"]:
                        grouped_travel[cat]["years_list"].append(y)
                    # Accumulate people and cost per year (rows sharing a year = same trip)
                    pby = grouped_travel[cat]["people_by_year"]
                    cby = grouped_travel[cat]["cost_by_year"]
                    pby[y] = pby.get(y, 0) + people
                    cby[y] = cby.get(y, 0) + per_trip * people

        pi_last = key_personnel[0]["last_name"] if key_personnel else ""

        for cat, data in grouped_travel.items():
            yl = sorted(data["years_list"])
            if len(yl) > 2:    years_str = ", ".join(yl[:-1]) + f", and {yl[-1]}"
            elif len(yl) == 2: years_str = f"{yl[0]} and {yl[1]}"
            else:              years_str = yl[0]

            # trip_type used by templates to distinguish field / conference / other
            if cat == "field":
                trip_type = "field"
            elif cat == "conference":
                trip_type = "conference"
            else:
                trip_type = "other"

            # Compute per-trip people count and per-person cost from year-based tracking.
            # Year 1 is most representative; fall back to the year with the most people.
            people_by_year = data["people_by_year"]
            cost_by_year   = data["cost_by_year"]
            if "1" in people_by_year:
                num_people     = people_by_year["1"]
                y1_trip_cost   = cost_by_year["1"]
            else:
                ref_year       = max(people_by_year, key=people_by_year.get)
                num_people     = people_by_year[ref_year]
                y1_trip_cost   = cost_by_year[ref_year]
            per_person_cost = y1_trip_cost / num_people if num_people > 0 else y1_trip_cost

            # Attendee description for conference trips
            if trip_type == "conference":
                att_desc = f"(graduate student and PI {pi_last})" if pi_last else ""
            else:
                att_desc = ""

            # Human-readable label used in Template1 travel header line
            if trip_type == "field":
                t_label = "Field Visits (US)"
            elif trip_type == "conference":
                t_label = "Conference Attendance (US)"
            else:
                t_label = data["purpose"]

            travel_list.append({
                "purpose":        data["purpose"],
                "label":          t_label,
                "trip_type":      trip_type,            # "field" / "conference" / "other"
                "years":          years_str,
                "has_year_1":     "1" in data["years_list"],
                "people":         str(num_people),
                "people_word":    num_word(num_people),
                "per_trip_cost":  money(per_person_cost),
                "airfare":        data["airfare"],
                "registration":   data["registration"],
                "hotel":          data["hotel"],
                "nights":         data["nights"],
                "nights_text":    num_word(data["nights"]),
                "meal_days":      data["meal_days"],
                "meal_days_text": num_word(data["meal_days"]),
                "expenses":       data["expenses"],
                "mileage":        data["mileage"],
                "total":          money(data["total_val"]),
                "year1_total":    money(data.get("year1_val", 0)),
                "attendee_desc":  att_desc,
            })

    def get_travel_order(item):
        if item["trip_type"] == "field":      return 1
        if item["trip_type"] == "conference": return 2
        return 3

    travel_list.sort(key=get_travel_order)

    # Compute per-year travel totals for Template3 year-by-year breakdown
    if grouped_travel:
        travel_by_year_val = {}
        for cat_data in grouped_travel.values():
            for yr_key, yr_cost in cat_data["cost_by_year"].items():
                travel_by_year_val[yr_key] = travel_by_year_val.get(yr_key, 0) + yr_cost
        travel_year_totals = [
            {"year": str(yi), "label": f"Year {yi}",
             "total": money(travel_by_year_val.get(str(yi), 0))}
            for yi in range(1, n_years + 1)
        ]

    # Build travel_years: per-year list with individual trip rows for Template3
    # Each year contains the year total and a list of trips with full detail.
    travel_years = []
    if not travel_df.empty:
        def _safe_float(val, default=0.0):
            try:    return float(val) if not pd.isna(val) else default
            except: return default
        def _safe_int(val, default=0):
            try:    return int(float(val)) if not pd.isna(val) else default
            except: return default

        for yi in range(1, n_years + 1):
            yr_key  = str(yi)
            yr_rows = travel_df[travel_df["Year"].astype(str).str.strip() == yr_key]
            trips, yr_total_val = [], 0.0
            for _, row in yr_rows.iterrows():
                t_total = _safe_float(row.get("TOTAL", 0))
                if t_total == 0:
                    continue
                yr_total_val += t_total
                airfare  = _safe_float(row.get("Airfare/ Person",       0))
                nights   = _safe_int  (row.get("# Nights",              0))
                rate_pn  = _safe_float(row.get("Rate per Night",        0))
                lodging  = _safe_float(row.get("Lodging Total",         0))
                meal_days= _safe_int  (row.get("# Meal Days",           0))
                meal_pd  = _safe_float(row.get("Meal Cost per Day",     0))
                meals    = _safe_float(row.get("Meal Total",            0))
                ground   = _safe_float(row.get("Ground Transportation", 0))
                reg      = _safe_float(row.get("Registration Per Person", 0))
                people   = _safe_int  (row.get("# of People",           1)) or 1
                purpose  = str(row.get("Purpose & Destination", "") or "").strip()
                trips.append({
                    "purpose":        purpose if purpose else "travel",
                    "people":         str(people),
                    "airfare":        money(airfare),
                    "lodging_total":  money(lodging),
                    "nights":         str(nights),
                    "rate_per_night": money(rate_pn),
                    "meals_total":    money(meals),
                    "meal_days":      str(meal_days),
                    "meal_per_day":   money(meal_pd),
                    "registration":   money(reg),
                    "ground_transport": money(ground),
                    "total":          money(t_total),
                })
            travel_years.append({
                "year":  yr_key,
                "total": money(yr_total_val),
                "trips": trips,
            })

    # ── 6. OTHER DIRECT COSTS ─────────────────────────────────────────────────
    def get_cost_dict(keyword):
        if direct_df.empty:
            return {"y1": "$0", "y2": "$0", "total": "$0", "years": []}
        matches = direct_df[
            direct_df["Cost"].str.contains(keyword, na=False, case=False, regex=True)
        ]
        if matches.empty:
            return {"y1": "$0", "y2": "$0", "total": "$0", "years": []}
        y_cols_d = [c for c in matches.columns if "Year" in c]
        # Sum ALL matching rows (e.g. Tuition has multiple sub-rows)
        y1    = matches[y_cols_d[0]].sum() if len(y_cols_d) > 0 else 0
        y2    = matches[y_cols_d[1]].sum() if len(y_cols_d) > 1 else 0
        total = matches[y_cols_d].sum().sum()
        years = [
            {"year": str(i + 1), "label": f"Year {i + 1}", "total": money(matches[col].sum())}
            for i, col in enumerate(y_cols_d)
        ]
        return {"y1": money(y1), "y2": money(y2), "total": money(total), "years": years}

    mat = get_cost_dict("Materials")
    pub = get_cost_dict("Publication")
    con = get_cost_dict("Consultant|Professional Services")
    tui = get_cost_dict("Tuition")
    sto = get_cost_dict("Storage|Computing|Computer|^Other$")
    pla = get_cost_dict("Planet")

    # ── Equipment (Section D in the Summary sheet) ────────────────────────────
    # grab_direct_cost() covers Section G only; read Section D separately.
    equip_total_val = 0.0
    if data_path:
        try:
            _edf = pd.read_excel(data_path, sheet_name="Summary", header=None)
            d_mask = _edf.iloc[:, 0].astype(str).str.strip() == "D"
            d_row  = _edf[d_mask]
            if not d_row.empty:
                equip_total_val = sum(
                    float(v) for v in d_row.iloc[0].values
                    if isinstance(v, (int, float)) and v > 0
                )
        except Exception:
            pass

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
        "pi_months":              key_personnel[0]["total_months"]   if key_personnel else "0",
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
        "ps_names":               dynamic_ps_names,        # Template1: all P&S (key + other)
        "other_ps_names":         dynamic_other_ps_names,  # Template2: other-personnel P&S only

        "n_years": n_years,

        # Personnel cost subtotals
        "total_key_personnel_cost":   money(total_key_cost),
        "total_other_personnel_cost": money(total_other_cost),
        "total_salary_wages_fringe":  money(total_salary_fringe),

        # Travel
        "travel_details":      travel_list,
        "total_travel":        money(total_travel_val),
        "travel_year_totals":  travel_year_totals,   # per-year totals (simple, legacy)
        "travel_years":        travel_years,          # per-year + per-trip details
        "travel_lines":        _build_travel_lines(travel_years),  # flat list for Template3

        # Other direct cost line items
        "materials":   mat,
        "publication": pub,
        "consultant":  con,
        "tuition":     tui,
        "storage":     sto,
        "planet":      pla,

        # Equipment (Section D)
        "equipment_total":          money(equip_total_val),

        # Flat aliases for Template1 direct-cost line items
        "materials_total":          mat["total"],
        "publication_total":        pub["total"],
        "publication_per_article":  pub["y2"] if pub["y2"] != "$0" else pub["y1"],
        "consultant_total":         con["total"],
        "tuition_total":            tui["total"],
        "tuition_year_totals":      tui.get("years", []),  # per-year totals (simple, legacy)
        "tuition_years":            _build_tuition_years(
                                        tui.get("years", []),
                                        _extract_tuition_years(data_path, n_years),
                                    ),
        "tuition_lines":            _build_tuition_lines(
                                        tui.get("years", []),
                                        _extract_tuition_years(data_path, n_years),
                                    ),  # flat list for Template3
        "storage_total":            sto["total"],
        "storage_rate":             "$8",        # Cylo server at ABE: $8/TB/yr
        "storage_total_tb":         (lambda v: "{:g}".format(v / 8 / n_years) if v > 0 and n_years > 0 else "")(
                                        float(sto["total"].replace("$","").replace(",","")) if sto["total"] != "$0" else 0
                                    ),
        "storage_server_life_tb":   (lambda v: "{:g}".format(v / 8 / 5) if v > 0 else "")(
                                        float(sto["total"].replace("$","").replace(",","")) if sto["total"] != "$0" else 0
                                    ),
        "planet_total":             pla["total"],
        "planet_rate":              (pla["y1"] + "/yr") if pla["y1"] != "$0" else "",
        "materials_list":           _extract_materials_items(data_path, n_years),

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

    # ── SPREADSHEET SELECTION ─────────────────────────────────────────────────
    # Set TARGET_SPREADSHEET to a specific filename to process only that file.
    # Leave as None to process every .xlsm / .xlsx in the spreadsheets folder.
    TARGET_SPREADSHEET = "PD7040 Budget_ISU_USDA_DSFAS_Gelder _tuition"   # ← change this to switch spreadsheets
    #TARGET_SPREADSHEET = "test"   # ← change this to switch spreadsheets
    #TARGET_SPREADSHEET = "test2"   # ← change this to switch spreadsheets
    # TARGET_SPREADSHEET = None         # ← uncomment to process all files
    # ─────────────────────────────────────────────────────────────────────────

    if TARGET_SPREADSHEET:
        target_path = spreadsheet_dir / TARGET_SPREADSHEET
        if not target_path.exists():
            # Try appending common extensions automatically
            for ext in (".xlsm", ".xlsx"):
                candidate = spreadsheet_dir / (TARGET_SPREADSHEET + ext)
                if candidate.exists():
                    target_path = candidate
                    break
            else:
                print(f"Spreadsheet not found: {target_path}")
                return
        xlsm_files = [target_path]
    else:
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

        for t_name in ["Template1.docx", "Template2.docx", "Template3.docx", "Template4.docx"]:
            template_path = base / "templates" / t_name
            if not template_path.exists():
                print(f"  Template not found: {t_name}")
                continue

            try:
                doc = DocxTemplate(str(template_path))
                doc.render(ctx, autoescape=True)
                add_section(
                    doc,
                    "Additional Information",
                    "This is just a section to list out some other key details",
                )
                output_path = outputs_dir / f"{spreadsheet_name}_{t_name}"
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
