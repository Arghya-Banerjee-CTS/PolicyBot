"""Generates all 10 Meridian Technologies policy PDFs into knowledge_base/.

Run directly:  python generate_pdfs.py
"""
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "knowledge_base"
COMPANY = "MERIDIAN TECHNOLOGIES PVT. LTD."

styles = getSampleStyleSheet()
H_STYLE = ParagraphStyle("H", parent=styles["Heading1"], fontSize=16, textColor=colors.HexColor("#1f3864"), spaceAfter=14)
SH_STYLE = ParagraphStyle("SH", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#2e5597"), spaceAfter=8)
SSH_STYLE = ParagraphStyle("SSH", parent=styles["Heading3"], fontSize=11, textColor=colors.HexColor("#404040"), spaceAfter=6)
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=6)
CENTERED = ParagraphStyle("C", parent=styles["BodyText"], fontSize=10, alignment=TA_CENTER, spaceAfter=4)
CONFIDENTIAL = ParagraphStyle("CONF", parent=styles["BodyText"], fontSize=8, textColor=colors.red, alignment=TA_CENTER)


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 9)
    canvas.setFillColor(colors.HexColor("#1f3864"))
    canvas.drawString(2 * cm, 28 * cm, COMPANY)
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.red)
    canvas.drawRightString(19 * cm, 28 * cm, "CONFIDENTIAL")
    canvas.setStrokeColor(colors.HexColor("#1f3864"))
    canvas.line(2 * cm, 27.8 * cm, 19 * cm, 27.8 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(10.5 * cm, 1.5 * cm, f"Page {doc.page}")
    canvas.restoreState()


def _title_block(title, doc_id, version, effective):
    return [
        Paragraph(COMPANY, CENTERED),
        Paragraph("Internal Policy Document", CENTERED),
        Spacer(1, 0.4 * cm),
        Paragraph(f"<b>{title}</b>", H_STYLE),
        Spacer(1, 0.2 * cm),
        Paragraph(f"<b>Document Number:</b> {doc_id}  |  <b>Version:</b> {version}  |  <b>Effective Date:</b> {effective}", BODY),
        Paragraph("<b>Classification:</b> Internal / Confidential", BODY),
        Paragraph("This document is the property of Meridian Technologies Pvt. Ltd. Unauthorized reproduction is prohibited.", BODY),
        Spacer(1, 0.6 * cm),
    ]


def _toc(items):
    rows = [["Section", "Title"]]
    for i, t in enumerate(items, 1):
        rows.append([str(i), t])
    t = Table(rows, colWidths=[2 * cm, 14 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3864")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4fa")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [Paragraph("<b>Table of Contents</b>", SH_STYLE), Spacer(1, 0.2 * cm), t]


def _section(num, title, paragraphs):
    out = [Paragraph(f"{num}. {title}", SH_STYLE)]
    for p in paragraphs:
        if isinstance(p, tuple):
            sub_title, sub_body = p
            out.append(Paragraph(f"<b>{sub_title}</b>", SSH_STYLE))
            for line in sub_body:
                out.append(Paragraph(line, BODY))
        else:
            out.append(Paragraph(p, BODY))
    out.append(Spacer(1, 0.3 * cm))
    return out


def _build(filename, title, doc_id, version, effective, toc_items, sections):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / filename
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
    )
    story = []
    story.extend(_title_block(title, doc_id, version, effective))
    story.append(PageBreak())
    story.extend(_toc(toc_items))
    story.append(PageBreak())
    for i, (sec_title, sec_content) in enumerate(sections, 1):
        story.extend(_section(i, sec_title, sec_content))
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    print(f"  generated: {filename}")


def gen_leave_policy():
    toc = [
        "Introduction and Scope",
        "Types of Leave",
        "Earned Leave (EL)",
        "Sick Leave (SL)",
        "Casual Leave (CL)",
        "Maternity and Paternity Leave",
        "Leave Encashment",
        "Leave Application Procedure",
        "Leave Without Pay",
        "Holiday Calendar and Special Leave",
    ]
    sections = [
        ("Introduction and Scope", [
            "This policy governs all categories of leave available to permanent employees of Meridian Technologies Pvt. Ltd. It applies to all employees on the company's payroll, including those on probation, with specific clauses noted where probationers are treated differently.",
            "The leave year follows the calendar year and runs from 1 January to 31 December. All entitlements reset on 1 January each year unless explicitly stated as carry-forward.",
        ]),
        ("Types of Leave", [
            "Meridian Technologies provides the following categories of paid leave: Earned Leave (EL), Sick Leave (SL), Casual Leave (CL), Maternity Leave, Paternity Leave, Bereavement Leave, and Marriage Leave. Special unpaid leave categories include Leave Without Pay (LWP) and Sabbatical Leave.",
            "Annual entitlements for confirmed employees: 18 days Earned Leave, 12 days Sick Leave, and 6 days Casual Leave per calendar year. Probationers receive a pro-rated entitlement based on date of joining.",
        ]),
        ("Earned Leave (EL)", [
            ("Annual Entitlement", [
                "Confirmed employees are entitled to 18 days of Earned Leave per calendar year, credited at the rate of 1.5 days per completed month of service.",
                "Probationers accrue EL at the same rate but cannot avail it until confirmation, except in special circumstances approved by HR.",
            ]),
            ("Carry Forward", [
                "Unused Earned Leave may be carried forward to the next calendar year subject to a maximum accumulation of 30 days.",
                "Any EL balance beyond 30 days as on 31 December will lapse automatically unless encashed during the encashment window.",
            ]),
            ("Minimum and Maximum Block", [
                "Minimum EL that can be availed at a stretch is 0.5 day (half day). Maximum continuous EL is 15 working days; longer durations require Business Unit Head approval.",
                "EL must be applied at least 7 calendar days in advance for durations of 3 days or more.",
            ]),
        ]),
        ("Sick Leave (SL)", [
            ("Entitlement and Use", [
                "Confirmed employees are entitled to 12 days of Sick Leave per calendar year. Sick Leave cannot be clubbed with Earned Leave or Casual Leave for vacation purposes.",
                "Sick Leave of 3 or more consecutive days requires a medical certificate from a registered medical practitioner, to be submitted within 7 days of return.",
            ]),
            ("Lapse and Encashment", [
                "Sick Leave does not carry forward to the next calendar year and lapses automatically on 31 December.",
                "Sick Leave is not encashable under any circumstances.",
            ]),
        ]),
        ("Casual Leave (CL)", [
            ("Entitlement", [
                "Confirmed employees receive 6 days of Casual Leave per calendar year for short, unplanned personal needs.",
                "CL is non-cumulative, non-encashable, and lapses on 31 December.",
            ]),
            ("Rules", [
                "Casual Leave cannot be clubbed with Earned Leave under any circumstances. It may be clubbed with weekly off or public holidays.",
                "Maximum continuous CL that may be taken is 3 days at a stretch.",
            ]),
        ]),
        ("Maternity and Paternity Leave", [
            ("Maternity Leave", [
                "Female employees who have completed 80 days of service are entitled to 26 weeks of paid maternity leave for the first two children, in line with the Maternity Benefit Act.",
                "For the third child onwards, maternity leave is reduced to 12 weeks paid. Adoptive and commissioning mothers are entitled to 12 weeks from the date of legal adoption or surrogacy delivery.",
            ]),
            ("Paternity Leave", [
                "Male employees are entitled to 10 working days of paid Paternity Leave, to be availed within 3 months of the birth of the child. This benefit covers up to 2 children.",
            ]),
        ]),
        ("Leave Encashment", [
            "Employees may encash unused Earned Leave (EL only) up to a maximum of 15 days per calendar year. Encashment is at the basic salary plus dearness allowance prevailing on 31 December.",
            "On separation (resignation, retirement, or termination on grounds other than misconduct), any unused EL balance is encashed in full at the last drawn basic plus DA.",
            "Encashment of Sick Leave and Casual Leave is not permitted under any circumstance.",
        ]),
        ("Leave Application Procedure", [
            "All leave must be applied through the HRMS leave module. Manual leave applications are accepted only when the HRMS is unavailable and must be regularised within 3 working days.",
            "Approval workflow: Reporting Manager (first level) -> Business Unit Head (for EL of 5 days or more) -> HR for any clarifications. Sick Leave can be approved post-facto where prior notice was not possible.",
            "Unauthorised absence beyond 5 consecutive working days will be treated as voluntary abandonment of employment, subject to the disciplinary procedure in the Code of Conduct.",
        ]),
        ("Leave Without Pay", [
            "Leave Without Pay (LWP) may be granted at the discretion of the Reporting Manager and HR when an employee has exhausted all entitled paid leave.",
            "LWP exceeding 30 calendar days in a year requires approval from the Business Unit Head and HR Head jointly. Extended LWP beyond 90 days may impact appraisal eligibility for the cycle.",
        ]),
        ("Holiday Calendar and Special Leave", [
            "The annual holiday calendar comprises 10 public holidays, of which 3 are restricted holidays employees may choose from a published list.",
            "Bereavement Leave of 5 working days is granted on the death of an immediate family member (spouse, parent, child, sibling, parent-in-law).",
            "Marriage Leave of 5 working days is granted once during the tenure of employment.",
        ]),
    ]
    _build(
        "HR_Leave_Policy.pdf",
        "Leave Policy",
        "HR-POL-001", "2.1", "January 2024",
        toc, sections,
    )


def gen_travel_policy():
    toc = [
        "Purpose and Applicability",
        "Travel Authorisation",
        "Domestic Travel",
        "International Travel",
        "Accommodation and Class Entitlements",
        "Per Diem Allowance",
        "Local Conveyance",
        "Reimbursement Procedure",
        "Forex and Card Policy",
        "Violations and Disciplinary Action",
    ]
    sections = [
        ("Purpose and Applicability", [
            "This policy defines rules for business travel undertaken by employees of Meridian Technologies, both domestic and international. It applies to all confirmed employees and pre-approved contract staff travelling on behalf of the company.",
        ]),
        ("Travel Authorisation", [
            "All business travel must be pre-approved by the Reporting Manager and Business Unit Head. International travel additionally requires approval from the Travel Desk and the relevant VP.",
            "Travel Requisition Form (TRF-01) must be submitted at least 7 working days in advance for domestic and 15 working days in advance for international travel.",
        ]),
        ("Domestic Travel", [
            ("Air Travel", [
                "Domestic air travel is permitted in economy class for all bands. Senior Vice Presidents and above are entitled to business class on flights longer than 2 hours.",
                "Bookings must be made through the empanelled travel agent or the online travel portal. Direct purchase from airlines is reimbursable only with prior written approval.",
            ]),
            ("Rail Travel", [
                "Rail travel is permitted in AC 2-tier for managers and below, and AC 1-tier for AVP and above. Tatkal charges are reimbursable only if travel was urgent and approved.",
            ]),
        ]),
        ("International Travel", [
            ("Class of Travel", [
                "Economy class for journeys up to 6 hours. Premium economy is permitted for journeys 6 to 10 hours for managers and above. Business class is permitted for journeys exceeding 10 hours for AVP and above.",
            ]),
            ("Documentation", [
                "Valid passport (minimum 6 months validity), visa, travel insurance, and an approved TRF must be in place before booking. Visa fees and travel insurance are fully reimbursable.",
            ]),
        ]),
        ("Accommodation and Class Entitlements", [
            ("Domestic Accommodation Ceilings (per night, excluding taxes)", [
                "Tier 1 cities (Bengaluru, Mumbai, Delhi NCR, Chennai, Hyderabad, Pune, Kolkata): Rs. 6,000 (managers and below), Rs. 8,500 (AVP and above).",
                "Tier 2 cities: Rs. 4,500 and Rs. 6,000 respectively.",
                "Tier 3 cities and others: Rs. 3,500 and Rs. 4,500 respectively.",
            ]),
            ("International Accommodation Ceilings (per night, USD)", [
                "USA, UK, Western Europe, Singapore, Japan: USD 200 (managers and below), USD 275 (AVP and above).",
                "Other regions: USD 150 and USD 200 respectively.",
            ]),
        ]),
        ("Per Diem Allowance", [
            "Domestic per diem: Rs. 1,500 per day inclusive of meals, laundry, and local incidentals. Per diem is paid for each completed 24 hour period away from base location, with a 50 percent rate for any incomplete day beyond 6 hours.",
            "International per diem: USD 75 per day for travel to USA, UK, Western Europe, Singapore, Japan. USD 60 per day for other countries. Per diem is paid in INR equivalent at the rate prevailing on the date of disbursement.",
            "Per diem is in addition to actual accommodation reimbursement and covers meals, laundry, tips, and incidental expenses. No separate meal bills are required to be submitted.",
        ]),
        ("Local Conveyance", [
            "Airport transfers within the same city by app-based cabs (Uber, Ola) are reimbursable on actuals. Outstation cab usage requires prior approval.",
            "Personal vehicle usage for business travel is reimbursed at Rs. 12 per km for cars and Rs. 5 per km for two-wheelers, supported by a log entry.",
        ]),
        ("Reimbursement Procedure", [
            "All travel expense claims must be submitted in the HRMS travel module within 15 working days of completion of travel, with original receipts attached as scans.",
            "Claims submitted beyond 30 working days will be rejected. Approval flow: Reporting Manager -> Finance for validation -> Payroll for payment with next salary cycle.",
        ]),
        ("Forex and Card Policy", [
            "Forex is to be drawn through the empanelled forex partner. The maximum forex advance is 80 percent of expected international expenses excluding accommodation if paid by company card.",
            "Corporate credit cards are issued to eligible roles (AVP and above) for travel expenses. Personal expenses on corporate cards are strictly prohibited.",
        ]),
        ("Violations and Disciplinary Action", [
            "Any claim found to be inflated, fabricated, or otherwise in breach of this policy will be subject to disciplinary action under the Code of Conduct, up to and including termination of employment.",
            "Repeated late submissions may result in suspension of travel privileges for up to 6 months.",
        ]),
    ]
    _build(
        "HR_Travel_Reimbursement_Policy.pdf",
        "Travel Reimbursement Policy",
        "HR-POL-002", "3.0", "April 2024",
        toc, sections,
    )


def gen_medical_policy():
    toc = [
        "Coverage Overview",
        "Eligibility",
        "Sum Insured and Family Floater",
        "Dependents Covered",
        "Inclusions",
        "Exclusions",
        "Claim Procedure",
        "Cashless Hospitalisation",
        "Maternity Cover",
        "Pre and Post Hospitalisation",
    ]
    sections = [
        ("Coverage Overview", [
            "Meridian Technologies provides a Group Mediclaim Insurance Policy (GMC) for all confirmed employees and their dependents, underwritten by a leading general insurer empanelled annually.",
            "Coverage commences from the date of confirmation and continues for as long as the employee is on the active payroll of the company.",
        ]),
        ("Eligibility", [
            "All confirmed permanent employees of Meridian Technologies are automatically enrolled. Probationers are eligible from the first day of confirmation.",
            "Contract employees, consultants, and interns are not covered under this policy.",
        ]),
        ("Sum Insured and Family Floater", [
            "The Sum Insured is Rs. 3,00,000 per family on a floater basis. The same sum insured is shared across all dependents enrolled by the employee.",
            "Top-up cover of an additional Rs. 5,00,000 is available at a subsidised employee-paid premium, opted during the enrollment window in April each year.",
        ]),
        ("Dependents Covered", [
            "An employee may enroll a maximum of 2 dependents under the base policy, in addition to themselves. Eligible dependents are: spouse and up to 2 children (natural or legally adopted).",
            "Parents and parents-in-law are not covered under the base policy but may be enrolled under the optional Parental Cover plan at the employee's expense.",
            "Children are covered up to the age of 25 or until they start earning, whichever is earlier.",
        ]),
        ("Inclusions", [
            "Inpatient hospitalisation expenses (room rent, ICU charges, doctor fees, surgery, diagnostic tests, medicines) for any treatment requiring a minimum of 24 hours of hospitalisation.",
            "Day-care procedures listed by the insurer (cataract, dialysis, chemotherapy, lithotripsy, etc.) are covered even if hospitalisation is less than 24 hours.",
            "Ambulance charges up to Rs. 2,000 per hospitalisation event.",
        ]),
        ("Exclusions", [
            "Cosmetic surgery, dental treatment (unless arising from accidental injury), refractive errors, vaccinations (except post bite), congenital external diseases, and self-inflicted injuries.",
            "Treatment outside India is not covered unless the employee was on an authorised business travel and the hospitalisation directly arose during that travel.",
        ]),
        ("Claim Procedure", [
            "Two modes of claim are available: Cashless at network hospitals and Reimbursement at non-network hospitals.",
            "All claims must be intimated to the TPA helpline within 24 hours of hospitalisation (planned) or 48 hours (emergency).",
        ]),
        ("Cashless Hospitalisation", [
            "Cashless requests for planned hospitalisation must be submitted to the TPA at least 3 working days in advance with the prescription, estimate, and pre-authorisation form.",
            "Cashless requests for emergency hospitalisation must be filed within 48 hours of admission, supported by the doctor's certificate.",
        ]),
        ("Maternity Cover", [
            "Maternity benefit is included in the base policy with a sub-limit of Rs. 50,000 for normal delivery and Rs. 75,000 for caesarean section.",
            "Maternity is covered for the first 2 living children only. A waiting period of 9 months from the policy inception date applies, except for new joiners where coverage is from date of confirmation.",
        ]),
        ("Pre and Post Hospitalisation", [
            "Pre-hospitalisation expenses are covered for 30 days prior to admission, and post-hospitalisation expenses are covered for 60 days post discharge, provided they are related to the same ailment.",
            "Original receipts, discharge summary, and the doctor's prescription must be submitted within 45 days of discharge for reimbursement claims.",
        ]),
    ]
    _build(
        "HR_Medical_Insurance_Policy.pdf",
        "Medical Insurance Policy",
        "HR-POL-003", "4.2", "April 2024",
        toc, sections,
    )


def gen_conduct_policy():
    toc = [
        "Purpose",
        "Core Values",
        "Workplace Behaviour",
        "Anti-Harassment and POSH",
        "Conflict of Interest",
        "Confidentiality",
        "Gifts and Hospitality",
        "Disciplinary Procedure",
        "Whistleblower Mechanism",
        "Acknowledgement",
    ]
    sections = [
        ("Purpose", [
            "The Code of Conduct establishes the standards of behaviour expected from all employees, contractors, and representatives of Meridian Technologies. Adherence is a condition of continued employment.",
        ]),
        ("Core Values", [
            "Integrity, Respect, Accountability, Innovation, and Customer Centricity are the five core values. All employees are expected to act in accordance with these values in every business interaction.",
        ]),
        ("Workplace Behaviour", [
            "Discrimination on the basis of gender, race, religion, caste, sexual orientation, disability, or age is strictly prohibited. The company is committed to providing a workplace free from harassment and bias.",
            "Use of intoxicants on company premises or during company business is prohibited. Smoking is permitted only in designated zones.",
        ]),
        ("Anti-Harassment and POSH", [
            "The Prevention of Sexual Harassment (POSH) policy is fully adopted. An Internal Complaints Committee (ICC) is constituted at every location with more than 10 employees.",
            "Complaints must be filed in writing to the ICC within 3 months of the incident. The ICC will complete the inquiry within 90 days. Confidentiality is strictly maintained throughout.",
        ]),
        ("Conflict of Interest", [
            "Employees must declare any potential conflict of interest in writing to the HR head. Examples include personal business ventures in competing fields, financial interest in vendors, and close family in supplier organisations.",
            "External employment (moonlighting) requires prior written approval from the Business Unit Head and HR. Unapproved external employment is treated as a serious breach of contract.",
        ]),
        ("Confidentiality", [
            "Confidential business information, client data, source code, designs, and strategic plans must not be shared outside the company. The Non-Disclosure Agreement signed at the time of joining continues to apply for 3 years post separation.",
        ]),
        ("Gifts and Hospitality", [
            "Employees may accept token gifts from clients and vendors not exceeding Rs. 2,500 in value. Gifts exceeding this limit must be declined or surrendered to HR.",
            "Cash, gift cards, and equivalent instruments must NEVER be accepted regardless of value.",
        ]),
        ("Disciplinary Procedure", [
            "Minor misconduct is addressed through verbal counselling followed by a written warning. Repeated or serious misconduct leads to a formal show-cause notice and an inquiry.",
            "Gross misconduct (fraud, theft, sexual harassment, breach of confidentiality, falsification of records) may lead to immediate termination without notice.",
            "Disciplinary inquiries are conducted by an Inquiry Officer appointed by HR. The employee has the right to representation, written charge sheet, and a fair hearing.",
        ]),
        ("Whistleblower Mechanism", [
            "Employees who become aware of fraud, financial irregularity, or breaches of this Code may report it anonymously via the Ethics Helpline (ethics@meridian.example) or the third-party reporting portal listed on the intranet.",
            "No retaliation against a whistleblower acting in good faith is permitted. Retaliation itself is a disciplinary offence.",
        ]),
        ("Acknowledgement", [
            "All employees must acknowledge this Code annually through the HRMS portal. Failure to acknowledge by the published deadline may result in suspension of system access until completion.",
        ]),
    ]
    _build(
        "HR_Code_of_Conduct.pdf",
        "Code of Conduct",
        "HR-POL-004", "5.0", "January 2024",
        toc, sections,
    )


def gen_it_aup():
    toc = [
        "Scope",
        "Issuance of Devices",
        "Acceptable Use of Devices",
        "Software Installation and Licensing",
        "Internet and Email",
        "Remote Access and VPN",
        "Personal Use",
        "Returns and Damages",
        "Monitoring",
        "Penalties",
    ]
    sections = [
        ("Scope", [
            "This Acceptable Use Policy covers all company-issued IT assets including laptops, desktops, mobile phones, tablets, software, networks, and cloud accounts.",
        ]),
        ("Issuance of Devices", [
            "Each confirmed employee is issued one primary laptop. Additional devices (secondary monitors, mobile phones, tablets) are issued based on role eligibility and require approval from the Reporting Manager.",
            "Devices remain the property of Meridian Technologies throughout the period of issue and must be returned on separation or role change.",
        ]),
        ("Acceptable Use of Devices", [
            "Company devices are issued primarily for business use. Limited and reasonable personal use is permitted provided it does not interfere with work or violate any policy.",
            "Employees must not modify hardware configurations, remove asset tags, or share device credentials with anyone, including family members.",
        ]),
        ("Software Installation and Licensing", [
            ("Approved Software", [
                "Only software from the IT-approved catalogue (accessible via the IT Service Desk portal) may be installed. Self-installation through the catalogue is permitted for whitelisted titles.",
            ]),
            ("Unapproved Software", [
                "Installation of any software outside the approved catalogue requires a Software Request Ticket and IT Security review. Pirated, cracked, or unlicensed software is strictly prohibited.",
                "Use of personal cloud storage (Dropbox, Google Drive, OneDrive personal) for company data is prohibited. The approved enterprise OneDrive must be used.",
            ]),
        ]),
        ("Internet and Email", [
            "Internet access is provided for business purposes. Browsing of websites containing illegal content, adult material, gambling, or known phishing or malware sources is blocked and logged.",
            "Company email accounts must not be used to subscribe to personal services or to send chain mails. Auto-forwarding of company email to personal accounts is strictly prohibited.",
        ]),
        ("Remote Access and VPN", [
            "Remote access to company systems requires connecting through the company VPN with multi-factor authentication. Split tunnelling and use of personal proxies is prohibited.",
            "Access from public Wi-Fi networks is permitted only after VPN connection is established. Public Wi-Fi without VPN is forbidden for all company work.",
        ]),
        ("Personal Use", [
            "Personal use is permitted only outside core working hours and only for non-resource-intensive activities. Streaming, gaming, torrents, and cryptocurrency mining are strictly prohibited.",
        ]),
        ("Returns and Damages", [
            "On separation, all devices must be returned to the IT Service Desk within 3 working days of the last working day. Failure to return devices may result in deduction from final settlement at replacement cost.",
            "Accidental damage must be reported within 24 hours. The first instance is treated as a no-fault event; subsequent damages may attract a recovery fee per the IT asset schedule.",
        ]),
        ("Monitoring", [
            "All activity on company networks and devices is subject to monitoring and audit. Employees should have no expectation of privacy for activities conducted on company IT assets.",
        ]),
        ("Penalties", [
            "Breach of this policy may result in disciplinary action up to and including termination, recovery of damages, and in cases of legal violation, referral to law enforcement.",
        ]),
    ]
    _build(
        "IT_Acceptable_Use_Policy.pdf",
        "Acceptable Use Policy",
        "IT-POL-001", "2.5", "March 2024",
        toc, sections,
    )


def gen_data_security():
    toc = [
        "Purpose and Scope",
        "Data Classification",
        "Handling Public Data",
        "Handling Internal Data",
        "Handling Confidential Data",
        "Handling Restricted Data",
        "Data Storage and Encryption",
        "Data Transfer",
        "Data Breach Response",
        "Records Retention",
    ]
    sections = [
        ("Purpose and Scope", [
            "This policy defines how all data assets owned, processed, or handled by Meridian Technologies must be classified, stored, transmitted, and disposed of to maintain confidentiality, integrity, and availability.",
        ]),
        ("Data Classification", [
            "All data is classified into one of four tiers: Public, Internal, Confidential, and Restricted. Owners of each data asset are responsible for accurate classification at creation.",
            "Public: information explicitly approved for public release. Internal: business information for employee use only. Confidential: business-sensitive information including client data and financials. Restricted: highly sensitive personal data, source code of products, regulatory data, and trade secrets.",
        ]),
        ("Handling Public Data", [
            "Public data has no handling restrictions but must still be reviewed by the Communications team before external release if it represents the company.",
        ]),
        ("Handling Internal Data", [
            "Internal data may be shared freely with employees on a need-to-know basis. Sharing with vendors or external parties requires an NDA to be in place.",
        ]),
        ("Handling Confidential Data", [
            "Confidential data must be stored in IT-managed systems with access controls. Local storage on laptops is permitted but must be in the encrypted user profile partition.",
            "Sharing externally requires written approval from the data owner and the use of approved secure channels (encrypted email, secure file transfer, NDA-backed portals).",
        ]),
        ("Handling Restricted Data", [
            "Restricted data must never be stored on laptops, USB drives, or personal devices. It must reside only on designated secure servers with role-based access and full audit logging.",
            "Access to Restricted data requires explicit written approval from the Data Protection Officer (DPO) and is reviewed quarterly. All access is logged and reviewed monthly.",
        ]),
        ("Data Storage and Encryption", [
            "All laptops and removable media must be encrypted using the company-approved disk encryption tool. Decryption keys are managed centrally by IT Security.",
            "Confidential and Restricted data at rest must be encrypted with AES-256 or stronger. Data in transit must be protected with TLS 1.2 or higher.",
        ]),
        ("Data Transfer", [
            "Approved channels for external transfer of Confidential data: secure file transfer portal, encrypted email (S/MIME or PGP), and DRM-protected document sharing.",
            "USB devices and removable media for data transfer are blocked by default. Exceptions require approval from IT Security and the data owner, are time-bound, and the device must be encrypted.",
        ]),
        ("Data Breach Response", [
            "Any suspected or confirmed data breach must be reported within 2 hours to the Incident Response Team (irt@meridian.example).",
            "The IRT will follow the Data Breach Response Plan: contain, assess, notify the DPO and Legal, notify affected parties as per regulatory requirements, and document for post-incident review.",
            "Regulatory breach notifications, where applicable (such as under the DPDP Act), must be initiated within 72 hours of confirmation of breach.",
        ]),
        ("Records Retention", [
            "Internal and Confidential data is retained for 7 years unless a longer period is mandated by regulation or contract. Restricted data retention is governed by the specific contract or law applicable to that data.",
            "On retention expiry, data must be securely disposed of using IT-approved sanitisation methods (cryptographic erasure or physical destruction for media).",
        ]),
    ]
    _build(
        "IT_Data_Security_Policy.pdf",
        "Data Security Policy",
        "IT-POL-002", "3.1", "February 2024",
        toc, sections,
    )


def gen_expense():
    toc = [
        "Purpose",
        "Eligible Expense Categories",
        "Approval Limits",
        "Documentation",
        "Submission Timelines",
        "Non-Reimbursable Items",
        "Foreign Currency Claims",
        "Audit and Sample Checks",
        "Recovery of Excess Payments",
        "Disputes",
    ]
    sections = [
        ("Purpose", [
            "This policy governs the reimbursement of business expenses incurred by employees on behalf of Meridian Technologies. The aim is to ensure expenses are reasonable, properly approved, and well documented.",
        ]),
        ("Eligible Expense Categories", [
            "Business travel (covered separately under the Travel Policy), client entertainment, internal team events, training and certification fees, professional memberships, mobile and internet reimbursements for eligible roles, and small office supplies.",
        ]),
        ("Approval Limits", [
            "Expense claims up to Rs. 10,000 require approval from the Reporting Manager only.",
            "Claims between Rs. 10,001 and Rs. 50,000 require approval from the Reporting Manager and the Business Unit Head.",
            "Claims above Rs. 50,000 require approval from the relevant Vice President. Claims above Rs. 2,00,000 additionally require concurrence from the Finance Controller.",
        ]),
        ("Documentation", [
            "All claims must be supported by original receipts, invoices, or system-generated bills. Hand-written acknowledgements are accepted only for unavoidable expenses below Rs. 500.",
            "Invoices for amounts above Rs. 5,000 must include the company GSTIN to be eligible for input tax credit. Claims without GSTIN above this threshold may be processed at the reduced amount net of tax.",
        ]),
        ("Submission Timelines", [
            "Expense claims must be submitted via the HRMS Finance module within 15 working days of incurring the expense. Claims for expenses older than 60 days will not be processed.",
        ]),
        ("Non-Reimbursable Items", [
            "Personal items, alcoholic beverages (unless part of an approved client entertainment), traffic fines, parking tickets, late fees, and any expense flagged in the Travel Policy exclusions.",
        ]),
        ("Foreign Currency Claims", [
            "Foreign currency expenses must be claimed in the original currency, supported by credit card statements or forex card transaction records. Conversion to INR is done by Finance using the rate on the date of expense.",
        ]),
        ("Audit and Sample Checks", [
            "Finance conducts a quarterly audit of 5 percent of claims on a sample basis. The Internal Audit team may conduct additional reviews. Audit findings are reported to the Audit Committee.",
        ]),
        ("Recovery of Excess Payments", [
            "Any excess payment identified through audit or self-disclosure must be returned within 30 days. Recovery via salary deduction is exercised only as a last resort with employee acknowledgement.",
        ]),
        ("Disputes", [
            "Disputes regarding claim rejection or partial approval should be raised in writing within 7 working days of the decision. The Finance Controller is the final authority on expense policy interpretation.",
        ]),
    ]
    _build(
        "Finance_Expense_Reimbursement_Policy.pdf",
        "Expense Reimbursement Policy",
        "FIN-POL-001", "2.3", "April 2024",
        toc, sections,
    )


def gen_procurement():
    toc = [
        "Purpose",
        "Procurement Principles",
        "Vendor Empanelment",
        "Purchase Order Limits",
        "Tendering and Quotations",
        "Single Source Justification",
        "Contract Approvals",
        "Payment Terms",
        "Performance Review",
        "Conflict of Interest",
    ]
    sections = [
        ("Purpose", [
            "The Procurement Policy ensures all purchases of goods and services by Meridian Technologies are made through a transparent, competitive, and value-driven process.",
        ]),
        ("Procurement Principles", [
            "All procurement is guided by the principles of transparency, value for money, fairness, accountability, and adherence to legal and regulatory requirements.",
        ]),
        ("Vendor Empanelment", [
            "Vendors providing recurring goods or services must be empanelled through the annual vendor evaluation process. Empanelment includes due diligence on financial stability, references, statutory compliance, and a sample order.",
            "Vendor empanelment is approved by the Procurement Committee, comprising the Procurement Head, Finance Controller, and the user department head.",
        ]),
        ("Purchase Order Limits", [
            "Purchase Orders up to Rs. 50,000 may be raised by the user department head with approval from the Procurement Head.",
            "Purchase Orders from Rs. 50,001 to Rs. 5,00,000 require approval from the Procurement Head and Finance Controller.",
            "Purchase Orders above Rs. 5,00,000 require approval from the relevant Vice President. POs above Rs. 25,00,000 additionally require CFO approval.",
            "Capital expenditure above Rs. 1,00,00,000 requires Board approval.",
        ]),
        ("Tendering and Quotations", [
            "Procurement above Rs. 1,00,000 requires a minimum of 3 written quotations from empanelled vendors.",
            "Procurement above Rs. 10,00,000 requires a formal RFP process with sealed bids opened by a panel of at least 3 members from Procurement, Finance, and the user department.",
        ]),
        ("Single Source Justification", [
            "Single source procurement is permitted only where it is the sole supplier, an OEM, or for an emergency where time-bound delivery is essential.",
            "Single source justification must be documented in writing and approved by the Procurement Head and Finance Controller, irrespective of order value.",
        ]),
        ("Contract Approvals", [
            "All contracts with vendors must be vetted by the Legal team. Contracts above Rs. 10,00,000 in value or those involving sharing of Confidential or Restricted data also require Information Security and Data Protection Officer review.",
        ]),
        ("Payment Terms", [
            "Standard payment terms are net 30 days from receipt of invoice and goods or services. Advance payments are permitted only for the procurement of capital goods up to 25 percent of order value, against a bank guarantee.",
        ]),
        ("Performance Review", [
            "Vendor performance is reviewed semi-annually on quality, timeliness, responsiveness, and pricing. Underperforming vendors are issued an improvement plan; persistent issues lead to de-empanelment.",
        ]),
        ("Conflict of Interest", [
            "Employees involved in procurement decisions must declare any personal interest in a vendor. Direct family members of employees may not be vendors without explicit approval of the CFO and the Audit Committee.",
        ]),
    ]
    _build(
        "Finance_Procurement_Policy.pdf",
        "Procurement Policy",
        "FIN-POL-002", "1.8", "June 2024",
        toc, sections,
    )


def gen_wfh():
    toc = [
        "Purpose and Applicability",
        "Eligibility",
        "Maximum WFH Days",
        "Approval Workflow",
        "Equipment and Connectivity",
        "Working Hours and Availability",
        "Attendance and Productivity",
        "Information Security",
        "Wellbeing and Communication",
        "Policy Review",
    ]
    sections = [
        ("Purpose and Applicability", [
            "This policy defines the framework under which employees may work from home (WFH) or remote locations, balancing flexibility with productivity and collaboration.",
        ]),
        ("Eligibility", [
            "All confirmed employees of Meridian Technologies are eligible to apply for WFH. Employees on probation are NOT eligible for the standard WFH benefit; exceptions may be granted only with HR Head approval for genuine reasons such as medical advisories.",
            "Roles which require physical presence (such as front office, lab operations, and on-site customer support) are excluded from WFH except on a case-by-case basis.",
        ]),
        ("Maximum WFH Days", [
            "Confirmed employees may avail a maximum of 2 WFH days per week. The remaining 3 days must be from the office unless an approved exception is in place.",
            "Special WFH (extended) of up to 5 working days in a row may be requested for specific reasons (relocation, health, family emergency) and requires Business Unit Head approval.",
        ]),
        ("Approval Workflow", [
            "Routine weekly WFH (within the 2 days entitlement) requires approval from the Reporting Manager via the HRMS leave/attendance module.",
            "Special or extended WFH requires approval from the Reporting Manager AND the Business Unit Head.",
        ]),
        ("Equipment and Connectivity", [
            "Employees on WFH must use the company-issued laptop. Personal devices are not permitted for company work.",
            "A reliable broadband connection of at least 25 Mbps download is recommended. The company does not provide a dedicated broadband reimbursement for general WFH; eligible roles may claim under the Communication Allowance scheme.",
        ]),
        ("Working Hours and Availability", [
            "Core working hours during WFH are 10:00 to 16:00, during which employees must be available on Teams or the equivalent collaboration platform.",
            "Employees must be reachable on the registered mobile number and email throughout standard business hours of 09:00 to 18:00.",
        ]),
        ("Attendance and Productivity", [
            "Attendance is marked via the HRMS self-service module on WFH days. Failure to mark attendance is treated as absence.",
            "Periodic productivity reviews may be conducted by the Reporting Manager. Sustained underperformance during WFH may lead to suspension of the WFH benefit.",
        ]),
        ("Information Security", [
            "Employees on WFH must comply with the IT Acceptable Use Policy and Data Security Policy at all times. The workplace must be reasonably private to prevent shoulder-surfing of confidential information.",
            "Confidential calls must not be taken in shared public spaces. Restricted data work is not permitted from any location other than office premises.",
        ]),
        ("Wellbeing and Communication", [
            "Employees and managers are encouraged to take regular breaks and maintain a clear separation between work and personal time, even when working from home.",
            "Managers are expected to hold at least one team in-person day per fortnight to maintain team cohesion.",
        ]),
        ("Policy Review", [
            "This policy will be reviewed annually by the HR Head and Business Unit Heads in consultation with the Leadership Team to ensure it remains aligned with business needs.",
        ]),
    ]
    _build(
        "WFH_Remote_Work_Policy.pdf",
        "Work From Home and Remote Work Policy",
        "HR-POL-005", "1.4", "May 2024",
        toc, sections,
    )


def gen_performance():
    toc = [
        "Purpose",
        "Performance Cycle",
        "Goal Setting",
        "Rating Scale",
        "Calibration",
        "Performance Improvement Plan",
        "Promotion Eligibility",
        "Recognition and Rewards",
        "Appeals",
        "Confidentiality",
    ]
    sections = [
        ("Purpose", [
            "The Performance Management Policy provides a structured framework for setting, reviewing, and rewarding individual performance at Meridian Technologies.",
        ]),
        ("Performance Cycle", [
            "The performance management year runs from 1 April to 31 March. Goal-setting is completed by 30 April. Mid-year review is conducted in October. Annual appraisal is completed by 31 May of the following year.",
        ]),
        ("Goal Setting", [
            "Goals are set jointly by the employee and the Reporting Manager, using the SMART framework (Specific, Measurable, Achievable, Relevant, Time-bound).",
            "Each employee should have between 5 and 8 goals, with explicit weighting that sums to 100 percent. At least one goal must be a development or learning goal.",
        ]),
        ("Rating Scale", [
            "Annual performance is rated on a 5-point scale: 1 - Below Expectations, 2 - Partially Meets Expectations, 3 - Meets Expectations, 4 - Exceeds Expectations, 5 - Outstanding.",
            "Final ratings are computed as a weighted score of goal achievement (70 percent) and behavioural competencies (30 percent), and then mapped to the 5-point scale.",
        ]),
        ("Calibration", [
            "All ratings are calibrated through a forced-distribution guideline at the Business Unit level: not more than 15 percent rated Outstanding or Exceeds combined, and not more than 10 percent rated Below or Partially Meets combined.",
            "Calibration discussions are chaired by the Business Unit Head and attended by the HR Business Partner.",
        ]),
        ("Performance Improvement Plan", [
            "Employees rated Below Expectations are placed on a formal Performance Improvement Plan (PIP) of 90 days duration. The PIP contains specific, measurable improvement goals and weekly check-ins.",
            "At the end of the PIP, performance is reviewed. Successful completion restores normal status. Unsuccessful completion may lead to extension by 30 days, role change, or separation, as decided by HR and the Business Unit Head jointly.",
        ]),
        ("Promotion Eligibility", [
            "Promotion is based on demonstrated readiness for the next role and is independent of the annual rating, though a minimum rating of Meets Expectations is required.",
            "A minimum tenure of 18 months in the current role is required for promotion consideration. Exceptions for high-potential employees require Business Unit Head and HR Head approval.",
        ]),
        ("Recognition and Rewards", [
            "Annual increments and variable pay are linked to the final rating and Business Unit performance. The exact ratio is communicated during the annual compensation cycle.",
            "Spot recognition awards and quarterly excellence awards provide non-cycle recognition opportunities, governed by the Rewards and Recognition guideline.",
        ]),
        ("Appeals", [
            "Employees who disagree with their final rating may file a written appeal to the HR Head within 10 working days of communication. Appeals are reviewed by a panel consisting of the HR Head, Business Unit Head, and the next-level reviewer.",
        ]),
        ("Confidentiality", [
            "All performance information is strictly confidential. Disclosure of one's own or another employee's performance information to unauthorised parties is a breach of conduct.",
        ]),
    ]
    _build(
        "Performance_Management_Policy.pdf",
        "Performance Management Policy",
        "HR-POL-006", "2.0", "April 2024",
        toc, sections,
    )


GENERATORS = [
    gen_leave_policy,
    gen_travel_policy,
    gen_medical_policy,
    gen_conduct_policy,
    gen_it_aup,
    gen_data_security,
    gen_expense,
    gen_procurement,
    gen_wfh,
    gen_performance,
]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating policy PDFs in: {OUTPUT_DIR}")
    for gen in GENERATORS:
        gen()
    print(f"\nDone. {len(GENERATORS)} PDFs generated.")


if __name__ == "__main__":
    main()
