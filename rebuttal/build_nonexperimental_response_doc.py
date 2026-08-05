from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


OUT = Path(__file__).resolve().parent / "Submission10833_NonExperimental_Reviewer_Responses.docx"

INK = "0B2545"
BLUE = "2E74B5"
DARK_BLUE = "1F4D78"
MUTED = "58636F"
LIGHT_BLUE = "E8EEF5"
LIGHT_GRAY = "F2F4F7"
CAUTION = "7A5A00"
RED = "9B1C1C"
WHITE = "FFFFFF"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=80, start=120, bottom=80, end=120):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_cell_width(cell, width_dxa):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(width_dxa))
    tc_w.set(qn("w:type"), "dxa")


def set_table_geometry(table, widths):
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl_pr = table._tbl.tblPr

    tbl_w = tbl_pr.find(qn("w:tblW"))
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(widths)))
    tbl_w.set(qn("w:type"), "dxa")

    tbl_ind = tbl_pr.find(qn("w:tblInd"))
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), "120")
    tbl_ind.set(qn("w:type"), "dxa")

    layout = tbl_pr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tbl_pr.append(layout)
    layout.set(qn("w:type"), "fixed")

    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)

    for row in table.rows:
        for idx, cell in enumerate(row.cells):
            set_cell_width(cell, widths[idx])
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_run_font(run, size=None, color=None, bold=None, italic=None, name="Calibri"):
    run.font.name = name
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:hAnsi"), name)
    if size is not None:
        run.font.size = Pt(size)
    if color is not None:
        run.font.color.rgb = RGBColor.from_string(color)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def set_keep_with_next(paragraph, value=True):
    p_pr = paragraph._p.get_or_add_pPr()
    keep = p_pr.find(qn("w:keepNext"))
    if keep is None:
        keep = OxmlElement("w:keepNext")
        p_pr.append(keep)
    keep.set(qn("w:val"), "1" if value else "0")


def set_keep_lines(paragraph):
    p_pr = paragraph._p.get_or_add_pPr()
    keep = p_pr.find(qn("w:keepLines"))
    if keep is None:
        keep = OxmlElement("w:keepLines")
        p_pr.append(keep)
    keep.set(qn("w:val"), "1")


def set_paragraph_shading(paragraph, fill):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = p_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        p_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def add_left_border(paragraph, color=BLUE, size=18, space=8):
    p_pr = paragraph._p.get_or_add_pPr()
    p_bdr = p_pr.find(qn("w:pBdr"))
    if p_bdr is None:
        p_bdr = OxmlElement("w:pBdr")
        p_pr.append(p_bdr)
    left = p_bdr.find(qn("w:left"))
    if left is None:
        left = OxmlElement("w:left")
        p_bdr.append(left)
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), str(size))
    left.set(qn("w:space"), str(space))
    left.set(qn("w:color"), color)


def add_field(paragraph, field_code):
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = field_code
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, text, end])
    set_run_font(run, size=9, color=MUTED)


