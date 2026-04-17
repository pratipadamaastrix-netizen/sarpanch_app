"""One-off: print Nalgonda sheet vs DB gap counts (no Excel write). Run: python locations/_verify_nalgonda_gap_inline.py from sarpanch_app."""
import os
import re
import sys

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import pandas as pd  # noqa: E402
from locations.models import District, LocalBody, Mandal  # noqa: E402

NALGONDA_SHEET_MANDAL_ALIASES = {
    "adavidevulapalli": "adavi devulapally",
    "chintha pally": "chintapally",
    "chityala": "chityal",
    "gattuppal": "ghatuppal",
    "kethe pally": "kethepally",
    "thipparthi": "thipparthy",
    "tirumalagiri sagar": "thirumalagiri sagar",
    "vemula pally": "vemulapally",
}


def _norm(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    return " ".join(text.split()).casefold()


def _strip_paren_for_mandal(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s*\([^)]*\)\s*", " ", text).strip()
    return text


def _excel_mandal_lookup_key(raw) -> str:
    cleaned = _strip_paren_for_mandal(raw)
    n = _norm(cleaned)
    return NALGONDA_SHEET_MANDAL_ALIASES.get(n, n)


def main():
    base = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(base, "NALGONDA DISTRICT NEW SARPANCH DETAILS .xlsx")
    if not os.path.isfile(src):
        print("Source Excel not found:", src)
        return

    df = pd.read_excel(src, header=1)
    df = df[df["Name of the mandal"].astype(str).str.strip() != "2"].copy()
    df = df.dropna(subset=["Name of the mandal"], how="all")

    district = District.objects.filter(name__iexact="Nalgonda").first()
    if not district:
        print("District Nalgonda not found")
        return

    db_mandals = {_norm(m.name): m for m in Mandal.objects.filter(district=district)}
    village_set = set()
    for lb in LocalBody.objects.filter(
        district=district, local_body_type="VILLAGE"
    ).select_related("mandal"):
        village_set.add((_norm(lb.mandal.name), _norm(lb.name)))

    excel_keys = sorted(
        {
            _excel_mandal_lookup_key(r["Name of the mandal"])
            for _, r in df.iterrows()
            if _excel_mandal_lookup_key(r["Name of the mandal"])
        }
    )
    missed_mandal_keys = [k for k in excel_keys if k not in db_mandals]

    missed_village_rows = 0
    matched_rows = 0
    for _, r in df.iterrows():
        m_key = _excel_mandal_lookup_key(r["Name of the mandal"])
        v_key = _norm(r.get("Name of the Grama Panchayat"))
        if not v_key:
            continue
        mandal_in_master = m_key in db_mandals
        if not mandal_in_master:
            missed_village_rows += 1
            continue
        db_name = db_mandals[m_key].name
        if (_norm(db_name), v_key) in village_set:
            matched_rows += 1
        else:
            missed_village_rows += 1

    print("=== Nalgonda vs source sheet (NALGONDA DISTRICT NEW SARPANCH DETAILS .xlsx) ===")
    print(f"Sheet data rows (with GP name): {len(df)}")
    print(f"Mandals in DB (Nalgonda): {len(db_mandals)}")
    print(f"Unique mandal keys from sheet (normalized): {len(excel_keys)}")
    print(f"Missed mandals (in sheet, not in DB): {len(missed_mandal_keys)}")
    if missed_mandal_keys:
        print("  Keys:", missed_mandal_keys)
    print(f"Sheet rows matched to DB village (mandal+name): {matched_rows}")
    print(f"Sheet rows still NOT in DB (missing village or mandal): {missed_village_rows}")
    print(f"Total VILLAGE LocalBodies in DB for Nalgonda: {LocalBody.objects.filter(district=district, local_body_type='VILLAGE').count()}")


if __name__ == "__main__":
    main()
