"""Shared OOXML names, fields and schema ordering for the Word edition."""
from __future__ import annotations

from dataclasses import dataclass, field
from xml.etree import ElementTree as ET

NS = {
    'pr': 'http://schemas.openxmlformats.org/package/2006/relationships',
    'ct': 'http://schemas.openxmlformats.org/package/2006/content-types',
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math',
    'v': 'urn:schemas-microsoft-com:vml',
    'o': 'urn:schemas-microsoft-com:office:office',
}
W = '{' + NS['w'] + '}'
XML_SPACE = '{http://www.w3.org/XML/1998/namespace}space'

# ISO/IEC 29500 property sequences. Validate/reorder only containers we author.
ORDER = {
    'settings': (
        'writeProtection view zoom removePersonalInformation removeDateAndTime '
        'doNotDisplayPageBoundaries displayBackgroundShape printPostScriptOverText '
        'printFractionalCharacterWidth printFormsData embedTrueTypeFonts embedSystemFonts '
        'saveSubsetFonts saveFormsData mirrorMargins alignBordersAndEdges bordersDoNotSurroundHeader '
        'bordersDoNotSurroundFooter gutterAtTop hideSpellingErrors hideGrammaticalErrors '
        'activeWritingStyle proofState formsDesign attachedTemplate linkStyles stylePaneFormatFilter '
        'stylePaneSortMethod documentType mailMerge revisionView trackRevisions doNotTrackMoves '
        'doNotTrackFormatting documentProtection autoFormatOverride styleLockTheme styleLockQFSet '
        'defaultTabStop autoHyphenation consecutiveHyphenLimit hyphenationZone doNotHyphenateCaps '
        'showEnvelope summaryLength clickAndTypeStyle defaultTableStyle evenAndOddHeaders '
        'bookFoldRevPrinting bookFoldPrinting bookFoldPrintingSheets drawingGridHorizontalSpacing '
        'drawingGridVerticalSpacing displayHorizontalDrawingGridEvery displayVerticalDrawingGridEvery '
        'doNotUseMarginsForDrawingGrid drawingGridHorizontalOrigin drawingGridVerticalOrigin '
        'doNotShadeFormData noPunctuationKerning characterSpacingControl printTwoOnOne '
        'strictFirstAndLastChars noLineBreaksAfter noLineBreaksBefore savePreviewPicture '
        'doNotValidateAgainstSchema saveInvalidXml ignoreMixedContent alwaysShowPlaceholderText '
        'doNotDemarcateInvalidXml saveXmlDataOnly useXSLTWhenSaving saveThroughXslt showXMLTags '
        'alwaysMergeEmptyNamespace updateFields hdrShapeDefaults footnotePr endnotePr compat docVars '
        'rsids attachedSchema themeFontLang clrSchemeMapping doNotIncludeSubdocsInStats '
        'doNotAutoCompressPictures forceUpgrade captions readModeInkLockDown smartTagType '
        'schemaLibrary shapeDefaults doNotEmbedSmartTags decimalSymbol listSeparator'
    ),
    'pPr': (
        'pStyle keepNext keepLines pageBreakBefore framePr widowControl numPr suppressLineNumbers '
        'pBdr shd tabs suppressAutoHyphens kinsoku wordWrap overflowPunct topLinePunct autoSpaceDE '
        'autoSpaceDN bidi adjustRightInd snapToGrid spacing ind contextualSpacing mirrorIndents '
        'suppressOverlap jc textDirection textAlignment textboxTightWrap outlineLvl divId cnfStyle '
        'rPr sectPr pPrChange'
    ),
    'rPr': (
        'rStyle rFonts b bCs i iCs caps smallCaps strike dstrike outline shadow emboss imprint '
        'noProof snapToGrid vanish webHidden color spacing w kern position sz szCs highlight u effect '
        'bdr shd fitText vertAlign rtl cs em lang eastAsianLayout specVanish oMath rPrChange'
    ),
    'tblPr': (
        'tblStyle tblpPr tblOverlap bidiVisual tblStyleRowBandSize tblStyleColBandSize tblW jc '
        'tblCellSpacing tblInd tblBorders shd tblLayout tblCellMar tblLook tblCaption tblDescription '
        'tblPrChange'
    ),
    'trPr': (
        'cnfStyle divId gridBefore gridAfter wBefore wAfter cantSplit trHeight tblHeader '
        'tblCellSpacing jc hidden ins del trPrChange'
    ),
    'tcPr': (
        'cnfStyle tcW gridSpan hMerge vMerge tcBorders shd noWrap tcMar textDirection tcFitText '
        'vAlign hideMark headers cellIns cellDel cellMerge tcPrChange'
    ),
}


def register_namespaces() -> None:
    for prefix, uri in NS.items():
        ET.register_namespace(prefix, uri)


def order_properties(root: ET.Element) -> None:
    for node in root.iter():
        order = ORDER.get(node.tag.removeprefix(W)) if node.tag.startswith(W) else None
        if order:
            ranks = {W + tag: index for index, tag in enumerate(order.split())}
            if node.tag == W + 'settings':
                ranks['{' + NS['m'] + '}mathPr'] = ranks[W + 'rsids'] + 0.5
            node[:] = sorted(node, key=lambda child: ranks.get(child.tag, len(ranks)))


def text_of(node: ET.Element) -> str:
    return ''.join(item.text or '' for item in node.iter(W + 't')).strip()


def style_of(paragraph: ET.Element) -> str:
    style = paragraph.find(W + 'pPr/' + W + 'pStyle')
    return style.get(W + 'val', '') if style is not None else ''


@dataclass
class Field:
    begin: ET.Element
    instructions: list[ET.Element] = field(default_factory=list)
    separated: bool = False

    @property
    def instruction(self) -> str:
        return ''.join(node.text or '' for node in self.instructions).strip()


def fields(root: ET.Element) -> list[Field]:
    """Read nested complex fields, rejecting malformed field boundaries."""
    stack: list[Field] = []
    result: list[Field] = []
    for node in root.iter():
        if node.tag == W + 'fldChar':
            kind = node.get(W + 'fldCharType')
            if kind == 'begin':
                stack.append(Field(node))
            elif kind == 'separate':
                if not stack or stack[-1].separated:
                    raise ValueError('DOCX field separator has no unmatched begin')
                stack[-1].separated = True
            elif kind == 'end':
                if not stack:
                    raise ValueError('DOCX field end has no begin')
                result.append(stack.pop())
            else:
                raise ValueError('DOCX field character has an invalid type')
        elif node.tag == W + 'instrText':
            if not stack or stack[-1].separated:
                raise ValueError('DOCX field instruction is outside its instruction range')
            stack[-1].instructions.append(node)
    if stack:
        raise ValueError('DOCX field is missing its end')
    return result


def field_run(kind: str, *, hidden: bool = False) -> ET.Element:
    run = ET.Element(W + 'r')
    if hidden:
        ET.SubElement(ET.SubElement(run, W + 'rPr'), W + 'vanish')
    marker = ET.SubElement(run, W + 'fldChar', {W + 'fldCharType': kind})
    if kind == 'begin':
        marker.set(W + 'dirty', 'true')
    return run


def instruction_run(instruction: str, *, hidden: bool = False) -> ET.Element:
    run = ET.Element(W + 'r')
    if hidden:
        ET.SubElement(ET.SubElement(run, W + 'rPr'), W + 'vanish')
    ET.SubElement(run, W + 'instrText', {XML_SPACE: 'preserve'}).text = ' ' + instruction + ' '
    return run
