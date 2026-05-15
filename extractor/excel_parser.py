import pandas as pd

IMPORTANT_KEYWORDS = [
    "mfa",
    "access",
    "password",
    "encryption",
    "incident",
    "backup",
    "logging",
    "monitoring",
    "vulnerability",
    "risk",
    "vendor",
    "soc2",
    "authentication"
]

def extract_excel(file_path):

    try:

        excel_data = pd.read_excel(
            file_path,
            sheet_name=None
        )

        combined_text = ""

        for sheet_name, df in excel_data.items():

            df = df.fillna("")

            rows = df.astype(str).values.tolist()

            for row in rows:

                row_text = " ".join(row)

                if any(
                    keyword.lower() in row_text.lower()
                    for keyword in IMPORTANT_KEYWORDS
                ):

                    combined_text += row_text + "\n"

        return combined_text

    except Exception as e:

        print(str(e))

        return ""