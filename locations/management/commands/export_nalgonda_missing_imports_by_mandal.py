"""
Build LocalBody bulk-import Excel files (one per mandal) from
Nalgonda_villages_missing_in_master.xlsx using master Mandal to Constituency links.
"""

import re
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand

from locations.models import District, Mandal


def _safe_filename_part(name: str) -> str:
    s = re.sub(r'[<>:"/\\|?*]', "", str(name).strip())
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "mandal"


class Command(BaseCommand):
    help = (
        "From Nalgonda_villages_missing_in_master.xlsx, write one "
        "{Mandal}_Constituency_LocalBody_Import.xlsx per mandal."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            type=str,
            default="Nalgonda_villages_missing_in_master.xlsx",
            help="Source workbook in locations/ (default: Nalgonda_villages_missing...)",
        )
        parser.add_argument(
            "--out-dir",
            type=str,
            default="",
            help="Output folder (default: same as locations app)",
        )

    def handle(self, *args, **options):
        locations_dir = Path(__file__).resolve().parent.parent.parent
        src = locations_dir / options["input"]
        out_dir = Path(options["out_dir"]) if options["out_dir"] else locations_dir

        if not src.is_file():
            self.stderr.write(f"Input not found: {src}")
            return

        out_dir.mkdir(parents=True, exist_ok=True)

        df = pd.read_excel(src)
        district = District.objects.filter(name__iexact="Nalgonda").first()
        if not district:
            self.stderr.write("District Nalgonda not found.")
            return

        # master_mandal_name_if_found maps to Mandal
        mandal_by_name = {
            m.name.strip().casefold(): m
            for m in Mandal.objects.filter(district=district).select_related(
                "constituency", "constituency__district"
            )
        }

        rows_out = []
        skipped = 0
        for _, r in df.iterrows():
            mname = r.get("master_mandal_name_if_found")
            if pd.isna(mname) or not str(mname).strip():
                skipped += 1
                continue
            key = str(mname).strip().casefold()
            m = mandal_by_name.get(key)
            if not m:
                skipped += 1
                continue
            v = r.get("grama_panchayat_as_in_sheet")
            if pd.isna(v) or not str(v).strip():
                skipped += 1
                continue

            rows_out.append(
                {
                    "district": district.name,
                    "constituency": m.constituency.display_name,
                    "mandal": m.name,
                    "name": str(v).strip(),
                    "local_body_type": "VILLAGE",
                    "pincode": "",
                    "is_active": True,
                }
            )

        if not rows_out:
            self.stderr.write("No rows to export (check master_mandal_name_if_found).")
            return

        out_df = pd.DataFrame(rows_out)
        # Dedupe per mandal + village name + type (import key)
        out_df["_key"] = (
            out_df["mandal"].str.strip().str.casefold()
            + "|"
            + out_df["name"].str.strip().str.casefold()
        )
        out_df = out_df.drop_duplicates(subset=["_key"], keep="first")
        out_df = out_df.drop(columns=["_key"])

        written = []
        for m_key, g in out_df.groupby("mandal", sort=True):
            m_obj = mandal_by_name.get(str(m_key).strip().casefold())
            slug = _safe_filename_part(m_obj.name if m_obj else m_key)
            fname = f"{slug}_Constituency_LocalBody_Import.xlsx"
            path = out_dir / fname

            export = g[
                [
                    "district",
                    "constituency",
                    "mandal",
                    "name",
                    "local_body_type",
                    "pincode",
                    "is_active",
                ]
            ].copy()
            # Empty pincode cells as NaN for Excel blank column
            export["pincode"] = ""

            with pd.ExcelWriter(path, engine="openpyxl") as w:
                export.to_excel(w, index=False, sheet_name="Sheet1")

            written.append((fname, len(export)))

        self.stdout.write(
            self.style.SUCCESS(
                f"Source rows used: {len(df) - skipped} (skipped {skipped})\n"
                f"Rows after dedupe: {len(out_df)}\n"
                f"Files written: {len(written)} to {out_dir}\n"
                + "\n".join(f"  {n} ({c} villages)" for n, c in sorted(written))
            )
        )
