"""Build V3.13 RIGOURATE-Differentiated + Realism-Aware docx from markdown.

Reuses the V3.13 docx builder logic with the new RIGOURATE-aware paths.
"""
import os
import re
import zipfile
from xml.sax.saxutils import escape

MD_PATH = r"D:\ocn\paper_versions_ordered\V3_13_rigourate_differentiated_realism_aware\CESE_OCN_V3_13_rigourate_differentiated_realism_aware.md"
DOCX_PATH = r"D:\ocn\paper_versions_ordered\V3_13_rigourate_differentiated_realism_aware\CESE_OCN_V3_13_rigourate_differentiated_realism_aware.docx"

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def render_inline_runs(text):
    parts = re.split(r"(\*\*[^*]+\*\*)", text)
    runs = []
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            inner = part[2:-2]
            runs.append('<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">' + escape(inner) + '</w:t></w:r>')
        else:
            italic_parts = re.split(r"(\*[^*]+\*)", part)
            for ip in italic_parts:
                if not ip:
                    continue
                if ip.startswith("*") and ip.endswith("*") and len(ip) > 2:
                    inner = ip[1:-1]
                    runs.append('<w:r><w:rPr><w:i/></w:rPr><w:t xml:space="preserve">' + escape(inner) + '</w:t></w:r>')
                else:
                    runs.append('<w:r><w:t xml:space="preserve">' + escape(ip) + '</w:t></w:r>')
    return "".join(runs)


def para(text, style=None, bold=False):
    ppr = '<w:pPr><w:pStyle w:val="' + style + '"/></w:pPr>' if style else ''
    if bold:
        runs = '<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">' + escape(text) + '</w:t></w:r>'
    else:
        runs = render_inline_runs(text)
    return '<w:p>' + ppr + runs + '</w:p>'


def heading(text, level):
    return para(text, style='Heading' + str(level))


def table_block(rows):
    if not rows:
        return ''
    n_cols = max(len(r) for r in rows)
    tbl_pr = ('<w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>'
              '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '</w:tblBorders></w:tblPr>')
    grid = '<w:tblGrid>' + ''.join('<w:gridCol w:w="2000"/>' for _ in range(n_cols)) + '</w:tblGrid>'
    rows_xml = []
    for i, row in enumerate(rows):
        is_header = (i == 0)
        cells_xml = []
        for j in range(n_cols):
            cell_text = row[j] if j < len(row) else ''
            ppr = '<w:pPr><w:pStyle w:val="TableCell"/></w:pPr>'
            if is_header:
                run = '<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">' + escape(cell_text) + '</w:t></w:r>'
            else:
                run = render_inline_runs(cell_text)
            cells_xml.append('<w:tc><w:tcPr><w:tcW w:w="2000" w:type="dxa"/></w:tcPr><w:p>' + ppr + run + '</w:p></w:tc>')
        rows_xml.append('<w:tr>' + ''.join(cells_xml) + '</w:tr>')
    return '<w:tbl>' + tbl_pr + grid + ''.join(rows_xml) + '</w:tbl>'


def parse_markdown(md):
    lines = md.split('\n')
    elements = []
    i = 0
    in_code_block = False
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()
        if stripped.startswith('```'):
            if in_code_block:
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue
        if in_code_block:
            safe = escape(stripped)
            elements.append('<w:p><w:pPr><w:pStyle w:val="TableCell"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/></w:rPr><w:t xml:space="preserve">' + safe + '</w:t></w:r></w:p>')
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        if stripped.startswith('#### '):
            elements.append(heading(stripped[5:], 4)); i += 1; continue
        if stripped.startswith('### '):
            elements.append(heading(stripped[4:], 3)); i += 1; continue
        if stripped.startswith('## '):
            elements.append(heading(stripped[3:], 2)); i += 1; continue
        if stripped.startswith('# '):
            elements.append(heading(stripped[2:], 1)); i += 1; continue
        if stripped.startswith('|') and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if re.match(r'^\|[\s\-:|]+\|$', next_line):
                table_rows = [[c.strip() for c in stripped.strip('|').split('|')]]
                i += 2
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                    i += 1
                elements.append(table_block(table_rows)); continue
        if stripped.startswith('- '):
            elements.append('<w:p><w:pPr><w:pStyle w:val="ListBullet"/></w:pPr>' + render_inline_runs(stripped[2:]) + '</w:p>')
            i += 1; continue
        if stripped.startswith(('✅', '❌')):
            elements.append(para(stripped)); i += 1; continue
        m = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if m:
            elements.append('<w:p><w:pPr><w:pStyle w:val="ListNumber"/></w:pPr>' + render_inline_runs(m.group(2)) + '</w:p>')
            i += 1; continue
        if stripped.startswith('> '):
            elements.append('<w:p><w:pPr><w:pStyle w:val="TableCell"/></w:pPr>' + render_inline_runs(stripped[2:]) + '</w:p>')
            i += 1; continue
        elements.append(para(stripped)); i += 1
    return elements


STYLES_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
              '<w:styles xmlns:w="' + NS_W + '">\n'
              '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>\n'
              '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="280" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="80"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="Heading4"><w:name w:val="heading 4"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="60"/><w:outlineLvl w:val="3"/></w:pPr><w:rPr><w:b/><w:sz w:val="22"/></w:rPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr><w:spacing w:after="80"/></w:pPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="ListNumber"><w:name w:val="List Number"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr><w:spacing w:after="80"/></w:pPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="TableCell"><w:name w:val="Table Cell"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr></w:style>\n'
              '</w:styles>')

CONTENT_TYPES_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>'''

RELS_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

DOC_RELS_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>'''

NUMBERING_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                 '<w:numbering xmlns:w="' + NS_W + '">\n'
                 '<w:abstractNum w:abstractNumId="0"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8226;"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>\n'
                 '<w:abstractNum w:abstractNumId="1"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>\n'
                 '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>\n'
                 '<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>\n'
                 '</w:numbering>')


def build_docx():
    with open(MD_PATH, 'r', encoding='utf-8') as f:
        md = f.read()
    elements = parse_markdown(md)
    body = ''.join(elements)
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="' + NS_W + '"><w:body>' + body +
        '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
        '</w:body></w:document>'
    )
    with zipfile.ZipFile(DOCX_PATH, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CONTENT_TYPES_XML)
        z.writestr('_rels/.rels', RELS_XML)
        z.writestr('word/document.xml', document_xml)
        z.writestr('word/_rels/document.xml.rels', DOC_RELS_XML)
        z.writestr('word/styles.xml', STYLES_XML)
        z.writestr('word/numbering.xml', NUMBERING_XML)
    print('DOCX written: ' + DOCX_PATH + ' (' + str(os.path.getsize(DOCX_PATH)) + ' bytes)')


if __name__ == '__main__':
    build_docx()
