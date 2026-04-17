"""
Map a client-style Excel (name, village, mandal, mobile, optional district)
to the Representative import format (district, constituency, mandal, village, ...).

Looks up LocalBody in the database so constituency is filled automatically.
Rows with no matching LocalBody are written to a separate sheet (errors).
"""

import re
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand

from locations.models import LocalBody


def _normalize_header(c) -> str:
    s = str(c).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


class Command(BaseCommand):
    help = (
        "Convert client Excel to Representative import format. "
        "Expected columns (case-insensitive): "
        "sarpanch / full_name / name, village / grama_panchayat, mandal, mobile, optional district."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            type=str,
            required=True,
            help="Path to client .xlsx",
        )
        parser.add_argument(
            "--out",
            type=str,
            default="",
            help="Output path (default: same folder as input, name Representative_Import_Ready.xlsx)",
        )
        parser.add_argument(
            "--district",
            type=str,
            default="Nalgonda",
            help="District name if not in file (default: Nalgonda)",
        )

    def handle(self, *args, **options):
        src = Path(options["input"])
        if not src.is_file():
            self.stderr.write(f"File not found: {src}")
            return

        out = Path(options["out"]) if options["out"] else src.parent / "Representative_Import_Ready.xlsx"
        default_district = (options["district"] or "Nalgonda").strip()

        df = pd.read_excel(src)
        df.columns = [_normalize_header(c) for c in df.columns]

        def pick(*names):
            for n in names:
                if n in df.columns:
                    return n
            return None

        c_name = pick(
            "full_name",
            "sarpanch_name",
            "name_of_the_sarpanch",
            "name",
            "sarpanch",
        )
        c_village = pick(
            "village",
            "name_of_the_grama_panchayat",
            "grama_panchayat",
            "gp",
            "local_body",
        )
        c_mandal = pick("mandal", "name_of_the_mandal")
        c_mobile = pick("mobile_number", "mobile", "phone", "contact")
        c_dist = pick("district")

        if not all([c_name, c_village, c_mandal, c_mobile]):
            self.stderr.write(
                f"Could not detect columns. Found: {list(df.columns)}. "
                "Need name, village, mandal, mobile (or similar headers)."
            )
            return

        ok_rows = []
        err_rows = []

        for idx, row in df.iterrows():
            full_name = row.get(c_name)
            village = row.get(c_village)
            mandal = row.get(c_mandal)
            mobile = row.get(c_mobile)
            district_name = (row.get(c_dist) if c_dist else None) or default_district
            if pd.isna(full_name) or pd.isna(village) or pd.isna(mandal) or pd.isna(mobile):
                err_rows.append(
                    {
                        "row_index": idx + 2,
                        "reason": "Missing name, village, mandal, or mobile",
                        "full_name": full_name,
                        "village": village,
                        "mandal": mandal,
                        "mobile": mobile,
                    }
                )
                continue

            fn = str(full_name).strip()
            vn = str(village).strip()
            mn = str(mandal).strip()
            mob = str(mobile).strip()
            dn = str(district_name).strip()

            qs = LocalBody.objects.filter(
                district__name=dn,
                mandal__name=mn,
                name=vn,
                local_body_type="VILLAGE",
            ).select_related("district", "constituency", "mandal")

            if qs.count() == 0:
                err_rows.append(
                    {
                        "row_index": idx + 2,
                        "reason": "No LocalBody (VILLAGE) in DB for this district/mandal/village",
                        "full_name": fn,
                        "village": vn,
                        "mandal": mn,
                        "mobile": mob,
                    }
                )
                continue
            if qs.count() > 1:
                err_rows.append(
                    {
                        "row_index": idx + 2,
                        "reason": "Multiple LocalBodies match; add constituency column manually",
                        "full_name": fn,
                        "village": vn,
                        "mandal": mn,
                        "mobile": mob,
                    }
                )
                continue

            lb = qs.first()
            ok_rows.append(
                {
                    "district": lb.district.name,
                    "constituency": lb.constituency.display_name,
                    "mandal": lb.mandal.name,
                    "village": lb.name,
                    "representative_type": "SARPANCH",
                    "full_name": fn,
                    "email": "",
                    "age": "",
                    "mobile_number": mob,
                    "gender": "",
                    "status": "ACTIVE",
                    "effective_from": "",
                    "effective_to": "",
                    "notes": "",
                }
            )

        out.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(out, engine="openpyxl") as w:
            pd.DataFrame(ok_rows).to_excel(w, index=False, sheet_name="import")
            pd.DataFrame(err_rows).to_excel(w, index=False, sheet_name="errors")

        self.stdout.write(
            self.style.SUCCESS(
                f"OK rows: {len(ok_rows)}; errors: {len(err_rows)}. Wrote: {out}"
            )
        )