def add_numbering_definition(doc, marker_type):
    numbering_part = doc.part.numbering_part
    root = numbering_part.element
    abstract_ids = [
        int(e.get(qn("w:abstractNumId")))
        for e in root.findall(qn("w:abstractNum"))
        if e.get(qn("w:abstractNumId")) is not None
    ]
    num_ids = [
        int(e.get(qn("w:numId")))
        for e in root.findall(qn("w:num"))
        if e.get(qn("w:numId")) is not None
    ]
    abstract_id = max(abstract_ids, default=-1) + 1
    num_id = max(num_ids, default=0) + 1

    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    multi = OxmlElement("w:multiLevelType")
    multi.set(qn("w:val"), "singleLevel")
    abstract.append(multi)
    lvl = OxmlElement("w:lvl")
    lvl.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:start")
    start.set(qn("w:val"), "1")
    lvl.append(start)
    num_fmt = OxmlElement("w:numFmt")
    num_fmt.set(qn("w:val"), "bullet" if marker_type == "bullet" else "decimal")
    lvl.append(num_fmt)
    lvl_text = OxmlElement("w:lvlText")
    lvl_text.set(qn("w:val"), "•" if marker_type == "bullet" else "%1.")
    lvl.append(lvl_text)
    suff = OxmlElement("w:suff")
    suff.set(qn("w:val"), "tab")
    lvl.append(suff)
    p_pr = OxmlElement("w:pPr")
    tabs = OxmlElement("w:tabs")
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "num")
    tab.set(qn("w:pos"), "540")
    tabs.append(tab)
    p_pr.append(tabs)
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), "540")
    ind.set(qn("w:hanging"), "270")
    p_pr.append(ind)
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:after"), "80")
    spacing.set(qn("w:line"), "300")
    spacing.set(qn("w:lineRule"), "auto")
    p_pr.append(spacing)
    lvl.append(p_pr)
    r_pr = OxmlElement("w:rPr")
    r_fonts = OxmlElement("w:rFonts")
    r_fonts.set(qn("w:ascii"), "Calibri")
    r_fonts.set(qn("w:hAnsi"), "Calibri")
    r_pr.append(r_fonts)
    lvl.append(r_pr)
    abstract.append(lvl)
    root.append(abstract)

    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(num_id))
    abs_id = OxmlElement("w:abstractNumId")
    abs_id.set(qn("w:val"), str(abstract_id))
    num.append(abs_id)
    root.append(num)
    return num_id


def apply_numbering(paragraph, num_id):
    p_pr = paragraph._p.get_or_add_pPr()
    num_pr = p_pr.find(qn("w:numPr"))
    if num_pr is None:
        num_pr = OxmlElement("w:numPr")
        p_pr.append(num_pr)
    ilvl = OxmlElement("w:ilvl")
    ilvl.set(qn("w:val"), "0")
    num_id_node = OxmlElement("w:numId")
    num_id_node.set(qn("w:val"), str(num_id))
    num_pr.extend([ilvl, num_id_node])


def add_bullet(doc, text, bullet_num_id):
    p = doc.add_paragraph()
    apply_numbering(p, bullet_num_id)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.25
    run = p.add_run(text)
    set_run_font(run, size=11)
    return p


