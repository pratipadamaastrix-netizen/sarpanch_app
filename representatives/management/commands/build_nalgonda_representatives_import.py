"""
Build Representative bulk-import Excel from NALGONDA DISTRICT NEW SARPANCH DETAILS .xlsx
using master LocalBody rows (district, constituency, mandal, village names from DB).
"""

from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand

from locations.management.commands.export_nalgonda_sheet_gaps import (
    _excel_mandal_lookup_key,
    _norm,
)
from locations.models import District, LocalBody, Mandal


class Command(BaseCommand):
    help = (
        "Read locations/NALGONDA DISTRICT NEW SARPANCH DETAILS .xlsx and write "
        "Nalgonda_Representatives_Import_Ready.xlsx for Django admin import."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            type=str,
            default="NALGONDA DISTRICT NEW SARPANCH DETAILS .xlsx",
            help="Filename under locations/ (default: NALGONDA DISTRICT NEW SARPANCH DETAILS .xlsx)",
        )
        parser.add_argument(
            "--out",
            type=str,
            default="",
            help="Output path (default: representatives/Nalgonda_Representatives_Import_Ready.xlsx)",
        )

    def handle(self, *args, **options):
        # sarpanch_app/locations/
        locations_dir = (
            Path(__file__).resolve().parent.parent.parent.parent / "locations"
        )
        src = locations_dir / options["input"]
        if not src.is_file():
            self.stderr.write(f"Source not found: {src}")
            return

        out = (
            Path(options["out"])
            if options["out"]
            else Path(__file__).resolve().parent.parent.parent
            / "Nalgonda_Representatives_Import_Ready.xlsx"
        )

        district = District.objects.filter(name__iexact="Nalgonda").first()
        if not district:
            self.stderr.write("District Nalgonda not found in database.")
            return

        mandal_by_key = {
            _norm(m.name): m
            for m in Mandal.objects.filter(district=district).select_related(
                "constituency", "district"
            )
        }

        df = pd.read_excel(src, header=1)
        df = df[df["Name of the mandal"].astype(str).str.strip() != "2"].copy()
        df = df.dropna(subset=["Name of the mandal"], how="all")

        ok = []
        errors = []

        for idx, r in df.iterrows():
            m_raw = r.get("Name of the mandal")
            v_raw = r.get("Name of the Grama Panchayat")
            name_raw = r.get("Name of the Sarpanch")
            mob_raw = r.get("Mobile Number")

            m_key = _excel_mandal_lookup_key(m_raw)
            v_key = _norm(v_raw)
            full_name = "" if pd.isna(name_raw) else str(name_raw).strip()
            mobile = "" if pd.isna(mob_raw) else str(mob_raw).strip()
            mobile = "".join(c for c in mobile if c.isdigit() or c == "+")
            if mobile.startswith("+91"):
                mobile = mobile[3:]
            if len(mobile) > 10 and mobile.isdigit():
                mobile = mobile[-10:]

            if not v_key or not full_name or not mobile:
                errors.append(
                    {
                        "excel_row": int(idx) + 3,
                        "reason": "Missing village, sarpanch name, or mobile",
                        "mandal_sheet": m_raw,
                        "village_sheet": v_raw,
                        "full_name": full_name,
                        "mobile": mob_raw,
                    }
                )
                continue

            m_obj = mandal_by_key.get(m_key)
            if not m_obj:
                errors.append(
                    {
                        "excel_row": int(idx) + 3,
                        "reason": "Mandal not in master (after alias map)",
                        "mandal_sheet": m_raw,
                        "mandal_key": m_key,
                        "village_sheet": v_raw,
                        "full_name": full_name,
                        "mobile": mobile,
                    }
                )
                continue

            lb = None
            for cand in LocalBody.objects.filter(
                district=district,
                mandal=m_obj,
                local_body_type="VILLAGE",
            ).select_related("constituency"):
                if _norm(cand.name) == v_key:
                    lb = cand
                    break

            if lb is None:
                errors.append(
                    {
                        "excel_row": int(idx) + 3,
                        "reason": "Village not found under this mandal in LocalBody master",
                        "district": district.name,
                        "mandal_master": m_obj.name,
                        "village_sheet": v_raw,
                        "full_name": full_name,
                        "mobile": mobile,
                    }
                )
                continue

            ok.append(
                {
                    "district": lb.district.name,
                    "constituency": lb.constituency.display_name,
                    "mandal": lb.mandal.name,
                    "village": lb.name,
                    "representative_type": "SARPANCH",
                    "full_name": full_name,
                    "email": "",
                    "age": "",
                    "mobile_number": mobile,
                    "gender": "",
                    "status": "ACTIVE",
                    "effective_from": "",
                    "effective_to": "",
                    "notes": "",
                }
            )

        out.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(out, engine="openpyxl") as w:
            pd.DataFrame(ok).to_excel(w, index=False, sheet_name="import")
            pd.DataFrame(errors).to_excel(w, index=False, sheet_name="errors")

        self.stdout.write(
            self.style.SUCCESS(
                f"Source rows: {len(df)}\n"
                f"Import rows: {len(ok)}\n"
                f"Errors: {len(errors)}\n"
                f"Wrote: {out}"
            )
        )
