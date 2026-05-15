from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def generate_report(data, output_file):

    doc = SimpleDocTemplate(output_file)

    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph(
        "<b>AI-Powered TPRM Risk Assessment Report</b>",
        styles['Title']
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    summary = Paragraph(
        f"<b>Executive Summary:</b> {data['summary']}",
        styles['BodyText']
    )

    elements.append(summary)

    elements.append(Spacer(1, 20))

    for risk in data["risks"]:

        content = f"""
        <b>Category:</b> {risk['category']}<br/>
        <b>Risk:</b> {risk['risk']}<br/>
        <b>Severity:</b> {risk['severity']}<br/>
        <b>Recommendation:</b> {risk['recommendation']}<br/>
        <b>Confidence:</b> {risk['confidence']}%
        """

        elements.append(
            Paragraph(content, styles['BodyText'])
        )

        elements.append(Spacer(1, 12))

    disclaimer = Paragraph(
        "<i>This assessment is AI-assisted and intended for preliminary risk analysis only.</i>",
        styles['Italic']
    )

    elements.append(disclaimer)

    doc.build(elements)