def add_label_paragraph(doc, label, text, label_color=DARK_BLUE, fill=None, border=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.left_indent = Inches(0.12) if border else None
    label_run = p.add_run(f"{label}: ")
    set_run_font(label_run, size=10.5, color=label_color, bold=True)
    body_run = p.add_run(text)
    set_run_font(body_run, size=11)
    if fill:
        set_paragraph_shading(p, fill)
    if border:
        add_left_border(p)
    set_keep_lines(p)
    return p


def add_question_block(doc, number, question, answer, action=None, boundary=None):
    p = doc.add_paragraph(style="Heading 2")
    p.add_run(f"{number}. {question}")
    set_keep_with_next(p)

    add_label_paragraph(doc, "Response", answer, border=True)
    if action:
        add_label_paragraph(doc, "Manuscript action", action, label_color=BLUE)
    if boundary:
        add_label_paragraph(doc, "Do not overclaim", boundary, label_color=RED, fill="FFF4F2")


def configure_styles(doc):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor.from_string("111111")
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.25

    h1 = styles["Heading 1"]
    h1.font.name = "Calibri"
    h1._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    h1._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.font.color.rgb = RGBColor.from_string(BLUE)
    h1.paragraph_format.space_before = Pt(18)
    h1.paragraph_format.space_after = Pt(10)
    h1.paragraph_format.keep_with_next = True

    h2 = styles["Heading 2"]
    h2.font.name = "Calibri"
    h2._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    h2._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    h2.font.size = Pt(13)
    h2.font.bold = True
    h2.font.color.rgb = RGBColor.from_string(BLUE)
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(7)
    h2.paragraph_format.keep_with_next = True

    h3 = styles["Heading 3"]
    h3.font.name = "Calibri"
    h3._element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    h3._element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    h3.font.size = Pt(12)
    h3.font.bold = True
    h3.font.color.rgb = RGBColor.from_string(DARK_BLUE)
    h3.paragraph_format.space_before = Pt(10)
    h3.paragraph_format.space_after = Pt(5)
    h3.paragraph_format.keep_with_next = True


def add_header_footer(doc):
    section = doc.sections[0]
    header = section.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run("SUBMISSION 10833  |  REBUTTAL WORKING DRAFT")
    set_run_font(r, size=8.5, color=MUTED, bold=True)

    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_before = Pt(0)
    r = p.add_run("Non-experimental reviewer responses  •  ")
    set_run_font(r, size=9, color=MUTED)
    add_field(p, "PAGE")


def add_mapping_table(doc):
    caption = doc.add_paragraph()
    caption.paragraph_format.space_before = Pt(4)
    caption.paragraph_format.space_after = Pt(4)
    run = caption.add_run("Review concern map")
    set_run_font(run, size=10, color=MUTED, italic=True)

    rows = [
        ("Difficulty target and external validity", "AC, ph2X, txM8, mEV6", "Shared"),
        ("Gold-label dependence and deployment scope", "AC, ph2X", "Shared"),
        ("Theory connecting disagreement to difficulty", "AC, ph2X", "Shared"),
        ("Split integrity, adaptivity, and reproducibility", "AC, ph2X, txM8, mEV6", "Shared"),
        ("Modest effect size and practical utility", "AC, ph2X", "Shared"),
        ("EIP citation, Agent-C setup, Table 3, ablations", "txM8", "Reviewer-specific"),
        ("Target circularity, missing details, figure size", "mEV6", "Reviewer-specific"),
    ]
    table = doc.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    widths = [4320, 2880, 2160]
    hdr = table.rows[0].cells
    for i, text in enumerate(("Concern", "Raised by", "Placement")):
        hdr[i].text = text
        set_cell_shading(hdr[i], LIGHT_BLUE)
        for run in hdr[i].paragraphs[0].runs:
            set_run_font(run, size=9.5, color=INK, bold=True)
    for concern, raised, placement in rows:
        cells = table.add_row().cells
        for i, text in enumerate((concern, raised, placement)):
            cells[i].text = text
            for p in cells[i].paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.1
                for run in p.runs:
                    set_run_font(run, size=9.5)
    set_table_geometry(table, widths)
    set_repeat_table_header(table.rows[0])


def build_document():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.5)
    section.page_height = Inches(11)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.492)
    section.footer_distance = Inches(0.492)
    configure_styles(doc)
    add_header_footer(doc)
    bullet_num_id = add_numbering_definition(doc, "bullet")

    # First-page memo masthead. Named title override to the compact-reference preset.
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run("SUBMISSION 10833")
    set_run_font(r, size=11, color=BLUE, bold=True)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(5)
    r = p.add_run("Non-Experimental Reviewer Questions and Draft Answers")
    set_run_font(r, size=24, color=INK, bold=True)
    set_keep_with_next(p)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(14)
    r = p.add_run("Common concerns first, followed by reviewer-specific responses")
    set_run_font(r, size=12.5, color=MUTED, italic=True)

    for label, value in (
        ("Paper", "Disagreement, Diversity, and Difficulty in Multi-Agent Language Models"),
        ("Source", "Area Chair meta-review and official reviews by ph2X, txM8, and mEV6"),
        ("Purpose", "Author working draft for responses that do not require new experiments"),
        ("Prepared", "27 July 2026"),
    ):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(2)
        lr = p.add_run(f"{label}: ")
        set_run_font(lr, size=10.5, color=INK, bold=True)
        vr = p.add_run(value)
        set_run_font(vr, size=10.5, color="333333")

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.left_indent = Inches(0.12)
    set_paragraph_shading(p, LIGHT_GRAY)
    add_left_border(p, color=CAUTION)
    r = p.add_run("Author-use note. ")
    set_run_font(r, size=10.5, color=CAUTION, bold=True)
    r = p.add_run(
        "These answers are deliberately conservative. They clarify the submitted method and "
        "acknowledge verified limitations, but they do not treat planned experiments as completed. "
        "Any numerical result should be inserted only after its underlying artifacts are verified."
    )
    set_run_font(r, size=10.5)

    add_mapping_table(doc)

    doc.add_heading("Part I — Questions Common Across Reviews", level=1)
    p = doc.add_paragraph(
        "The following themes were raised by at least two reviewers or were adopted by the Area Chair "
        "as central weaknesses. The wording below is suitable for a rebuttal or revision after normal "
        "length editing."
    )
    p.paragraph_format.space_after = Pt(8)

    add_question_block(
        doc,
        "C1",
        "What does the paper mean by “difficulty,” and how trustworthy is the target?",
        "We agree that the submitted target should not be interpreted as a validated measure of "
        "human or cognitive difficulty. In MMLU-Pro, s(q) is a heuristic surface-complexity score "
        "constructed from question length, mean option length, option-length dispersion, counts of "
        "mathematical symbols and digits, and fixed category boosts. It is useful as a controlled "
        "evaluation proxy, but it may underrepresent semantic difficulty in areas such as philosophy "
        "and history. We will therefore describe our result as an association with the submitted "
        "proxy, rather than evidence that disagreement recovers intrinsic difficulty.",
        "Move a compact form of Eq. 12 and a plain-language explanation into the main evaluation "
        "section. State explicitly that the score is heuristic and not validated against human "
        "ratings, solution times, item-response-theory difficulty, or historical pass rates.",
        "Do not write that the method measures “true,” “intrinsic,” or “human” difficulty. Independent "
        "difficulty validation belongs to the experiment plan.",
    )

    add_question_block(
        doc,
        "C2",
        "Is the proposed method label-free?",
        "Only part of the scoring procedure is label-free. Answer entropy, pairwise Jensen–Shannon "
        "divergence, and confidence variance can be computed from agent outputs without a gold answer. "
        "The correctness-diversity component uses the gold label, and the current specialization, "
        "Agent-C routing, and co-evolution updates also use supervised targets. We will therefore "
        "describe the complete pipeline as supervised. When gold labels are unavailable, the first "
        "three components define a reduced inference-time ranking score.",
        "Add a stage-by-stage label-use table covering scoring, specialization, calibration, buffer "
        "routing, co-evolution, and final evaluation. Replace global “label-free” wording with the "
        "narrower phrase “label-free score components at inference.”",
        "Do not imply that the no-correctness variant makes the entire training and co-evolution "
        "pipeline label-free.",
    )

    add_question_block(
        doc,
        "C3",
        "Why should disagreement be connected to question difficulty?",
        "The intended mechanism is conditional: when agents have genuinely complementary inductive "
        "biases and non-identical failure modes, harder questions are more likely to produce different "
        "answers, probability distributions, or confidence levels. This mechanism does not hold "
        "universally. Disagreement can also arise from ambiguity, miscalibration, representation "
        "differences, or systematic bias, while difficult questions can still produce correlated "
        "errors. The theoretical section should therefore be read as design motivation under explicit "
        "assumptions, not as a general guarantee that disagreement is equivalent to difficulty.",
        "State the assumptions immediately before each theorem and distinguish formal conditional "
        "claims from empirical hypotheses. Replace “establishes” or “guarantees” with “motivates,” "
        "“characterizes under the assumptions,” or “suggests.”",
        "Do not claim a general lower bound on disagreement–difficulty correlation unless every "
        "assumption used by the bound is stated and justified.",
    )

    add_question_block(
        doc,
        "C4",
        "Were specialization, co-evolution, model selection, and final evaluation strictly separated?",
        "The submitted description did not make this separation sufficiently auditable, and the "
        "current repository artifacts do not support describing the stored Agent-C result as fully "
        "held out. We now define an immutable protocol: the training split is used for specialization, "
        "hard-case buffering, and co-evolution; the validation split is used for calibration, "
        "hyperparameter selection, iteration selection, and checkpoint selection; and the test split "
        "is evaluated once after all choices are frozen. Under the current strict manifest, these "
        "partitions contain 2,416, 300, and 300 questions, respectively.",
        "Describe the permitted use of every split in the main protocol and record the split-manifest "
        "hash, seed, code commit, adapter hashes, and split-specific output files. State that corrected "
        "held-out numbers will be reported only after the planned reruns.",
        "Do not characterize the currently stored evaluation as held out: the repository audit found "
        "that 240 of 300 stored evaluation questions occur in Agent C’s current training or validation "
        "partition.",
    )

    add_question_block(
        doc,
        "C5",
        "Could the co-evolution loop or hard-case buffer create circularity or adaptivity bias?",
        "The intended buffer is ranked by the composite disagreement score D(q), with agent-specific "
        "sampling based on answer disagreement, confidence gaps, domain membership, and Agent-C "
        "calibration error. The implementation does not directly rank examples by the heuristic "
        "difficulty target s(q). The sentence in Appendix B.8 stating that examples with both high "
        "D(q) and high s(q) are amplified is therefore misleading and should be corrected. Separately, "
        "adaptivity bias is controlled only when buffer updates remain inside training data, model "
        "selection remains inside validation data, and the test set is untouched until the final run.",
        "Rewrite Appendix B.8 to separate the training signal D(q) from the evaluation target s(q). "
        "Add pseudocode identifying exactly which quantities are available at each stage.",
        "Clarifying that s(q) is not used by the buffer removes direct target optimization; it does not "
        "validate s(q) or repair split overlap by itself.",
    )

    add_question_block(
        doc,
        "C6",
        "Are the reported correlations practically meaningful?",
        "We agree that the effect size is modest. Even the submitted co-evolution endpoint should be "
        "interpreted as explaining only a limited portion of rank variation in the heuristic target. "
        "The most defensible current use is triage: prioritizing questions for inspection, annotation, "
        "or additional model evaluation. The method is not presented as a standalone difficulty "
        "oracle or as sufficient evidence for high-stakes routing decisions.",
        "Use “triage signal,” “ranking cue,” or “prioritization signal” consistently. Add an explicit "
        "paragraph separating exploratory offline curation from deployment-time reliability.",
        "Do not describe ρ≈0.20 as strong or operationally reliable. Practical utility against an "
        "independent target is part of the experiment plan.",
    )

    add_question_block(
        doc,
        "C7",
        "Is the training and evaluation protocol reproducible from the paper?",
        "The revised paper should provide one authoritative configuration instead of scattering "
        "details across sections. The submitted text specifies greedy next-token option scoring for "
        "heterogeneous agents, Agent-C temperature scaling, temperature 1 for Agents R and D, seeds "
        "42/1337/2024, a single NVIDIA T4 with 16 GB, and approximately 14 hours per seed for the "
        "30-iteration loop. It also reports LoRA rank 16, alpha 32, dropout 0.05, and 50 LoRA steps per "
        "co-evolution iteration. We will consolidate all verifiable prompts, datasets, optimizer "
        "settings, buffer rules, checkpoint-selection rules, and output schemas into a single protocol.",
        "Add a concise reproducibility table and release exact commands/configurations where they can "
        "be recovered. Distinguish manuscript-reported settings from settings verified by saved run "
        "artifacts.",
        "Do not assert that unavailable prompts, adapters, seed logs, or trajectories have been "
        "recovered. The current checkout does not independently reproduce the submitted co-evolution "
        "and seven-benchmark results.",
    )

    add_question_block(
        doc,
        "C8",
        "What is the correct scope of the paper’s claim?",
        "The defensible claim is that structured, functionally heterogeneous agents produce a "
        "composite disagreement signal that shows an empirical association with the paper’s "
        "difficulty proxy, and that the signal may support offline hard-case triage. The present "
        "evidence does not establish human difficulty estimation, universal transfer, or a fully "
        "label-free deployment pipeline.",
        "Revise the abstract, introduction, conclusion, and limitations so that the same scope is used "
        "throughout. Add explicit limitations covering the heuristic target, label use, split risk, "
        "conditional theory, modest effect size, multiple-choice scope, and deployment gap.",
        "Avoid stronger language in the abstract than in the limitations.",
    )

    doc.add_heading("Part II — Reviewer-Specific Questions", level=1)
    p = doc.add_paragraph(
        "This section includes questions or requested clarifications that are distinctive to one "
        "reviewer. Shared concerns are not repeated unless the reviewer asked for a specific detail."
    )

    doc.add_heading("Reviewer ph2X", level=1)
    add_question_block(
        doc,
        "P1",
        "Beyond MMLU-Pro, how was the difficulty proxy defined on each benchmark?",
        "The rebuttal should provide a benchmark-by-benchmark definition rather than imply that the "
        "MMLU-Pro surface-feature formula transfers automatically. At present, the repository audit "
        "cannot verify the original target construction for the complete seven-benchmark study; the "
        "checked-in GPQA and BBH preparation files assign a constant difficulty value of 1.0, which "
        "cannot support a Spearman correlation. We should therefore state that the cross-benchmark "
        "target definitions were insufficiently documented and treat the corresponding claims as "
        "provisional until the original artifacts are recovered or the targets are rebuilt.",
        "Add a benchmark-target appendix listing the source, formula, normalization, variation, and "
        "intended interpretation for every benchmark. Report proxy-sensitivity results only after the "
        "planned analysis.",
        "Do not invent missing target definitions or defend GPQA/BBH correlations computed against a "
        "constant target.",
    )

    add_question_block(
        doc,
        "P2",
        "How should the paper describe deployment-time applicability?",
        "The current full pipeline is best understood as supervised offline benchmark curation and "
        "hard-case discovery. A serving-time system can compute entropy, Jensen–Shannon divergence, "
        "and confidence variance without labels, but the submitted specialization and update process "
        "still depends on labeled data. Online adapter swapping is a possible extension that was not "
        "tested in the paper.",
        "Move the online-deployment discussion from a broad capability statement to a clearly labeled "
        "future-work paragraph.",
        "Do not imply that an online co-evolution system was evaluated.",
    )

    doc.add_heading("Reviewer txM8", level=1)
    add_question_block(
        doc,
        "T1",
        "What dataset and objective were used for Agent C?",
        "Agent C is the calibration specialist. In the submitted method it is trained as a "
        "multiple-choice scorer using cross-entropy plus an expected-calibration-error term, followed "
        "by scalar temperature scaling on validation logits. The current checked-in loader uses "
        "partitions of the MMLU-Pro hard subset. Because those current partitions overlap with stored "
        "evaluation questions, the revision should specify the exact split IDs and report corrected "
        "results only from the immutable split protocol.",
        "Add Agent C’s dataset, train/calibration split, objective, temperature-fitting procedure, "
        "LoRA configuration, and split manifest to the main setup table.",
        "Do not call the current Agent-C validation partition “held out” relative to the stored "
        "evaluation.",
    )

    add_question_block(
        doc,
        "T2",
        "What does “static disagreement” mean?",
        "Static disagreement is the composite disagreement computed from the already specialized "
        "agents before any co-evolution update. It is the Iteration-0 state of the co-evolution "
        "procedure.",
        "Define the term on first use and use “pre-co-evolution (Iteration 0)” in the relevant table "
        "caption.",
    )

    add_question_block(
        doc,
        "T3",
        "What exact setting and dataset are used in Table 3?",
        "Table 3 reports the different-family configuration on MMLU-Pro with n=300. Agents R and C use "
        "Qwen2.5-3B-Instruct adapters, while Agent D uses Mistral-7B-Instruct-v0.3. The table compares "
        "Iteration 0 with the reported Iteration-30 endpoint.",
        "Put “different-family, MMLU-Pro, n=300” directly in the Table 3 caption and identify each "
        "backbone in the surrounding text.",
        "Retain the Iteration-30 numerical values only if their original artifacts are recovered or "
        "the planned rerun reproduces them.",
    )

    add_question_block(
        doc,
        "T4",
        "Why is the Iteration-0 correlation in Table 3 lower than the values in Table 1?",
        "Table 3’s Iteration-0 value is the baseline for one specific different-family MMLU-Pro n=300 "
        "run. Its matching static comparison is the corresponding row in Table 2, not Table 1. Table 1 "
        "summarizes a broader model-by-benchmark design space and therefore is not the one-to-one "
        "baseline for Table 3.",
        "Add an explicit cross-reference from Table 3 to its matching Table 2 row and document exactly "
        "how Table 1 cells were aggregated once the original run matrix is recovered.",
        "Do not explain the difference through aggregation details that cannot be verified from the "
        "saved artifacts.",
    )

    add_question_block(
        doc,
        "T5",
        "What does each component of the composite score contribute?",
        "The submitted Appendix Table 11 already reports entropy-only, JS-only, confidence-only, "
        "correctness-only, equal-weight, entropy-plus-JS, entropy-heavy, JS-heavy, no-correctness, and "
        "the selected weighting. In the submitted table, the selected weighting is "
        "(0.45, 0.35, 0.15, 0.05); JS-heavy is numerically similar; and removing correctness changes "
        "the reported endpoint only slightly. This supports interpreting correctness diversity as a "
        "small supervised tie-breaker rather than the principal source of the score.",
        "Point directly to Table 11 from the main text and summarize the qualitative conclusion in one "
        "sentence.",
        "The raw endpoint artifacts are absent from the current checkout. Refer to these values as "
        "submitted results, not as independently reproduced results.",
    )

    add_question_block(
        doc,
        "T6",
        "Was co-evolution considered without initial agent specialization?",
        "No result for a non-specialized co-evolution initialization is reported. Initial "
        "specialization is part of the proposed design because the loop is intended to preserve and "
        "refine complementary failure modes, rather than create heterogeneity from identical agents. "
        "The reviewer’s suggested control is nevertheless valuable because it would test whether "
        "co-evolution alone can induce useful diversity.",
        "Acknowledge the missing control and list it in the planned experiment set or future work.",
        "Do not imply that this baseline was run.",
    )

    add_question_block(
        doc,
        "T7",
        "How does this paper relate to EIP by Hu et al. (2026)?",
        "We thank the reviewer for identifying this relevant work and will add it to Related Work. EIP "
        "also uses multiple LLMs to estimate question difficulty and importantly validates its signal "
        "against human judgment. Our work studies a different mechanism: disagreement among agents "
        "with deliberately different roles, training objectives, and—in one condition—model families, "
        "combined with a composite probabilistic score and co-evolution. The two approaches are "
        "complementary, and EIP’s validation standard reinforces the need to validate our proxy "
        "against an independent target.",
        "Add the full citation supplied by the reviewer and a comparison paragraph covering target "
        "definition, human validation, agent construction, and intended use.",
        "Do not claim that the proposed method outperforms EIP without a direct comparison.",
    )

    doc.add_heading("Reviewer mEV6", level=1)
    add_question_block(
        doc,
        "M1",
        "What is the exact MMLU-Pro target score, and why is it not in the main paper?",
        "For MMLU-Pro, the submitted score combines clipped terms for question length, mean option "
        "length, mathematical-symbol and digit count, inverse option-length dispersion, and a fixed "
        "boost for selected categories. The reviewer is correct that this target is central to the "
        "paper’s primary correlation and should be visible in the main evaluation section rather than "
        "only in Appendix B.1.",
        "Move Eq. 12 or a compact equivalent into the main paper, define every term, and place its "
        "limitations immediately after the definition.",
    )

    add_question_block(
        doc,
        "M2",
        "Can the proxy behave inconsistently across categories such as philosophy and history?",
        "Yes. Length, symbols, and option statistics may align more naturally with mathematical or "
        "technical complexity than with semantic, interpretive, or factual difficulty. We will state "
        "that category boosts do not eliminate this construct-validity problem and that category-level "
        "correlations should not be interpreted as validation of human difficulty.",
        "Add this category-dependence explicitly to the limitations and avoid treating the fixed "
        "category boost as a semantic difficulty model.",
        "Whether conclusions are stable under a semantic or human target requires the planned "
        "validation experiment.",
    )

    add_question_block(
        doc,
        "M3",
        "Does the hard-case buffer train the models to hack the heuristic target?",
        "The implemented buffer is driven by D(q), not directly by s(q). Agent R is sampled using "
        "R–D answer and confidence disagreement; Agent D additionally uses domain membership and "
        "disagreement with Agent C; Agent C uses calibration-error cases. Therefore the target proxy "
        "is not an explicit optimization or ranking signal in the implemented buffer. Appendix B.8 "
        "should be corrected because its current wording suggests otherwise.",
        "Replace the statement that high-D(q), high-s(q) examples are amplified with a faithful "
        "description of the implemented sampling rules. Include the complete sampling equations in "
        "the method description.",
        "This response addresses direct target leakage only; it does not establish that D(q) cannot "
        "learn correlated surface features indirectly.",
    )

    add_question_block(
        doc,
        "M4",
        "Where are the prompts, decoding settings, seeds, and compute details?",
        "Appendix D contains some of the requested information: heterogeneous inference uses greedy "
        "next-token scoring restricted to option labels; Agent C uses its calibrated temperature; "
        "Agents R and D use temperature 1; runs list seeds 42, 1337, and 2024; heterogeneous runs use "
        "a single T4 16 GB; and the submitted 30-iteration loop is reported as approximately 14 hours "
        "per seed. The paper should nevertheless provide the full role prompts, exact model and adapter "
        "identifiers, commands, library versions, and run configurations in one accessible location.",
        "Create a single reproducibility appendix and artifact manifest. Correct the main-text pointer "
        "so readers can find the exact subsection.",
        "Do not claim that the exact submitted prompts or run bundle are currently recoverable from "
        "the repository if they are not.",
    )

    add_question_block(
        doc,
        "M5",
        "Can the figures and prose be made easier to read?",
        "Yes. The revision will enlarge figure labels, simplify crowded multi-panel layouts, remove "
        "duplicated labels in Figure 1, correct typographical errors, and move essential method details "
        "from the appendix into the main text.",
        "Apply these presentation fixes throughout the camera-ready or revision. They require no new "
        "experimental evidence.",
    )

    doc.add_heading("Area Chair", level=1)
    p = doc.add_paragraph(
        "The Area Chair did not pose a separate numbered question. The meta-review consolidates the "
        "shared concerns addressed in Part I: heuristic difficulty validation, label dependence, "
        "conditional theory, protocol clarity and adaptivity, reproducibility, and modest practical "
        "effect size."
    )

    doc.add_heading("Part III — Claims Reserved for the Experiment Plan", level=1)
    p = doc.add_paragraph(
        "The following questions may be acknowledged now, but their substantive conclusions should "
        "not be answered numerically until the planned experiments or artifact recovery are complete:"
    )
    for text in (
        "Validation against human ratings, independent model pass rates, or IRT difficulty.",
        "Sensitivity to alternative difficulty targets and category-specific target definitions.",
        "Corrected held-out specialization and co-evolution results under the immutable split.",
        "Co-evolution from a non-specialized initialization.",
        "Operational top-k enrichment or other utility metrics against an independent target.",
        "Reproduced three-seed trajectories, cross-benchmark transfer, and endpoint ablations.",
        "Direct empirical comparison with EIP.",
    ):
        add_bullet(doc, text, bullet_num_id)

    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.left_indent = Inches(0.12)
    set_paragraph_shading(p, LIGHT_BLUE)
    add_left_border(p, color=BLUE)
    r = p.add_run("Recommended response posture. ")
    set_run_font(r, size=10.5, color=INK, bold=True)
    r = p.add_run(
        "Clarify what the submitted method actually does, concede limitations that the current "
        "evidence cannot resolve, narrow the central claim to an offline triage signal, and reserve "
        "all new numerical claims for verified experimental outputs."
    )
    set_run_font(r, size=10.5)

    # Core properties to improve pagination.
    core = doc.core_properties
    core.title = "Submission 10833 — Non-Experimental Reviewer Questions and Draft Answers"
    core.subject = "NeurIPS 2026 rebuttal working draft"
    core.author = "Submission 10833 Authors"
    core.keywords = "NeurIPS, rebuttal, reviewer responses, disagreement, difficulty"

    doc.save(OUT)
    return OUT


if __name__ == "__main__":
    print(build_document())
