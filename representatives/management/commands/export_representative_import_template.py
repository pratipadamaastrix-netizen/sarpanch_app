"""
Write an empty Excel template for Representative bulk import (admin).
"""

from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand

COLUMNS = [
    "district",
    "constituency",
    "mandal",
    "village",
    "representative_type",
    "full_name",
    "email",
    "age",
    "mobile_number",
    "gender",
    "status",
    "effective_from",
    "effective_to",
    "notes",
]


class Command(BaseCommand):
    help = "Create Representative_Import_Template.xlsx in representatives/ folder."

    def handle(self, *args, **options):
        base = Path(__file__).resolve().parent.parent.parent
        out = base / "Representative_Import_Template.xlsx"
        df = pd.DataFrame(columns=COLUMNS)
        with pd.ExcelWriter(out, engine="openpyxl") as w:
            df.to_excel(w, index=False, sheet_name="import")
        self.stdout.write(self.style.SUCCESS(f"Wrote: {out}"))
