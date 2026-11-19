import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from apps.ai_interviews.models import AIMockSession


def generate_mock_interview_pdf(session: AIMockSession) -> io.BytesIO:
    """
    Generates a professional PDF Evaluation Report for an AIMockSession using ReportLab.
    Returns a BytesIO buffer containing the PDF stream.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1E3A8A'),
        alignment=1, # Center
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#4B5563'),
        alignment=1,
        spaceAfter=15
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=10,
        spaceAfter=6
    )
    body_bold = ParagraphStyle(
        'BodyBold',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        fontName='Helvetica-Bold'
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#1F2937')
    )
    score_banner = ParagraphStyle(
        'ScoreBanner',
        parent=styles['Normal'],
        fontSize=16,
        leading=20,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#047857'),
        alignment=1
    )
    disclaimer_style = ParagraphStyle(
        'Disclaimer',
        parent=styles['Normal'],
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor('#6B7280'),
        alignment=1
    )

    story = []

    # 1. Header Banner
    story.append(Paragraph("AI-BASED MOCK INTERVIEW SYSTEM", title_style))
    story.append(Paragraph("Official Performance & Evaluation Report Card", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#3B82F6'), spaceAfter=12))

    # 2. Candidate & Session Info Table
    candidate_name = session.candidate.full_name if hasattr(session, 'candidate') else "N/A"
    candidate_email = session.candidate.user.email if hasattr(session, 'candidate') else "N/A"
    completed_str = session.completed_at.strftime('%B %d, %Y - %I:%M %p') if session.completed_at else session.created_at.strftime('%B %d, %Y')

    info_data = [
        [
            Paragraph("<b>Candidate Name:</b>", body_style),
            Paragraph(candidate_name, body_style),
            Paragraph("<b>Target Role:</b>", body_style),
            Paragraph(session.job_role, body_style)
        ],
        [
            Paragraph("<b>Email:</b>", body_style),
            Paragraph(candidate_email, body_style),
            Paragraph("<b>Category:</b>", body_style),
            Paragraph(session.get_category_display() if hasattr(session, 'get_category_display') else session.category, body_style)
        ],
        [
            Paragraph("<b>Date Evaluated:</b>", body_style),
            Paragraph(completed_str, body_style),
            Paragraph("<b>Difficulty:</b>", body_style),
            Paragraph(session.get_difficulty_display() if hasattr(session, 'get_difficulty_display') else session.difficulty, body_style)
        ],
    ]
    info_table = Table(info_data, colWidths=[100, 170, 100, 170])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F3F4F6')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#D1D5DB')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # 3. Overall Performance Score Banner
    overall_score_val = float(session.overall_score) if session.overall_score is not None else 0.0
    score_data = [
        [
            Paragraph(f"OVERALL PERFORMANCE SCORE: {overall_score_val}%", score_banner)
        ],
        [
            Paragraph(f"<b>Summary Evaluation:</b> {session.summary_feedback or 'Session completed.'}", body_style)
        ],
        [
            Paragraph(f"<b>Key Strengths:</b> {session.strengths_summary or 'Solid baseline.'}", body_style)
        ],
        [
            Paragraph(f"<b>Areas for Improvement:</b> {session.improvements_summary or 'Practice structured communication.'}", body_style)
        ]
    ]
    score_table = Table(score_data, colWidths=[540])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ECFDF5')),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFFFFF')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#10B981')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 12))

    # 4. Camera Telemetry Section (if present)
    if hasattr(session, 'camera_telemetry') and session.camera_telemetry:
        tel = session.camera_telemetry
        story.append(Paragraph("BEHAVIORAL & CAMERA TELEMETRY ANALYSIS", section_heading))
        tel_data = [
            [
                Paragraph("<b>Centered Posture:</b>", body_style),
                Paragraph(f"{tel.centered_posture_percentage}%", body_style),
                Paragraph("<b>Head Stability:</b>", body_style),
                Paragraph(f"{tel.head_stability_score}%", body_style),
                Paragraph("<b>Camera Focus Ratio:</b>", body_style),
                Paragraph(f"{tel.eye_contact_ratio}%", body_style),
            ],
            [
                Paragraph("<b>Observations:</b>", body_style),
                Paragraph(tel.observations or "Steady camera positioning maintained.", body_style),
                Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style)
            ]
        ]
        tel_table = Table(tel_data, colWidths=[95, 75, 95, 75, 105, 95])
        tel_table.setStyle(TableStyle([
            ('SPAN', (1, 1), (5, 1)),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(tel_table)
        story.append(Spacer(1, 12))

    # 5. Question-by-Question Evaluation Breakdown
    story.append(Paragraph("QUESTION-WISE DETAILED EVALUATION", section_heading))
    questions = session.questions.all().order_by('question_number')

    for q in questions:
        has_ans = hasattr(q, 'answer') and q.answer is not None
        ans_text = q.answer.answer_text if has_ans else "<i>[Not Answered]</i>"
        q_score = f"{float(q.answer.overall_question_score)}%" if has_ans and q.answer.overall_question_score else "0.0%"
        q_feedback = q.answer.feedback if has_ans and q.answer.feedback else "No response provided."
        q_strengths = q.answer.strengths if has_ans and q.answer.strengths else "N/A"
        q_improvements = q.answer.improvement_areas if has_ans and q.answer.improvement_areas else "N/A"

        q_table_data = [
            [
                Paragraph(f"<b>Q{q.question_number}: {q.question_text}</b>", body_bold),
                Paragraph(f"<b>Score: {q_score}</b>", body_bold)
            ],
            [
                Paragraph(f"<b>Candidate Response:</b> {ans_text}", body_style),
                Paragraph("", body_style)
            ],
            [
                Paragraph(f"<b>AI Evaluator Feedback:</b> {q_feedback}<br/><b>Observed Strengths:</b> {q_strengths}<br/><b>Suggestions:</b> {q_improvements}", body_style),
                Paragraph("", body_style)
            ]
        ]
        q_table = Table(q_table_data, colWidths=[450, 90])
        q_table.setStyle(TableStyle([
            ('SPAN', (0, 1), (1, 1)),
            ('SPAN', (0, 2), (1, 2)),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EFF6FF')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFFFFF')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#BFDBFE')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(KeepTogether([q_table, Spacer(1, 8)]))

    # 6. Ethical Disclaimer & Footer
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#9CA3AF'), spaceAfter=6))
    story.append(Paragraph(
        "Confidential Assessment Report. Generated by AI-Based Mock Interview Preparation System. "
        "Behavioral and camera telemetry are observational and advisory only and must never be used as an automatic hiring or rejection filter.",
        disclaimer_style
    ))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
