"""
Compare Nalgonda SARPANCH details Excel to master Mandal / LocalBody data
and write two workbooks: missed mandals, missed villages.

The sheet often spells mandals differently than master (spacing, TH vs Th, etc.).
We strip parenthetical qualifiers and apply a small alias map before matching.
"""

import re
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand

from locations.models import District, LocalBody, Mandal

# Excel normalized mandal name (after _strip_paren + collapse space + casefld)
# -> master mandal key from DB (_norm(m.name))
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
    """e.g. 'Gundlapally (Dindi)' -> 'Gundlapally'."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    text = re.sub(r"\s*\([^)]*\)\s*", " ", text).strip()
    return text


def _excel_mandal_lookup_key(raw) -> str:
    cleaned = _strip_paren_for_mandal(raw)
    n = _norm(cleaned)
    return NALGONDA_SHEET_MANDAL_ALIASES.get(n, n)


class Command(BaseCommand):
    help = (
        "Read NALGONDA DISTRICT NEW SARPANCH DETAILS Excel and export "
        "missed mandals / missed villages vs MySQL master data."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            type=str,
            default="NALGONDA DISTRICT NEW SARPANCH DETAILS .xlsx",
            help="Excel filename inside locations/ (default: NALGONDA... .xlsx)",
        )

    def handle(self, *args, **options):
        locations_dir = Path(__file__).resolve().parent.parent.parent
        src = locations_dir / options["input"]
        if not src.is_file():
            self.stderr.write(f"Input not found: {src}")
            return

        df = pd.read_excel(src, header=1)
        df = df[df["Name of the mandal"].astype(str).str.strip() != "2"].copy()
        df = df.dropna(subset=["Name of the mandal"], how="all")

        district = District.objects.filter(name__iexact="Nalgonda").first()
        if not district:
            self.stderr.write("District 'Nalgonda' not found in database.")
            return

        db_mandals = {
            _norm(m.name): m
            for m in Mandal.objects.filter(district=district)
        }
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

        missed_mandals_rows = [
            {
                "district": district.name,
                "mandal_name_as_in_sheet_norm_key": mk,
                "note": "No Mandal in master for this district after sheet normalization",
            }
            for mk in missed_mandal_keys
        ]
        df_missed_mandals = pd.DataFrame(missed_mandals_rows)

        missed_village_rows = []
        for _, r in df.iterrows():
            m_raw = r.get("Name of the mandal")
            v_raw = r.get("Name of the Grama Panchayat")
            m_key = _excel_mandal_lookup_key(m_raw)
            v_key = _norm(v_raw)
            if not v_key:
                continue

            mandal_in_master = m_key in db_mandals
            db_mandal_name_for_pair = (
                db_mandals[m_key].name if mandal_in_master else ""
            )
            in_db = mandal_in_master and (
                _norm(db_mandal_name_for_pair),
                v_key,
            ) in village_set
            if in_db:
                continue

            missed_village_rows.append(
                {
                    "district": district.name,
                    "mandal_as_in_sheet": m_raw,
                    "mandal_match_key_used": m_key,
                    "grama_panchayat_as_in_sheet": v_raw,
                    "mandal_in_master": "Yes" if mandal_in_master else "No",
                    "master_mandal_name_if_found": db_mandal_name_for_pair,
                    "name_of_the_sarpanch": r.get("Name of the Sarpanch"),
                    "mobile_number": r.get("Mobile Number"),
                }
            )

        df_missed_villages = pd.DataFrame(missed_village_rows)

        out_mandals = locations_dir / "Nalgonda_mandals_missing_in_master.xlsx"
        out_villages = locations_dir / "Nalgonda_villages_missing_in_master.xlsx"

        with pd.ExcelWriter(out_mandals, engine="openpyxl") as w:
            df_missed_mandals.to_excel(w, index=False, sheet_name="missed_mandals")
        with pd.ExcelWriter(out_villages, engine="openpyxl") as w:
            df_missed_villages.to_excel(w, index=False, sheet_name="missed_villages")

        self.stdout.write(
            self.style.SUCCESS(
                f"Excel rows processed: {len(df)}\n"
                f"Unique mandal keys from sheet (after normalization): {len(excel_keys)}\n"
                f"Mandals in master for {district.name}: {len(db_mandals)}\n"
                f"Missed mandals (still not in master): {len(missed_mandal_keys)}\n"
                f"Missed village rows: {len(missed_village_rows)}\n"
                f"Wrote: {out_mandals}\n"
                f"Wrote: {out_villages}"
            )
        )
